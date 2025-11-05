import json
import logging
from io import BytesIO, StringIO
from typing import Annotated, Union

import pandas as pd
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic.v1 import Json
from sqlalchemy import update
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from api.dependencies import (
    FlowV3ServiceDep,
    GetSessionDep,
    GetSettingsDep,
    GetUserDep,
    PrefectClientDep,
    S3ClientDep,
)
from api.v2.models import (
    TextMessageCreate,
    UiEnum,
    V2GenericJobErrorResponse,
    V2GenericJobResponse,
    V2ThoughtSpotDeleteTasksRequest,
    V2ThoughtSpotDeleteTasksResponse,
    V2ThoughtSpotDiscoveryRequest,
    V2ThoughtSpotInstanceRequestsModel,
    V2ThoughtSpotRefreshTagsRequest,
    V2ThoughtSpotTaskList,
    V2ThoughtSpotTaskListResult,
    V2ThoughtSpotTaskUploadWrite,
)
from api.v2.orm import (
    V2ThoughtSpotInstanceRequests,
)
from api.v2.queries import (
    build_thoughtspot_tagging_query,
    query_referenced_engagement_id,
)
from api.v2.services import ExternalServiceTracker

logger = logging.getLogger("api")
ts_task_tracker = ExternalServiceTracker(
    UiEnum.canvas_actions.value, "ThoughtSpot Task"
)
TSTaskTracker = Annotated[ExternalServiceTracker, Depends(ts_task_tracker)]
instance_tagging_tracker = ExternalServiceTracker(
    UiEnum.instance_tagging, "Instance Tagging"
)
InstanceTaggingTracker = Annotated[
    ExternalServiceTracker, Depends(instance_tagging_tracker)
]

router = APIRouter()


@router.post("/upload/{engagement_id}", response_model=V2ThoughtSpotTaskListResult)
async def upload_thoughtspot_task(
    engagement_id: int,
    records: Annotated[UploadFile, Form()],
    data: Annotated[Json[V2ThoughtSpotTaskUploadWrite], Form()],
    session: GetSessionDep,
    settings: GetSettingsDep,
    s3_client: S3ClientDep,
    db_user: GetUserDep,
):
    """Stage a Thoughtspot Tagging action with the records from a CSV file."""
    # Check that user can add tagging tasks to a given engagement

    db_engagement_query = query_referenced_engagement_id(engagement_id, db_user.user_id)
    db_engagement_id = session.exec(db_engagement_query).one_or_none()

    if not db_engagement_id:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="User does not have permissions to add tagging tasks",
        )

    file_contents = await records.read()
    await records.close()

    # Expose the file contents as a file-like object for Pandas to read
    with StringIO(file_contents.decode("utf-8")) as fp:
        try:
            df = (
                pd.read_csv(fp, usecols=["INSTANCE_ID"])
                .astype("Int64")
                .dropna()
                .drop_duplicates()
            )
        except ValueError as e:
            logger.exception(
                "Error reading CSV file for user cisco_cco_id=%s engagement_id=%s",
                db_user.cisco_cco_id,
                engagement_id,
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="The CSV file from ThoughtSpot has an invalid format. Please check the validity of your liveboard.",
            ) from e
        except Exception as e:
            logger.exception(
                "Error reading CSV file for user cisco_cco_id=%s engagement_id=%s",
                db_user.cisco_cco_id,
                engagement_id,
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="The CSV file from ThoughtSpot could not be read. Please check the validity of your liveboard.",
            ) from e

    # The CSV must have a single column of INSTANCE_ID or subsequent steps will fail
    if "INSTANCE_ID" not in df.columns:
        msg = (
            "'INSTANCE_ID' column not found in CSV file for user cisco_cco_id=%s engagement_id=%s. File has columns : %s"
            % (db_user.cisco_cco_id, engagement_id, df.columns)
        )
        logger.error(msg)
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="The CSV file from ThoughtSpot should have a column named 'INSTANCE_ID', but it was not found.",
        )

    db_ts_request = V2ThoughtSpotInstanceRequests(
        dc_engagement_id=engagement_id,
        user_id=db_user.user_id,
        tag_ids=data.tag_ids,
        tagset_ids=data.tagset_ids,
        comment=data.comment,
        user_action=data.user_action,
        canvas_id=data.canvas_id,
        count_instances=len(df),
        file_location=None,
        created_by=db_user.cisco_cco_id,
    )

    session.add(db_ts_request)
    session.commit()
    session.refresh(db_ts_request)

    ts_request_id = db_ts_request.thoughtspot_id

    # Create the file location based on ts_request_id
    bucket_name = settings.ts_tag_requests_settings.bucket
    obj_key = f"{settings.ts_tag_requests_settings.key}/{ts_request_id}.csv"
    obj_uri = f"s3://{bucket_name}/{obj_key}"

    # Dump df to bytes for upload
    fp_out = BytesIO()
    # noinspection PyTypeChecker,PydanticTypeChecker
    df.to_csv(fp_out, index=False)
    fp_out.seek(0)
    del df

    try:
        logger.info(
            "Uploading thoughtspot_task thoughtspot_id=%s to obj_uri=%s",
            db_ts_request.thoughtspot_id,
            obj_uri,
        )
        s3_client.upload_fileobj(fp_out, bucket_name, obj_key)
    except Exception as e:
        logger.exception(
            "Error Uploading thoughtspot_task for user cisco_cco_id=%s thoughtspot_id=%s",
            db_user.cisco_cco_id,
            db_ts_request.thoughtspot_id,
        )
        db_ts_request.soft_delete(db_user.cisco_cco_id, session)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 Error. Could not upload the CSV file.",
        ) from e

    db_ts_request.file_location = obj_uri
    session.commit()

    return V2ThoughtSpotTaskListResult(
        user_action=data.user_action,
        success=True,
        thoughtspot_id=db_ts_request.thoughtspot_id,
        dc_engagement_id=engagement_id,
        tag_ids=db_ts_request.tag_ids,
        tagset_ids=db_ts_request.tagset_ids,
        canvas_id=db_ts_request.canvas_id,
    )


