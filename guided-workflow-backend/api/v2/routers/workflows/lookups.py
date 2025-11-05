import logging
from typing import Annotated, Union

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic.v1 import Json
from starlette.status import HTTP_403_FORBIDDEN

from api.dependencies import (
    FlowServiceDep,
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
    V2AcatDiscoveryModel,
    V2GenericJobErrorResponse,
    V2GenericJobResponse,
    V2HostNameSiteMovesModel,
    V2SiteReportUpload,
    V2SNIFReportUpload,
    V2TagHistoryReportUpload,
)
from api.v2.queries import query_referenced_engagement_id
from api.v2.services import ExternalServiceTracker

router = APIRouter()

logger = logging.getLogger("api")


snif_report_tracker = ExternalServiceTracker(UiEnum.snif_report, "SNIF Report")
SnifReportTracker = Annotated[ExternalServiceTracker, Depends(snif_report_tracker)]
site_report_tracker = ExternalServiceTracker(UiEnum.site_report, "Site Report")
SiteReportTracker = Annotated[ExternalServiceTracker, Depends(site_report_tracker)]
tag_history_tracker = ExternalServiceTracker(UiEnum.tag_history, "Tag History")
TagHistoryTracker = Annotated[ExternalServiceTracker, Depends(tag_history_tracker)]
host_name_site_move_tracker = ExternalServiceTracker(
    UiEnum.host_name_site_moves, "Hostname Site Moves"
)
HostNameSiteMoveTracker = Annotated[
    ExternalServiceTracker, Depends(host_name_site_move_tracker)
]
host_name_relink_tracker = ExternalServiceTracker(
    UiEnum.host_name_relink, "Hostname Relink"
)
HostNameRelinkTracker = Annotated[
    ExternalServiceTracker, Depends(host_name_relink_tracker)
]
acat_discovery_tracker = ExternalServiceTracker(UiEnum.acat_discovery, "ACAT Discovery")
AcatDiscoveryTracker = Annotated[
    ExternalServiceTracker, Depends(acat_discovery_tracker)
]


@router.post("/acat-discovery", tags=["PrefectV3"])
def generate_acat_report(
    payload: V2AcatDiscoveryModel,
    flow_service: FlowV3ServiceDep,
    db_user: GetUserDep,
    tracker: AcatDiscoveryTracker,
) -> V2GenericJobResponse:
    with flow_service:
        try:
            run_result = flow_service.create_acat_discovery_flow(
                dc_engagement_id=payload.engagement_id,
                requestor=db_user,
                tracker=tracker,
            )
        except Exception as e:
            logger.exception("Error submitting ACAT Discovery Job")
            raise HTTPException(
                status_code=500, detail="Error submitting ACAT Discovery Job"
            ) from e

    return V2GenericJobResponse(
        request_id=run_result.request_id,
        notification_id=run_result.notification_id,
        external_job_id=run_result.external_job_id,
        external_run_id=run_result.external_run_id,
        message="Submitted ACAT Discovery Job",
        success=True,
    )


@router.post(
    "/snif-report",
)
def generate_snif_report(
    payload: V2SNIFReportUpload,
    session: GetSessionDep,
    prefect_client: PrefectClientDep,
    settings: GetSettingsDep,
    s3_client: S3ClientDep,
    db_user: GetUserDep,
    tracker: SnifReportTracker,
) -> Union[V2GenericJobResponse, V2GenericJobErrorResponse]:
    """Upload SNIF report"""
    # __root__ is a Pydantic feature that allows for discriminated unions

    data = payload.__root__
    db_engagement_query = query_referenced_engagement_id(
        data.engagement_id, db_user.user_id
    )

    db_engagement = session.exec(db_engagement_query).one_or_none()
    if not db_engagement:
        # Not authorized
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action",
        )

    # Add the background job to get a request id

    requested_by = db_user.cisco_cco_id
    version_group_id = settings.prefect_settings.snif_report_version_group_id
    labels = settings.prefect_settings.snif_report_flow_labels
    run_config = settings.prefect_settings.snif_report_run_config.to_object()
    prefect_parameters = {
        "env": str(settings.env),
        "requested_by": requested_by,
        "request_json_loc": {},
        "dc_engagement_id": data.engagement_id,
    }

    db_background, db_notification = tracker.create_job(
        dc_engagement_id=data.engagement_id,
        parameters=prefect_parameters,
        db_session=session,
        external_job_id=version_group_id,
        workflow_data=data.dict(exclude={"ids"}),
    )

    request_id = db_background.request_id
    notification_id = db_notification.notification_id

    prefect_parameters.update(
        {"request_id": request_id, "notification_id": notification_id}
    )

    s3_bucket = "dc-json-requests"
    s3_key = f"{settings.env!s}/snif-report/{request_id}.json"
    request_json_loc = f"s3://{s3_bucket}/{s3_key}"

    log_prefix = f"[SNIF Report {request_id=}, {requested_by=}] "

    logger.info("%s - Uploading to S3: %s", log_prefix, request_json_loc)

    try:
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=data.json().encode("utf-8"),
        )

    except ClientError as err:
        logger.exception("Error uploading to S3")
        tracker.handle_job_error(
            session,
            db_notification,
            TextMessageCreate(data="Error uploading to S3", type="text"),
            err,
        )

    prefect_parameters.update({"request_json_loc": request_json_loc})

    logger.info("%s - Uploaded JSON to S3, submitting SNIF Report Job", log_prefix)

    try:
        run_id = prefect_client.create_flow_run(
            version_group_id=version_group_id,
            parameters=prefect_parameters,
            labels=labels,
            run_config=run_config,
        )
        logger.info("%s - Submitted SNIF Report Job run_id='%s'", log_prefix, run_id)
        db_background.external_run_id = run_id
        session.add(db_background)
        session.commit()
        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=version_group_id,
            external_run_id=run_id,
            message="Submitted SNIF Report Job",
            success=True,
        )
    except Exception as e:
        logger.exception("%s - Error submitting SNIF Report Job", log_prefix)
        tracker.handle_job_error(
            session,
            db_notification,
            TextMessageCreate(data="Error submitting SNIF Report Job", type="text"),
            e,
        )
        raise HTTPException(
            status_code=500, detail="Error submitting SNIF Report Job"
        ) from e


