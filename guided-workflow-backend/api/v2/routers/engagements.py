import json
import logging
from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlmodel import select
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from api.dependencies import (
    FlowV3ServiceDep,
    GetSessionDep,
    GetUserDep,
    is_support,
)
from api.v2.models import (
    UiEnum,
    V2CamEngagementWrite,
    V2EngagementCreate,
    V2EngagementRead,
    V2EngagementUpdate,
    V2UserModel,
    V2UserRead,
)
from api.v2.orm import (
    V2BookingContracts,
    V2BookingToEngagementResponsibleUser,
    V2CamEngagement,
    V2Engagement,
    V2User,
)
from api.v2.queries import query_available_users, query_users_engagements_by_user_id
from api.v2.services import EngagementsService, ExternalServiceTracker, ServiceException

share_canvas_tracker = ExternalServiceTracker(
    UiEnum.canvas_actions.value, "Sharing Canvas"
)
ShareCanvasTracker = Annotated[ExternalServiceTracker, Depends(share_canvas_tracker)]


logger = logging.getLogger("api")
router = APIRouter()


@router.get("/users", response_model=list[V2UserModel])
def get_available_users_for_sharing(session: GetSessionDep):
    query = query_available_users()
    result = session.exec(query).all()
    return result


@router.get("/engagement_owners/{engagement_id}", response_model=list[V2UserRead])
def get_user_engagement_owners_v2(engagement_id: int, session: GetSessionDep):
    users = session.exec(
        select(V2User)
        .join(V2CamEngagement)
        .where(V2CamEngagement.dc_engagement_id == engagement_id)
        .where(V2User.is_deleted == "F")
        .where(V2CamEngagement.is_deleted == "F")
    ).all()
    return users


@router.get("", response_model=list[V2EngagementRead])
def get_users_engagements(db_user: GetUserDep, session: GetSessionDep):
    """Get all Engagements for a user"""
    query = query_users_engagements_by_user_id(db_user.user_id)

    result = session.exec(query).all()
    return result


@router.post("", response_model=V2EngagementRead, status_code=HTTP_201_CREATED)
def create_engagement_v2(
    data: V2EngagementCreate,
    session: GetSessionDep,
    db_user: GetUserDep,
):
    """Create a new Engagement"""
    db_existing = session.exec(
        select(V2Engagement)
        .join(V2CamEngagement)
        .join(V2User)
        .where(V2User.user_id == db_user.user_id)
        .where(V2Engagement.engagement_name == data.engagement_name)
    ).one_or_none()
    if not db_existing:  # create eng, cam2Eng and tagging table else rehydrate
        db_engagement = V2Engagement.create_from_model(
            data, db_user.cisco_cco_id, session
        )
        _cam_engagement_model = V2CamEngagementWrite(
            user_id=db_user.user_id, dc_engagement_id=db_engagement.dc_engagement_id
        )
        _db_cam_engagement = V2CamEngagement.create_from_model(
            _cam_engagement_model, db_user.cisco_cco_id, session
        )
        create_table_query = text(
            f"""
                    CREATE TABLE DC_ENGAGEMENT_TAGS_{db_engagement.dc_engagement_id} (
                        INSTANCE_ID      NUMBER NOT NULL,
                        TAGSET_ID        NUMBER NOT NULL REFERENCES DC_TAGSET,
                        TAG_ID           NUMBER NOT NULL REFERENCES DC_TAGS,
                        DC_ENGAGEMENT_ID NUMBER NOT NULL,
                        UPDATE_DTM       TIMESTAMPNTZ DEFAULT CURRENT_TIMESTAMP(),
                        UPDATE_BY        VARCHAR(250),
                        IS_DELETED       VARCHAR(100) DEFAULT 'F',
                        PRIMARY KEY (INSTANCE_ID, TAGSET_ID)
                    )
                """
        )  # Use the new engagement's ID to name the table
        session.execute(create_table_query)
        return db_engagement
    elif db_existing.is_deleted == "F":
        raise HTTPException(
            status_code=409,
            detail=f"Engagement ({db_existing.dc_engagement_id}) with name:{db_existing.engagement_name} already exists.",
        )
    else:
        db_existing.update_from_model(data, db_user.cisco_cco_id, session)
        return db_existing


@router.patch("/{dc_engagement_id}", response_model=V2EngagementRead, status_code=200)
def update_engagement_v2(
    data: V2EngagementUpdate,
    dc_engagement_id: int,
    session: GetSessionDep,
    db_user: GetUserDep,
):
    """
    Update an existing Engagement
    """
    query = query_users_engagements_by_user_id(db_user.user_id).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    result = session.exec(query).one_or_none()
    if not result:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Engagement ({dc_engagement_id}) not found",
        )

    result.update_from_model(data, db_user.cisco_cco_id, session)
    return result