@router.get("/{engagement_id}", response_model=list[V2ThoughtSpotInstanceRequestsModel])
def get_thoughtspot_engagement_tasks(
    engagement_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    """Get all ThoughtSpot tasks for a given engagement."""

    query = build_thoughtspot_tagging_query(
        dc_engagement_id=engagement_id, dc_user_id=db_user.user_id
    )
    db_tasks = session.exec(query).all()
    return db_tasks


@router.get(
    "/canvas_tasks/{canvas_id}", response_model=list[V2ThoughtSpotInstanceRequestsModel]
)
def get_thoughtspot_canvas_tasks(
    canvas_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    """Get ThoughtSpot tasks for a given canvas."""

    query = build_thoughtspot_tagging_query(
        canvas_id=canvas_id, dc_user_id=db_user.user_id
    )
    db_tasks = session.exec(query).all()
    return db_tasks


@router.post(
    "/actions/extracts",
    tags=["PrefectV1"],
    response_model=Union[V2GenericJobResponse, V2GenericJobErrorResponse],
)
async def process_ts_extract_tasks(
    payload: V2ThoughtSpotTaskList,
    session: GetSessionDep,
    settings: GetSettingsDep,
    s3_client: S3ClientDep,
    prefect_client: PrefectClientDep,
    tracker: TSTaskTracker,
    db_user: GetUserDep,
):
    """
    Submit one or more ThoughtSpot tasks to 'extract' the data. This will create a background job and submit it to Prefect.
    When the file is ready to download, the user will be notified in the Thoughtspot Tasks Wf tree
    """

    db_engagement_query = query_referenced_engagement_id(
        payload.dc_engagement_id, db_user.user_id
    )
    db_engagement = session.exec(db_engagement_query).one_or_none()

    if not db_engagement:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action",
        )

    prefect_parameters = {
        "list_of_ids": payload.idList,
        "columns_to_extract": str(payload.columnsToExtract),
        "env": str(settings.env),
        "dc_engagement_id": payload.dc_engagement_id,
        "requested_by": db_user.cisco_cco_id,
        "request_id": None,
        "notification_id": None,
    }

    db_background_job, db_notification = tracker.create_job(
        dc_engagement_id=payload.dc_engagement_id,
        parameters=prefect_parameters,
        db_session=session,
        external_job_id=settings.prefect_settings.extract_ts_version_group_id,
        subject="Tagging Extract",
        messages=[
            TextMessageCreate(
                type="text",
                data=f"Starting Extract of '"
                f"{payload.columnsToExtract}' "
                f"for {len(payload.idList)} "
                f"ThoughtSpot Tasks",
            )
        ],
    )

    prefect_parameters.update(
        {
            "request_id": str(db_background_job.request_id),
            "notification_id": db_notification.notification_id,
        }
    )

    extract_body = json.dumps(prefect_parameters).encode("utf-8")

    try:
        logger.info("Uploading extract payload to S3")
        s3_client.put_object(
            Bucket="dc-tags-messaging.prod",
            Key=f"requests/{payload.dc_engagement_id}-{db_background_job.request_id}.json",
            Body=extract_body,
        )
    except Exception as e:
        tracker.handle_job_error(
            db_session=session,
            db_notification=db_notification,
            message=TextMessageCreate(type="text", data="Error writing to S3"),
            exception=e,
        )
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Error writing to S3"
        ) from e

    logger.info(
        "Uploaded extract request_id=%s payload idList=%s to S3",
        db_background_job.request_id,
        payload.idList,
    )

    run_name = f"extract-{db_user.cisco_cco_id.replace('@cisco.com', '')}-{db_background_job.request_id}-{db_notification.notification_id}"

    try:
        run_id = prefect_client.create_flow_run(
            version_group_id=settings.prefect_settings.extract_ts_version_group_id,
            labels=settings.prefect_settings.extract_ts_flow_labels,
            parameters=prefect_parameters,
            run_name=run_name,
        )
        logger.info(
            "Submitted Extract Job request_id=%s logged_user=%s run_id=%s",
            db_background_job.request_id,
            db_user.cisco_cco_id,
            run_id,
        )
        db_background_job.external_run_id = run_id
        session.add(db_background_job)
        session.commit()
        session.refresh(db_background_job)
        return V2GenericJobResponse(
            request_id=db_background_job.request_id,
            notification_id=db_notification.notification_id,
            external_job_id=settings.prefect_settings.extract_ts_version_group_id,
            external_run_id=run_id,
            message="Submitted Extract Job",
            success=True,
        )

    except Exception as e:
        tracker.handle_job_error(
            db_session=session,
            db_notification=db_notification,
            message=TextMessageCreate(type="text", data="Error submitting extract job"),
            exception=e,
        )
        logger.exception("Error submitting extract job: %r", e)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting extract job",
        ) from e


