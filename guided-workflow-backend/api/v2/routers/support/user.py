from fastapi import APIRouter, HTTPException
from sqlmodel import select

from api.dependencies import GetSessionDep, GetSettingsDep, GetUserDep
from api.v2.models import (
    SupportCaseCreatePayload,
    SupportCaseModel,
    SupportCaseUserClosedPayload,
)
from api.v2.orm import SupportCase

router = APIRouter()


@router.post("", response_model=SupportCaseModel)
def create_support_case(
    payload: SupportCaseCreatePayload, db_user: GetUserDep, session: GetSessionDep
):
    """
    Create a new support case
    """

    data = dict(
        **payload.dict(),
        user_id=db_user.user_id,
        created_by=db_user.cisco_cco_id,
        status="new",
    )

    db_case = SupportCase(**data)
    session.add(db_case)
    session.commit()
    session.refresh(db_case)
    return db_case


@router.get("", response_model=list[SupportCaseModel])
def get_user_support_cases(session: GetSessionDep, db_user: GetUserDep):
    """
    Get all support cases associated with the current user
    """

    query = (
        select(SupportCase)
        .where(SupportCase.user_id == db_user.user_id)
        .where(SupportCase.is_deleted == "F")
    )

    return session.exec(query).all()


@router.post("/{case_id}/close", response_model=SupportCaseModel)
def close_user_support_case(
    case_id: int,
    payload: SupportCaseUserClosedPayload,
    db_user: GetUserDep,
    session: GetSessionDep,
    settings: GetSettingsDep,
):
    """
    Close a support case from the user's perspective
    """

    query = (
        select(SupportCase)
        .where(SupportCase.case_id == case_id)
        .where(SupportCase.user_id == db_user.user_id)
        .where(SupportCase.is_deleted == "F")
        .where(~SupportCase.is_closed)
    )
    db_case = session.exec(query).one_or_none()

    if not db_case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    if payload.comments:
        db_case.comments = payload.comments
    db_case.resolved_dtm = settings.get_db_datetime_now()
    session.commit()
    session.refresh(db_case)
    return db_case