@router.delete("/{dc_engagement_id}", status_code=200, response_model=V2EngagementRead)
def delete_engagement_v2(
    dc_engagement_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    """
    Delete an existing Engagement that is not linked to any booking contracts
    """

    query = query_users_engagements_by_user_id(db_user.user_id).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )
    db_engagement = session.exec(query).unique().one_or_none()
    if not db_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Engagement ({dc_engagement_id}) not found",
        )

    # Check for linked booking contracts
    query = (
        select(
            V2BookingToEngagementResponsibleUser.booking_contract,
        )
        .outerjoin(
            V2BookingContracts,
            V2BookingToEngagementResponsibleUser.booking_contract
            == V2BookingContracts.booking_contract & V2BookingContracts.is_deleted
            == "F",
        )
        .where(
            (V2BookingToEngagementResponsibleUser.dc_engagement_id == dc_engagement_id)
            & (V2BookingToEngagementResponsibleUser.is_deleted == "F")
        )
    )

    linked_contracts = session.exec(query).all()
    if linked_contracts:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=f"Engagement ({dc_engagement_id}) cannot be deleted."
            f" It is linked to booking contracts: {', '.join(map(str, set(linked_contracts)))}",
        )

    db_engagement.soft_delete(db_user.cisco_cco_id, session)

    return db_engagement


@router.post("/{engagement_id}/share/{cco_id}", tags=["PrefectV3"])
def create_user_to_engagement_link(
    engagement_id: int,
    cco_id: str,
    db_user: GetUserDep,
    session: GetSessionDep,
    tracker: ShareCanvasTracker,
    flow_service: FlowV3ServiceDep,
):
    with EngagementsService(session) as service:
        try:
            service.share_engagement(
                requestor=db_user,
                target_user_cisco_cco_id=cco_id,
                dc_engagement_id=engagement_id,
                tracker=tracker,
                flow_service=flow_service,
            )
            session.commit()
        except ServiceException as e:
            logger.exception(e)
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e


@router.delete("/{engagement_id}/share/{cco_id}")
def delete_user_link(
    engagement_id: int,
    cco_id: str,
    session: GetSessionDep,
    db_user: GetUserDep,
):
    with EngagementsService(session) as service:
        try:
            service.unshare_engagement(
                requestor=db_user,
                target_user_cisco_cco_id=cco_id,
                dc_engagement_id=engagement_id,
            )
            session.commit()
        except ServiceException as e:
            logger.exception(e)
            session.rollback()
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e


@router.get("/deleted", response_model=None, dependencies=[Depends(is_support)])
async def get_deleted_engagements(
    session: GetSessionDep,
):
    stmt = text(
        """
        with canvas as (
                 SELECT c.DC_ENGAGEMENT_ID,c.ENGAGEMENT_NAME, c.NOTES, c.UPDATE_DTM, c.UPDATED_BY
                    FROM DC_ENGAGEMENT_HDR c
                    WHERE c.IS_DELETED = 'T'
                    ORDER BY c.UPDATE_DTM DESC
            )
            select TO_JSON(
                OBJECT_CONSTRUCT_KEEP_NULL(
                            'dc_engagement_id',                c.DC_ENGAGEMENT_ID,
                            'engagement_name',                 c.ENGAGEMENT_NAME,
                            'engagement_notes',                c.NOTES,
                            'update_dtm',                      NVL(c.UPDATE_DTM, CURRENT_TIMESTAMP()),
                            'updated_by',                      NVL(c.UPDATED_BY, 'Unknown')
                        )
                    )
                           from canvas c
                   """
    )
    result = session.exec(stmt).scalars().all()
    if not result:
        return []
    return [json.loads(r) for r in result]


@router.put(
    "/{dc_engagement_id}",
    response_model=V2EngagementRead,
    status_code=200,
    dependencies=[Depends(is_support)],
)
async def undelete_engagement_v2(
    dc_engagement_id: int,
    session: GetSessionDep,
    db_user: GetUserDep,
):
    stmt = select(V2Engagement).where(V2Engagement.dc_engagement_id == dc_engagement_id)
    db_engagement = session.exec(stmt).one_or_none()

    if not db_engagement:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No Such Engagement",
        )

    db_engagement.is_deleted = "F"
    db_engagement.updated_by = db_user.cisco_cco_id
    session.add(db_engagement)
    session.commit()
    session.refresh(db_engagement)
    return db_engagement
