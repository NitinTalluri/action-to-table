from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, update

from api.dependencies import GetSessionDep, GetSettingsDep, GetUserDep, GroupGetterDep
from api.v2.models import (
    SupportCaseAgentModel,
    SupportCaseAgentUpdatePayload,
    V2SupportStatus,
    V2UserModel,
    V2UserModelAgentView,
)
from api.v2.orm import V2User
from api.v2.queries import query_agent_cases, query_available_users

router = APIRouter()


@router.get("", response_model=list[SupportCaseAgentModel])
def get_cases(
    session: GetSessionDep,
    status: Annotated[
        Optional[list[V2SupportStatus]],
        Query(title="status", description="Filter cases by status"),
    ] = None,
    assigned_cisco_cco_id: Annotated[
        Optional[str],
        Query(
            title="assigned_to_cisco_cco_id",
            description="Filter cases assigned to a specific user's cisco cco id",
        ),
    ] = None,
    assigned_user_id: Annotated[
        Optional[int],
        Query(
            title="assigned_to_user_id",
            description="Filter cases assigned to a specific user's user id",
        ),
    ] = None,
    cisco_cco_id: Annotated[
        Optional[str],
        Query(
            title="cisco_cco_id",
            description="Filter cases by submitting user's cisco cco id",
        ),
    ] = None,
    user_id: Annotated[
        Optional[int],
        Query(title="user_id", description="Filter cases by submitting user's user id"),
    ] = None,
):
    query = query_agent_cases(
        statuses=status,
        assigned_cisco_cco_id=assigned_cisco_cco_id,
        assigned_user_id=assigned_user_id,
        user_id=user_id,
        user_cisco_cco_id=cisco_cco_id,
    )

    query = query.order_by(desc("create_dtm"))

    return session.exec(query).all()


@router.get("/available_agents", response_model=list[V2UserModelAgentView])
def get_available_agents(
    session: GetSessionDep,
    group_getter: GroupGetterDep,
):
    # The members of the cognito group "dc_support" are the agents. This needs to be cross-referenced with the
    # users table to get the user details.
    cisco_cco_ids = group_getter("dc_support", "dc_admin")

    query = query_available_users().where(V2User.cisco_cco_id.in_(cisco_cco_ids))

    result = session.exec(query).all()

    return result


@router.get("/{case_id}", response_model=SupportCaseAgentModel)
def get_case(case_id: int, session: GetSessionDep):
    query = query_agent_cases(case_id=case_id)
    result = session.exec(query).one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return result


@router.put("/{case_id}", response_model=SupportCaseAgentModel)
def update_case(
    case_id: int,
    payload: SupportCaseAgentUpdatePayload,
    session: GetSessionDep,
    db_user: GetUserDep,
    settings: GetSettingsDep,
):
    from api.v2.orm import SupportCase

    query = query_agent_cases(case_id=case_id)
    result = session.exec(query).one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    payload_values = payload.dict(
        exclude_unset=True, exclude_defaults=True, exclude={"is_resolved"}
    )

    updated_values = {
        **{k: v for k, v in payload_values.items() if v is not None},
        "update_dtm": settings.get_db_datetime_now(),
        "updated_by": db_user.cisco_cco_id,
    }
    if payload.is_resolved is not None:
        updated_values["resolved_dtm"] = (
            settings.get_db_datetime_now() if payload.is_resolved else None
        )

    stmt = (
        update(SupportCase).where(SupportCase.case_id == case_id).values(updated_values)
    )
    session.exec(stmt)
    session.commit()

    return session.exec(query).one()