@router.delete("")
def delete_thoughtspot_tasks(
    payload: V2ThoughtSpotDeleteTasksRequest,
    db_user: GetUserDep,
    session: GetSessionDep,
    settings: GetSettingsDep,
):
    """Delete ThoughtSpot Tasks by Ids"""
    ts_ids = payload.thoughtspot_ids
    stmt = (
        update(V2ThoughtSpotInstanceRequests)
        .where(V2ThoughtSpotInstanceRequests.thoughtspot_id.in_(ts_ids))
        .where(V2ThoughtSpotInstanceRequests.user_id == db_user.user_id)
        .where(V2ThoughtSpotInstanceRequests.is_deleted == "F")
        .values(
            {
                V2ThoughtSpotInstanceRequests.is_deleted: "T",
                V2ThoughtSpotInstanceRequests.update_dtm: settings.get_db_datetime_now(),
                V2ThoughtSpotInstanceRequests.updated_by: db_user.cisco_cco_id,
            }
        )
    )
    try:
        session.exec(stmt)
        session.commit()
        return V2ThoughtSpotDeleteTasksResponse(thoughtspot_ids=ts_ids)
    except Exception as e:
        logger.exception(
            "Error soft-deleting thoughtspot tasks for user %s ts_ids=%s",
            db_user.cisco_cco_id,
            ts_ids,
        )
        session.rollback()
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting thoughtspot tasks",
        ) from e


@router.post(
    "/refresh-tagsets", response_model=V2GenericJobResponse, tags=["PrefectV3"]
)
def refresh_tagsets(
    data: V2ThoughtSpotRefreshTagsRequest,
    session: GetSessionDep,
    flow_service: FlowV3ServiceDep,
    db_user: GetUserDep,
    tracker: TSTaskTracker,
):
    """Call a prefect flow to rebuild the Canvas View to reflect any changes in the tagging"""

    db_engagement_query = query_referenced_engagement_id(
        data.dc_engagement_id, db_user.user_id
    )

    db_engagement = session.exec(db_engagement_query).one_or_none()
    if not db_engagement:
        # Not authorized
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action",
        )

    # Create background job to get request_id
    with flow_service:
        response = flow_service.refresh_canvas_view_flow(
            canvas_id=data.canvas_id,
            requestor=db_user,
            dc_engagement_id=data.dc_engagement_id,
            tracker=tracker,
        )

    return response


@router.post("/discover", tags=["PrefectV3"])
def run_discovery_flow(
    data: V2ThoughtSpotDiscoveryRequest,
    db_user: GetUserDep,
    session: GetSessionDep,
    flow_service: FlowV3ServiceDep,
    tracker: TSTaskTracker,
) -> V2GenericJobResponse:
    """Run dc-canvas-service SyncService"""

    request_id = tracker.get_next_request_id(db_session=session)
    db_notification = tracker.create_notification(
        dc_engagement_id=data.dc_engagement_id,
        db_session=session,
        subject=f"Discovery for Canvas #{data.canvas_id}",
        user_id=db_user.user_id,
        request_id=request_id,
    )

    with flow_service:
        try:
            flow_service.emit_liveboard_discovery_requested(
                canvas_id=data.canvas_id,
                dc_user_id=db_user.user_id,
                dc_engagement_id=data.dc_engagement_id,
                request_id=request_id,
                notification_id=db_notification.notification_id,
            )
            return V2GenericJobResponse(
                request_id=request_id,
                notification_id=db_notification.notification_id,
                external_job_id=None,
                external_run_id=None,
                message="Submitted Discovery Job",
                success=True,
            )
        except Exception as e:
            tracker.handle_job_error(
                db_session=session,
                db_notification=db_notification,
                message=TextMessageCreate(
                    type="text", data="Error submitting discovery job"
                ),
                exception=e,
            )
            logger.exception("Error submitting discovery job: %r", e)
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error submitting discovery job",
            ) from e
