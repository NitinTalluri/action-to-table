import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, UploadFile
from pydantic.v1 import Json
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from api.dependencies import GetSettingsDep, GetUserDep, S3ClientDep
from api.dependencies.database import GetEngineDep
from api.v2.models import (
    UiEnum,
    V2GenericJobResponse,
    V2SEAUploadPayload,
)
from api.v2.services import ExternalServiceTracker

sea_uploads_tracker = ExternalServiceTracker(UiEnum.sea_upload, "SEA File Upload")
SEAUploadsTracker = Annotated[ExternalServiceTracker, Depends(sea_uploads_tracker)]

router = APIRouter()

logger = logging.getLogger("api")


@router.post("/sea_upload", response_model=V2GenericJobResponse)
async def submit_sea_upload(
    payload: Annotated[Json[V2SEAUploadPayload], Form()],
    settings: GetSettingsDep,
    db_user: GetUserDep,
    engine: GetEngineDep,
    background_tasks: BackgroundTasks,
    data: Annotated[UploadFile, Form()],
    s3_client: S3ClientDep,
    tracker: SEAUploadsTracker,
):
    _data_content = await data.read()
    # noinspection PyTypeChecker
    session_local = sessionmaker(bind=engine, class_=Session)
    with session_local() as session:
        request_id = tracker.get_next_request_id(db_session=session)
        notification_id = tracker.get_next_notification_id(db_session=session)

    from api.v2 import process_sea_upload

    background_tasks.add_task(
        process_sea_upload,
        payload=payload,
        file_content=_data_content,
        engine=engine,
        settings=settings,
        s3_client=s3_client,
        tracker=tracker,
        request_id=request_id,
        notification_id=notification_id,
        user={
            "cisco_cco_id": db_user.cisco_cco_id,
            "dc_user_id": db_user.user_id,
        },
    )

    return V2GenericJobResponse(
        request_id=request_id,
        notification_id=notification_id,
        message="SEA Upload job submitted successfully.",
        external_job_id=None,
        external_run_id=None,
        success=True,
    )
