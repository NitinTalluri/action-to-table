import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy import VARCHAR, text, update
from sqlmodel import cast, func, select

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models import (
    CreateMessage,
    NotificationCategory,
    TCreateMessage,
    TextMessage,
    UiEnum,
)
from api.v2.orm import V2ActionItem, V2BackgroundJob, V2Notification

if TYPE_CHECKING:
    from sqlmodel import Session

logger = logging.getLogger("api")


class ExternalServiceTracker:
    """
    Repository pattern that orchestrates background jobs, notifications and relating them.
    The logic for doing so is complex and bridges the UI expectations with External Job expectations.

    The user is mostly focused on notifications, whereas the system cares more about background jobs.

    When a user wants additional details via audit log, then we can include the background job details.
    """

    message: Optional[TextMessage]

    def __init__(
        self,
        ui_enum: UiEnum,
        default_subject: str,
        default_message: Optional[str] = None,
    ):
        self.ui_enum = ui_enum.value if hasattr(ui_enum, "value") else str(ui_enum)
        self.subject = default_subject
        self.message = (
            self.format_text_message(default_message) if default_message else None
        )
        self.request_id = None
        self.user_id = None
        self.cisco_cco_id = None
        self.tree_id = None
        self.notification_id = None

    def _lookup_ui_enum(self, session) -> Optional[int]:
        query = select(V2ActionItem.tree_id).where(V2ActionItem.ui_enum == self.ui_enum)
        result = session.exec(query).one()
        return result

    def __call__(self, session: GetSessionDep, db_user: GetUserDep):
        self.tree_id = self._lookup_ui_enum(session)
        self.user_id = db_user.user_id
        self.cisco_cco_id = db_user.cisco_cco_id
        return self

    def get_next_request_id(self, db_session: "Session") -> int:
        """
        Get the next request_id for a background job.
        """
        stmt = text("select seq_dc_request.nextval")
        result = db_session.exec(stmt).scalar_one()
        db_session.commit()
        return result

    def get_next_notification_id(self, db_session: "Session") -> int:
        """
        Get the next notification_id for a notification.
        """
        stmt = text("select dc_wf_notification_seq.nextval")
        result = db_session.exec(stmt).scalar_one()
        db_session.commit()
        return result

    def create_notification(
        self,
        dc_engagement_id: int,
        db_session: "Session",
        messages: Optional[list[TCreateMessage]] = None,
        subject: Optional[str] = None,
        user_id: Optional[int] = None,
        request_id: Optional[int] = None,
        notification_id: Optional[int] = None,
    ) -> V2Notification:
        msgs = [self.message] if self.message else []
        if messages:
            msgs.extend(messages)

        db_notification = V2Notification(
            tree_id=self.tree_id,
            dc_engagement_id=dc_engagement_id,
            notification_category=NotificationCategory.PENDING.value,
            data=[msg.dict() for msg in msgs],
            dc_user_id=user_id or self.user_id,
            subject=subject or self.subject,
            request_id=request_id or self.request_id,
            created_by=self.cisco_cco_id,
        )
        if notification_id is not None:
            db_notification.notification_id = notification_id
        db_session.add(db_notification)
        db_session.commit()
        db_session.refresh(db_notification)
        self.notification_id = db_notification.notification_id
        return db_notification

    def create_job(
        self,
        dc_engagement_id: int,
        parameters: dict,
        db_session: "Session",
        external_job_id: str,
        workflow_data: Optional[dict] = None,
        user_id: Optional[int] = None,
        messages: Optional[list[TCreateMessage]] = None,
        subject: Optional[str] = None,
        canvas_id: Optional[int] = None,
        request_id: Optional[int] = None,
        notification_id: Optional[int] = None,
    ) -> tuple[V2BackgroundJob, V2Notification]:
        db_background_job = V2BackgroundJob(
            dc_engagement_id=dc_engagement_id,
            dc_user_id=user_id or self.user_id,
            parameters=parameters,
            external_job_id=external_job_id,
            workflow_enum=self.ui_enum,
            workflow_data=workflow_data,
            created_by=self.cisco_cco_id,
            canvas_id=canvas_id,
        )
        if request_id is not None:
            db_background_job.request_id = request_id
        db_session.add(db_background_job)
        db_session.commit()
        db_session.refresh(db_background_job)
        self.request_id = db_background_job.request_id

        msgs: list[TCreateMessage] = [self.message] if self.message else []
        if messages:
            msgs.extend(messages)

        db_notification = self.create_notification(
            dc_engagement_id,
            db_session,
            messages=msgs,
            subject=subject,
            user_id=user_id,
            notification_id=notification_id,
        )

        return db_background_job, db_notification

    def attach_notification(
        self,
        db_session: "Session",
        request_id: int,
        subject: str,
        tree_id: int,
        dc_engagement_id: int,
        user_id: int,
        data: list[CreateMessage],
        category: NotificationCategory,
    ):
        """
        External job calls this method to attach a new notification to a background job
        """

        db_notification = V2Notification(
            tree_id=tree_id,
            dc_engagement_id=dc_engagement_id,
            notification_category=category.value,
            data=[d.dict() for d in data],
            dc_user_id=user_id,
            subject=subject,
            request_id=request_id,
        )

        db_session.add(db_notification)
        db_session.commit()
        db_session.refresh(db_notification)
        return db_notification

    def format_text_message(self, message: str) -> TextMessage:
        return TextMessage(data=message, timestamp=datetime.utcnow(), type="text")

    def format_exception(self, exception: Exception) -> TextMessage:
        str_exception = f"Details of exception: \n{exception!s}"
        return self.format_text_message(str_exception)

    def handle_job_error(
        self,
        db_session,
        db_notification: V2Notification,
        message: TCreateMessage,
        exception: Optional[Exception] = None,
    ) -> V2Notification:
        """
        If the call to schedule an external job fails, we need to update the notification object and use the 'data' field to store the error message
        """

        data = db_notification.data or []
        new_data = [
            line
            for line in (
                message,
                self.format_exception(exception) if exception else None,
            )
            if line is not None
        ]
        db_notification.data = [*data, *[msg.dict() for msg in new_data]]
        db_notification.notification_category = NotificationCategory.ERROR.value
        db_session.add(db_notification)
        db_session.commit()
        db_session.refresh(db_notification)
        return db_notification

    @classmethod
    def make_update_notification_status_statement(
        cls, notification_id: int, status: NotificationCategory, updated_by: str
    ):
        """
        Generate an update statement to change the status of a notification.
        """

        stmt = (
            update(V2Notification)
            .where(V2Notification.notification_id == notification_id)
            .values(
                notification_category=status.value,
                update_dtm=func.utc_time(),
                is_deleted="F",
                updated_by=updated_by,
            )
        )

        return stmt

    @classmethod
    def make_message_append_statement(
        cls, notification_id: int, messages: list[TCreateMessage]
    ):
        """
        Generate an update statement to append a message to the notification data field.

        This column is stored as VARCHAR but is JSON data. It is potentially null. The details of working with JSON
        in snowflake sqlalchemy are a bit ugly hence this helper method.
        """
        data = json.dumps(
            [jsonable_encoder(msg.dict()) for msg in messages], separators=(",", ":")
        )

        existing_is_null = V2Notification.data.is_(None)

        existing_as_json = func.parse_json(V2Notification.data)
        existing_as_array = func.to_array(existing_as_json)

        input_json = func.to_array(func.parse_json(data))

        set_data_to_input = cast(input_json, VARCHAR)

        extend_input_on_existing = cast(
            func.array_cat(existing_as_array, input_json), VARCHAR
        )

        update_inner_stmt = func.iff(
            existing_is_null, set_data_to_input, extend_input_on_existing
        )

        stmt = (
            update(V2Notification)
            .where(V2Notification.notification_id == notification_id)
            .values(data=update_inner_stmt, update_dtm=func.utc_time())
        )

        return stmt
