from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic.v1 import Json
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from api.dependencies import FlowV3ServiceDep, GetSettingsDep, GetUserDep, S3ClientDep
from api.dependencies.database import GetEngineDep
from api.v2 import ExternalServiceTracker, PrefectV3FlowService
from api.v2.models import UiEnum, V2GenericJobResponse
from api.v2.models.workflows.macd import (
    MacdAuditPayload,
    MacdHeaderResponseRow,
    MacdSubmissionPayload,
    ModelSchema,
)

macd_uploads_tracker = ExternalServiceTracker(UiEnum.macd_upload, "MACD File Upload")
MACDUploadsTracker = Annotated[ExternalServiceTracker, Depends(macd_uploads_tracker)]

macd_historical_uploads_tracker = ExternalServiceTracker(
    UiEnum.macd_historical_upload, "MACD Historical Upload"
)
MACDHistoricalUploadsTracker = Annotated[
    ExternalServiceTracker, Depends(macd_historical_uploads_tracker)
]

macd_audit_tracker = ExternalServiceTracker(UiEnum.macd_audit, "MACD Audit")
MACDAuditTracker = Annotated[ExternalServiceTracker, Depends(macd_audit_tracker)]

router = APIRouter()


@router.get("/schemas", response_model=list[ModelSchema])
async def get_macd_schemas():
    """
    Retrieves an array of MACD schemas. Each schema contains `tool_name` and `tool_action` fields
    that identify which tool and action the schema is for.

    The response is a flat array of JSON Schema objects.

    `tool_name` and `tool_action` can be treated as enums.

    Action Schemas are [JSON Schemas](https://json-schema.org/)

    If additional metadata is required, this will be annotated in the json_schema_extra section at the field level.
    Additional metadata may be available such as `order` at the model level.

    An example schema in the array:
    ```json
    {
      "title": "AMRRDelinkSchema",
      "type": "object",
      "properties": {
        "tool_name": {
          "title": "Tool Name",
          "default": "amrr",
          "enum": [
            "amrr"
          ],
          "type": "string"
        },
        "tool_action": {
          "title": "Tool Action",
          "default": "delink",
          "enum": [
            "delink"
          ],
          "type": "string"
        },
        "instance_id": {
          "title": "INSTANCE NUMBER (Mandatory)",
          "type": "integer"
        },
        "parent_instance_id": {
          "title": "PARENT INSTANCE NUMBER (Mandatory)",
          "type": "integer"
        }
      },
      "required": [
        "instance_id",
        "parent_instance_id"
      ],
      "order": [
        "instance_id",
        "parent_instance_id"
      ]
    }
    ```

    Which can be used to generate a zod schema:
    ```ts
    const AMRRDelinkSchema = z.object({
        tool_name: z.literal("amrr"),
        tool_action: z.literal("delink"),
        target_instance_id: z.coerce.number().describe("TARGET INSTANCE NUMBER"),
        parent_instance_id: z.coerce.number().describe("PARENT INSTANCE NUMBER (Mandatory)"),
    });
    ```
    """

    from api.v2.models.workflows.macd import register_schema

    content = register_schema.json()
    return Response(content=content, media_type="application/json")


@router.get(
    "/submissions/{dc_engagement_id}", response_model=list[MacdHeaderResponseRow]
)
async def get_macd_submissions(
    dc_engagement_id: int,
    engine: GetEngineDep,
):
    """
    Retrieves the MACD submissions for a given dc_engagement_id.
    """

    from api.v2.queries.workflows.macd import make_macd_hdr_query

    stmt = make_macd_hdr_query(dc_engagement_id=dc_engagement_id)

    with engine.begin() as conn:
        result = conn.execute(stmt)
        rows = result.mappings().all()

    return rows


@router.post("")
async def post_macd_submission(
    payload: Annotated[Json[MacdSubmissionPayload], Form()],
    user: GetUserDep,
    engine: GetEngineDep,
    data: Annotated[UploadFile, Form()],
    s3_client: S3ClientDep,
    background_tasks: BackgroundTasks,
    settings: GetSettingsDep,
    tracker: MACDUploadsTracker,
    historical_tracker: MACDHistoricalUploadsTracker,
) -> V2GenericJobResponse:
    """
    Submits a MACD submission for a given tool_name and tool_action.
    """

    _data_content = await data.read()
    # noinspection PyTypeChecker
    session_local = sessionmaker(bind=engine, class_=Session)
    with session_local() as session:
        request_id = tracker.get_next_request_id(db_session=session)
        notification_id = tracker.get_next_notification_id(db_session=session)

    from api.v2 import process_macd_upload

    background_tasks.add_task(
        process_macd_upload,
        payload=payload,
        file_content=_data_content,
        engine=engine,
        s3_client=s3_client,
        tracker=macd_historical_uploads_tracker
        if payload.tool_name == "historical"
        else macd_uploads_tracker,
        request_id=request_id,
        notification_id=notification_id,
        user={
            "cisco_cco_id": user.cisco_cco_id,
            "dc_user_id": user.user_id,
        },
        settings=settings,
    )

    return V2GenericJobResponse(
        request_id=request_id,
        notification_id=notification_id,
        message="MACD submission is being processed",
        external_job_id=None,
        external_run_id=None,
        success=True,
    )


@router.post("/audit", tags=["PrefectV3", "File Upload"])
async def post_macd_audit(
    payload: Annotated[Json[MacdAuditPayload], Form()],
    user: GetUserDep,
    flow_service: FlowV3ServiceDep,
    tracker: MACDAuditTracker,
    data: Annotated[UploadFile | None, Form()] = None,
):
    """
    This is passed to a Prefect Flow

    If `payload.schema_type` is 'skip', _data_content will be ignored
    """
    if data is None:
        _data_content = None
    else:
        _data_content = await data.read()

    with flow_service as service:
        return service.create_macd_audit_flow(
            dc_engagement_id=payload.dc_engagement_id,
            payload=payload,
            data=_data_content,
            requestor=user,
            tracker=tracker,
        )
