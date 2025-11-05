import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from toolz import groupby

from api.dependencies import FlowV3ServiceDep, GetSessionDep, GetUserDep
from api.v2.models import UiEnum, V2ThoughtSpotTaskListWrite
from api.v2.queries import (
    get_thoughtspot_tasks_engagement,
)
from api.v2.services import ExternalServiceTracker

router = APIRouter()
logger = logging.getLogger("api")

# Create tracker for thoughtspot tagging
ts_tagging_tracker = ExternalServiceTracker(
    UiEnum.instance_tagging, "ThoughtSpot Tagging"
)
TsTaggingTracker = Annotated[ExternalServiceTracker, Depends(ts_tagging_tracker)]


@router.post("", tags=["PrefectV3"])
def tagging_task_runner(
    payload: V2ThoughtSpotTaskListWrite,
    db_user: GetUserDep,
    session: GetSessionDep,
    flow_service: FlowV3ServiceDep,
    tracker: TsTaggingTracker,
):
    """
    Run several tagging tasks grouped by dc_engagement_id using Prefect v3 flows.
    For each unique dc_engagement_id, creates a separate flow that operates on
    the dc_engagement_id and the associated thoughtspot_ids.
    """
    thoughtspot_ids = {r.thoughtspot_id for r in payload.requests}
    config_strategy = payload.requests[0].config_strategy

    db_tasks = get_thoughtspot_tasks_engagement(
        thoughtspot_ids=thoughtspot_ids,
        user_id=db_user.user_id,
        session=session,
    )

    if not db_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"No tasks found for thoughtspot_ids={thoughtspot_ids}",
        )

    # Check for missing thoughtspot_ids
    found_ids = {task["thoughtspot_id"] for task in db_tasks}
    missing_ids = thoughtspot_ids - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=404, detail=f"Tasks not found for thoughtspot_ids={missing_ids}"
        )

    tasks_by_engagement = groupby(lambda t: t["dc_engagement_id"], db_tasks)

    created_flows = []

    with flow_service as service:
        for dc_engagement_id, engagement_tasks in tasks_by_engagement.items():
            engagement_thoughtspot_ids = [
                task["thoughtspot_id"] for task in engagement_tasks
            ]
            try:
                response = service.create_thoughtspot_tagging_flow(
                    thoughtspot_ids=engagement_thoughtspot_ids,
                    config_strategy=config_strategy,
                    requestor=db_user,
                    tracker=tracker,
                    dc_engagement_id=dc_engagement_id,
                )
                created_flows.append(
                    {
                        "dc_engagement_id": dc_engagement_id,
                        "thoughtspot_ids": engagement_thoughtspot_ids,
                        "response": response,
                    }
                )
            except Exception as e:
                logger.exception(
                    "Failed to create ThoughtSpot tagging flow for dc_engagement_id=%s",
                    dc_engagement_id,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create tagging flow for engagement {dc_engagement_id}",
                ) from e

    return {
        "message": f"Created {len(created_flows)} ThoughtSpot tagging flows",
        "flows": created_flows,
    }, 202