@router.post(
    "/site-report",
)
def generate_site_report(
    data: V2SiteReportUpload,
    session: GetSessionDep,
    prefect_client: PrefectClientDep,
    settings: GetSettingsDep,
    db_user: GetUserDep,
    tracker: SiteReportTracker,
) -> Union[V2GenericJobResponse, V2GenericJobErrorResponse]:
    """Generate site report"""

    db_engagement_query = query_referenced_engagement_id(
        data.engagement_id, db_user.user_id
    )

    db_engagement = session.exec(db_engagement_query).one_or_none()
    if not db_engagement:
        # Not authorized
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action",
        )

    requested_by = db_user.cisco_cco_id
    prefect_parameters = {
        "env": str(settings.env),
        "requested_by": requested_by,
        "request_json": data.dict(),
        "dc_engagement_id": data.engagement_id,
    }

    # Add the background job to get a request id

    version_group_id = settings.prefect_settings.site_report_version_group_id
    labels = settings.prefect_settings.site_report_flow_labels
    run_config = (
        settings.prefect_settings.site_report_run_config.to_object()
        if settings.prefect_settings.site_report_run_config
        else None
    )

    db_background, db_notification = tracker.create_job(
        dc_engagement_id=data.engagement_id,
        parameters=prefect_parameters,
        db_session=session,
        external_job_id=version_group_id,
        workflow_data=data.dict(),
    )

    request_id = db_background.request_id
    notification_id = db_notification.notification_id
    prefect_parameters.update(
        {"request_id": request_id, "notification_id": db_notification.notification_id}
    )

    log_prefix = f"[Site Report {request_id=}, {requested_by=}] "

    logger.info("%s - Submitting Site Report Job", log_prefix)

    try:
        run_id = prefect_client.create_flow_run(
            version_group_id=version_group_id,
            parameters=prefect_parameters,
            labels=labels,
            run_config=run_config,
        )
        logger.info("%s - Submitted Site Report Job run_id='%s'", log_prefix, run_id)
        db_background.external_run_id = run_id
        session.add(db_background)
        session.commit()
        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=version_group_id,
            external_run_id=run_id,
            message="Submitted Site Report Job",
            success=True,
        )
    except Exception as e:
        logger.exception("%s - Error submitting Prefect job", log_prefix)
        tracker.handle_job_error(
            session,
            db_notification,
            TextMessageCreate(data="Error submitting Prefect job", type="text"),
            e,
        )
        raise HTTPException(
            status_code=500, detail="Error submitting Prefect job"
        ) from e


@router.post(
    "/tag-history",
    response_model=V2GenericJobResponse,
    tags=["PrefectV3", "File Upload"],
)
async def generate_tag_history_report(
    payload: Annotated[Json[V2TagHistoryReportUpload], Form()],
    data: Annotated[UploadFile, Form()],
    db_user: GetUserDep,
    flow_service: FlowV3ServiceDep,
    tracker: TagHistoryTracker,
):
    """Generate tag history report"""

    _data_content = await data.read()
    with flow_service as service:
        return service.create_tag_history_flow(
            payload=payload,
            data=_data_content,
            tracker=tracker,
            requestor=db_user,
        )


@router.post(
    "/host-name-site-moves", response_model=V2GenericJobResponse, tags=["PrefectV1"]
)
def generate_host_name_site_moves(
    flow_service: FlowServiceDep,
    payload: V2HostNameSiteMovesModel,
    db_user: GetUserDep,
    tracker: HostNameSiteMoveTracker,
):
    with flow_service:
        try:
            run_result = flow_service.create_host_name_site_moves_flow(
                dc_engagement_id=payload.engagement_id,
                tracker=tracker,
                db_user=db_user,
            )
        except Exception as e:
            logger.exception("Error submitting Host Name Site Moves Job")
            raise HTTPException(
                status_code=500, detail="Error submitting Host Name Site Moves Job"
            ) from e

    return V2GenericJobResponse(
        request_id=run_result.request_id,
        notification_id=run_result.notification_id,
        external_job_id=run_result.external_job_id,
        external_run_id=run_result.external_run_id,
        message="Submitted Host Name Site Moves Job",
        success=True,
    )


@router.post("/host-name-relink", tags=["PrefectV3"])
def generate_host_name_relink(
    payload: V2HostNameSiteMovesModel,
    flow_service: FlowV3ServiceDep,
    db_user: GetUserDep,
    tracker: HostNameRelinkTracker,
) -> V2GenericJobResponse:
    with flow_service:
        try:
            run_result = flow_service.create_host_name_relink_flow(
                dc_engagement_id=payload.engagement_id,
                requestor=db_user,
                tracker=tracker,
            )
        except Exception as e:
            logger.exception("Error submitting Host Name Relink Job")
            raise HTTPException(
                status_code=500, detail="Error submitting Host Name Relink Job"
            ) from e

    return V2GenericJobResponse(
        request_id=run_result.request_id,
        notification_id=run_result.notification_id,
        external_job_id=run_result.external_job_id,
        external_run_id=run_result.external_run_id,
        message="Submitted Host Name Relink Job",
        success=True,
    )
