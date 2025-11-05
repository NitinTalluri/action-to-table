import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import parse_obj_as
from pydantic.v1 import Json
from starlette.status import (
    HTTP_202_ACCEPTED,
)

from api.dependencies import (
    FlowV3ServiceDep,
    GetUserDep,
)
from api.dependencies.database import GetEngineDep
from api.v2.models import (
    TagsetTagModel,
    UiEnum,
    V2BulkInstanceTaggingPayload,
    V2GenericJobResponse,
    V2SerialTaggingPayload,
    V2WriteTags,
)
from api.v2.queries.tagsets import query_tagsets_from_tag_ids
from api.v2.services import (
    ExternalServiceTracker,
)

router = APIRouter()

logger = logging.getLogger("api")

serial_tagging_tracker = ExternalServiceTracker(UiEnum.serial_tagging, "Serial Tagging")
SerialTaggingTracker = Annotated[
    ExternalServiceTracker, Depends(serial_tagging_tracker)
]
instance_tagging_tracker = ExternalServiceTracker(
    UiEnum.instance_tagging, "Instance Tagging"
)
InstanceTaggingTracker = Annotated[
    ExternalServiceTracker, Depends(instance_tagging_tracker)
]
bulk_tagging_tracker = ExternalServiceTracker(UiEnum.bulk_tagging, "Bulk Tagging")
BulkTaggingTracker = Annotated[ExternalServiceTracker, Depends(bulk_tagging_tracker)]


@router.post("/serial_tagging", tags=["File Upload", "PrefectV3"])
async def submit_serial_tagging(
    payload: Annotated[Json[V2SerialTaggingPayload], Form()],
    data: Annotated[UploadFile, Form()],
    flow_service: FlowV3ServiceDep,
    db_user: GetUserDep,
    tracker: SerialTaggingTracker,
    engine: GetEngineDep,
) -> V2GenericJobResponse:
    """
    Submit Serial Numbers for Resolution
    Compressed JSON should be an array of objects like {"serial_number": "1234567890"}
    """
    _data_content = await data.read()
    tagset_query = query_tagsets_from_tag_ids(tag_ids=payload.tag_ids)
    with engine.begin() as conn:
        tagset_result = conn.execute(tagset_query).mappings().all()

    tagset_tag_ids = parse_obj_as(list[TagsetTagModel], tagset_result)

    found_tags = {row.tag_id for row in tagset_tag_ids}
    missing_tags = {tag_id for tag_id in payload.tag_ids if tag_id not in found_tags}
    if missing_tags:
        raise HTTPException(
            status_code=404,
            detail=f"These tag_ids do not exist: {missing_tags}",
        )

    with flow_service as service:
        response = service.create_serial_tagging_flow(
            payload=payload,
            data=_data_content,
            tagset_tag_ids=tagset_tag_ids,
            requestor=db_user,
            tracker=tracker,
        )
    return response


@router.post(
    "/instance_tagging",
    status_code=HTTP_202_ACCEPTED,
    tags=["File Upload", "PrefectV3"],
)
async def submit_instance_tagging(
    payload: Annotated[Json[V2WriteTags], Form()],
    data: Annotated[UploadFile, Form()],
    flow_service: FlowV3ServiceDep,
    db_user: GetUserDep,
    engine: GetEngineDep,
    tracker: InstanceTaggingTracker,
) -> V2GenericJobResponse:
    """
    Tag one or more instances with one or more tag_ids.
    """

    _data_content = await data.read()
    tagset_query = query_tagsets_from_tag_ids(tag_ids=payload.tag_ids)
    with engine.begin() as conn:
        tagset_result = conn.execute(tagset_query).mappings().all()

    tagset_tag_ids = parse_obj_as(list[TagsetTagModel], tagset_result)

    found_tags = {row.tag_id for row in tagset_tag_ids}
    missing_tags = {tag_id for tag_id in payload.tag_ids if tag_id not in found_tags}
    if missing_tags:
        raise HTTPException(
            status_code=404,
            detail=f"These tag_ids do not exist: {missing_tags}",
        )
    with flow_service as service:
        response = service.create_instance_tagging_flow(
            payload=payload,
            data=_data_content,
            tagset_tag_ids=tagset_tag_ids,
            requestor=db_user,
            tracker=tracker,
        )

    return response


@router.post(
    "/bulk_instance_tagging",
    status_code=HTTP_202_ACCEPTED,
    tags=["File Upload", "PrefectV3"],
)
async def submit_bulk_instance_tagging(
    payload: Annotated[Json[V2BulkInstanceTaggingPayload], Form()],
    data: Annotated[UploadFile, Form()],
    db_user: GetUserDep,
    flow_service: FlowV3ServiceDep,
    tracker: BulkTaggingTracker,
):
    """
    Submit a Bulk Tagging Payload.
    Instance Tagging Format of GZIP compressed JSON:
    ```json
    [{
        id: 'number',
        tagset_id: 'number',
        tag_name: 'string'
    }]
    ```
    Serial Number Tagging Format of GZIP compressed JSON:
    ```json
    [{
        id: 'string',
        tagset_id: 'number',
        tag_name: 'string'
    }]

    """

    _data_content = await data.read()

    with flow_service as service:
        response = service.create_bulk_tagging_flow(
            payload=payload,
            data=_data_content,
            requestor=db_user,
            tracker=tracker,
        )

    return response
