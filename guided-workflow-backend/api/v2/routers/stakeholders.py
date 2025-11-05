from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from starlette.status import HTTP_404_NOT_FOUND

from api.dependencies import GetSessionDep, UserRequest
from api.v2.models import V2StakeholderRead, V2StakeholderUpdate, V2StakeholderWrite
from api.v2.orm import V2Engagement, V2Stakeholder
from api.v2.queries import GET_logged_user, query_users_engagements

router = APIRouter()


@router.get("/{dc_engagement_id}", response_model=list[V2StakeholderRead])
async def get_engagement_stakeholders(
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    logged_user = GET_logged_user(req, logged_user)
    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    engagement_stakeholders_query = (
        select(V2Stakeholder)
        .where(V2Stakeholder.dc_engagement_id == dc_engagement_id)
        .where(V2Stakeholder.is_deleted == "F")
    )

    db_stakeholders = session.exec(engagement_stakeholders_query).all()

    return [V2StakeholderRead.from_orm(row) for row in db_stakeholders]


@router.post("/{dc_engagement_id}", response_model=V2StakeholderRead)
async def create_engagement_stakeholder(
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    stakeholder: V2StakeholderWrite,
    logged_user: Optional[str] = None,
):
    logged_user = GET_logged_user(req, logged_user)
    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    stakeholder.dc_engagement_id = dc_engagement_id
    db_stakeholder = V2Stakeholder.create_from_model(stakeholder, logged_user, session)
    return V2StakeholderRead.from_orm(db_stakeholder)


@router.patch("/{dc_engagement_id}/{stakeholder_id}", response_model=V2StakeholderRead)
async def update_engagement_stakeholder(
    dc_engagement_id: int,
    stakeholder_id: int,
    req: UserRequest,
    session: GetSessionDep,
    stakeholder: V2StakeholderUpdate,
    logged_user: Optional[str] = None,
):
    """Update a stakeholder"""
    logged_user = GET_logged_user(req, logged_user)
    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    stakeholder_query = (
        select(V2Stakeholder)
        .where(V2Stakeholder.dc_engagement_id == dc_engagement_id)
        .where(V2Stakeholder.stakeholder_id == stakeholder_id)
        .where(V2Stakeholder.is_deleted == "F")
        .where(V2Stakeholder.dc_engagement_id == user_engagement.dc_engagement_id)
    )

    db_stakeholder = session.exec(stakeholder_query).one_or_none()
    if not db_stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    db_stakeholder.update_from_model(stakeholder, logged_user, session)

    return V2StakeholderRead.from_orm(db_stakeholder)


@router.delete("/{dc_engagement_id}/{stakeholder_id}", response_model=V2StakeholderRead)
async def delete_engagement_stakeholder(
    dc_engagement_id: int,
    stakeholder_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    """Soft delete stakeholder"""
    logged_user = GET_logged_user(req, logged_user)
    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    stakeholder_query = (
        select(V2Stakeholder)
        .where(V2Stakeholder.dc_engagement_id == dc_engagement_id)
        .where(V2Stakeholder.stakeholder_id == stakeholder_id)
        .where(V2Stakeholder.is_deleted == "F")
        .where(V2Stakeholder.dc_engagement_id == user_engagement.dc_engagement_id)
    )

    db_stakeholder = session.exec(stakeholder_query).one_or_none()

    if not db_stakeholder:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Stakeholder not found"
        )

    db_stakeholder.soft_delete(logged_user, session)
    return V2StakeholderRead.from_orm(db_stakeholder)
