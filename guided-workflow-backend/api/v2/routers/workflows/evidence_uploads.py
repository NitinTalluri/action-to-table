import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic import Json

from api.dependencies import FlowServiceDep, FlowV3ServiceDep, GetSessionDep, GetUserDep
from api.v2.models import (
    UiEnum,
    V2CollectorFileUpload,
    V2CustomerFileUpload,
    V2GenericJobResponse,
    V2GenericResponse,
)
from api.v2.services import ExternalServiceTracker

customer_uploads_tracker = ExternalServiceTracker(
    UiEnum.customer_upload, "Customer File Upload"
)
CustomerUploadsTracker = Annotated[
    ExternalServiceTracker, Depends(customer_uploads_tracker)
]

collector_uploads_tracker = ExternalServiceTracker(
    UiEnum.collector_upload, "Collector File Upload"
)
CollectorUploadsTracker = Annotated[
    ExternalServiceTracker, Depends(collector_uploads_tracker)
]


router = APIRouter()
logger = logging.getLogger("api")


@router.post(
    "/customer", response_model=V2GenericJobResponse, tags=["File Upload", "PrefectV3"]
)
async def submit_customer_file(
    payload: Annotated[Json[V2CustomerFileUpload], Form()],
    data: Annotated[UploadFile, Form()],
    session: GetSessionDep,
    flow_service: FlowV3ServiceDep,
    db_user: GetUserDep,
    tracker: CustomerUploadsTracker,
):
    _data_content = await data.read()
    with flow_service as service:
        try:
            result = service.create_evidence_customer_flow(
                payload=payload,
                data=_data_content,
                requestor=db_user,
                tracker=tracker,
            )
            session.commit()
        except Exception as e:
            logger.exception("Error submitting Customer File")
            session.rollback()
            raise HTTPException(
                status_code=500, detail="Error submitting Customer File"
            ) from e

    return result


@router.post(
    "/collector", response_model=V2GenericJobResponse, tags=["File Upload", "PrefectV3"]
)
async def submit_collector_file(
    payload: Annotated[Json[V2CollectorFileUpload], Form()],
    data: Annotated[UploadFile, Form()],
    session: GetSessionDep,
    flow_service: FlowV3ServiceDep,
    db_user: GetUserDep,
    tracker: CollectorUploadsTracker,
):
    """
    Submit Collector File Upload (multipart: payload + gzip data)
    """
    _data_content = await data.read()
    with flow_service as service:
        try:
            result = service.create_evidence_collector_flow(
                payload=payload,
                data=_data_content,
                requestor=db_user,
                tracker=tracker,
            )
            session.commit()
        except Exception as e:
            logger.exception("Error submitting Collector File")
            session.rollback()
            raise HTTPException(
                status_code=500, detail="Error submitting Collector File"
            ) from e

    return result
