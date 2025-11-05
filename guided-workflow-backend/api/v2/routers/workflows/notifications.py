import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from starlette.status import HTTP_200_OK

from api.dependencies import GetSessionDep, GetSettingsDep, GetUserDep, require_admin
from api.v2.models import (
    NotificationCategory,
    TaskNotification,
    TaskNotificationCreate,
    TaskNotificationDetail,
    TaskNotificationUpdate,
    safe_parse_collection,
)
from api.v2.orm import V2BackgroundJob, V2Notification
from api.v2.queries import (
    QueryMembership,
    query_engagement_notifications,
    query_notification_by_id,
    query_users_notifications,
)
from api.v2.services import ExternalServiceTracker

router = APIRouter()

logger = logging.getLogger("api")


def datetime_to_db_datetime(
    settings: GetSettingsDep, last_activity: Optional[datetime] = None
) -> Optional[datetime]:
    """
    The purpose of this function is to translate a datetime object from either an arbitrary timezone or no timezone
    to the db_timezone. After conversion, the datetime will be converted to a naive datetime as the database does not
    store timezone information and assumes that all datetime are in the db_timezone.

    Examples
    --------
    Frontend -> 2020-01-01T00:00:00Z (The Z indicates that the datetime is in UTC)
    Server -> America/New_York (The server is in us-east-1, UTC-4) 2019-12-31T20:00:00Z-04:00
    Database -> America/Los_Angeles (The database is UTC-7) 2019-12-31T17:00:00Z-07:00

    """
    if last_activity is None:
        return None

    db_timezone = settings.db_timezone

    last_activity = last_activity.astimezone(db_timezone).replace(tzinfo=None)
    return last_activity


DtFilterDep = Annotated[Optional[datetime], Depends(datetime_to_db_datetime)]


@router.get("", response_model=list[TaskNotification])
def get_notifications(
    session: GetSessionDep,
    date_filter: DtFilterDep,
    db_user: GetUserDep,
):
    """

    Get all engagement notifications that the user is associated with.

    ### Notification Types
    The `notification.data` field is guaranteed to be a list.

    #### Text
    ```json
    {
        "type": "text",
        "data": "Hello, World!"
        "timestamp": "2024-06-28T19:47:48.043639"
    }
    ```

    #### Download
    ```json
    {
        "type": "download",
        "data": {
            "label": "Download Results",
            "url": "s3://some-bucket/some-key"
        },
    }
    ```
    > Special handling should be used to detect s3 file Uris. If found, the uri
    should be
     converted to a presigned url. See [Get Presigned Url](
     http://localhost:8080/docs#/WorkflowsV2/get_presigned_url_api_v2_workflows_downloads_post)

    #### Table
    ```json
    {
        "type": "table",
        "data": {
                "some_key": "some value",
                }
    }
    ```
    > This table would have a typescript type of Record<string, string|string[]>

    #### Code
    ```json
    {
        "type": "code",
        "data": {
            "language": "python",
            "code": "print('Hello, World!')"
        }
    }
    ```
    > Code is intended to be displayed in a code block where data is the result of JSON.stringify

    #### Parameters
    ```json
    {
        "type": "parameters",
        "data":
            {
                "Canvas Name": "My Canvas",
                "Customer Files": ["SomeReport.csv", "AnotherReport.csv"],
            },
        "form_data": {
            "canvas_name": "My Canvas",
            "customer_files": [1, 2],
        }
    }
    ```
    > This structure is rather similar to the table structure, but is intended to be
    used for rendering parameters in a human-readable format and for rehydrating form data.

    """

    notification_query = query_users_notifications(
        dc_user_id=db_user.user_id, last_activity=date_filter
    )
    notifications = session.exec(notification_query).mappings().all()
    return safe_parse_collection(list[TaskNotification], notifications)


@router.get("/{dc_engagement_id}", response_model=list[TaskNotification])
def get_engagement_notifications(
    session: GetSessionDep,
    dc_engagement_id: int,
    date_filter: DtFilterDep,
):
    """Get notifications for the specified engagement using the dc_engagement_id."""

    notification_query = query_engagement_notifications(
        dc_engagement_id=dc_engagement_id, last_activity=date_filter
    )
    notifications = session.exec(notification_query).mappings().all()

    return safe_parse_collection(list[TaskNotification], notifications)


@router.get(
    "/{dc_engagement_id}/{notification_id}", response_model=TaskNotificationDetail
)
def get_notification(
    session: GetSessionDep,
    dc_engagement_id: int,
    notification_id: int,
):
    """Get a specific notification for a specific engagement."""

    notification_query = query_notification_by_id(
        dc_engagement_id=dc_engagement_id, notification_id=notification_id
    )
    notification = session.exec(notification_query).mappings().one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return TaskNotificationDetail.parse_obj(notification)


@router.post(
    "",
    dependencies=[Depends(require_admin)],
    response_model=list[TaskNotification],
)
def create_user_notifications(
    session: GetSessionDep,
    notifications: list[TaskNotificationCreate],
    db_user: GetUserDep,
):
    """
    Create new notifications for users.

    If a request_id is provided,
    it will be checked to ensure that it refers to an existing background job.
    """
    # We need to ensure that if passed, request_id refers to an existing background job

    having_request_id = (
        (notification.request_id is not None) for notification in notifications
    )
    if any(having_request_id):
        # Pick out all request_ids that are not None
        request_ids = {
            notification.request_id
            for notification in notifications
            if notification.request_id is not None
        }
        query_members = (
            QueryMembership()
            .add_orm_membership(V2BackgroundJob, list(request_ids))
            .build()
        )
        result = session.exec(query_members).all()
        non_existent_request_ids = {row.id for row in result}

        def overwrite_request_id(n: TaskNotificationCreate):
            match n.request_id:
                case None:
                    return n
                case int() as request_id if request_id in non_existent_request_ids:
                    logger.warning(
                        "Request ID %s does not exist. Removing request_id from notification.",
                        request_id,
                    )
                    n.request_id = None
                    return n
                case _:
                    return n

        if non_existent_request_ids:
            notifications = map(overwrite_request_id, notifications)

    db_notifications = V2Notification.bulk_create_from_models(
        notifications, db_user.cisco_cco_id
    )
    session.add_all(db_notifications)
    session.commit()
    for notification in db_notifications:
        session.refresh(notification)

    response = [
        TaskNotification.from_orm(notification) for notification in db_notifications
    ]

    return response


@router.post("/{notification_id}/{status}", dependencies=[Depends(require_admin)])
def update_notification_status(
    session: GetSessionDep,
    db_user: GetUserDep,
    notification_id: int,
    status: NotificationCategory,
):
    """Update the status of a notification."""

    stmt = ExternalServiceTracker.make_update_notification_status_statement(
        notification_id, status, db_user.cisco_cco_id
    )

    session.exec(stmt)
    session.commit()
    return HTTP_200_OK


@router.patch("/message/{notification_id}", dependencies=[Depends(require_admin)])
def update_notification(
    session: GetSessionDep,
    notification_id: int,
    payload: TaskNotificationUpdate,
) -> int:
    """Update a notification with additional messages and optionally subject and category."""

    if payload.data is not None:
        stmt = ExternalServiceTracker.make_message_append_statement(
            notification_id, [msg.__root__ for msg in payload.data]
        )
        session.exec(stmt)
        session.commit()

    data = payload.dict(exclude_unset=True, exclude_none=True, exclude={"data"})
    if not data:
        return HTTP_200_OK

    db_notification = session.exec(
        select(V2Notification).where(V2Notification.notification_id == notification_id)
    ).one()

    for key, value in data.items():
        setattr(db_notification, key, value)

    session.add(db_notification)
    session.commit()

    return HTTP_200_OK
