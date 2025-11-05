import logging

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from api.dependencies import (
    FlowV3ServiceDep,
    GetSessionDep,
    GetUserDep,
    ManagerBookingsServiceTypesDep,
)
from api.v2.models import (
    V2ClaimedBookingContractsModel,
    V2ReplaceResponsibleUser,
    V2VerifiedBookingAssignmentModify,
)
from api.v2.orm import V2User
from api.v2.queries.manager.bookings import query_claimed_booking
from api.v2.routers.engagements import ShareCanvasTracker
from api.v2.services import EngagementsService, ManagerBookingsService, ServiceException

logger = logging.getLogger("api")

router = APIRouter()


@router.post(
    "/replace", tags=["PrefectV3"], response_model=V2ClaimedBookingContractsModel
)
def replace_responsible_user(
    payload: V2ReplaceResponsibleUser,
    db_user: GetUserDep,
    session: GetSessionDep,
    flow_service: FlowV3ServiceDep,
    tracker: ShareCanvasTracker,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """
    Replace a responsible user, maintaining their association but with zero allocations
    """

    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            is_new_share = service.replace_assignment_responsible_user(
                booking_contract=payload.booking_contract,
                prev_user_id=payload.prev_user_id,
                new_user_id=payload.new_user_id,
                requestor=db_user,
            )
            session.commit()
        except ServiceException as e:
            session.rollback()
            raise HTTPException(status_code=e.code, detail=e.msg) from e

    if not is_new_share:
        result = session.exec(query_claimed_booking(payload.booking_contract)).one()
        return result

    new_user_email = session.exec(
        select(V2User.cisco_cco_id).where(
            V2User.user_id == payload.new_user_id, V2User.is_deleted == "F"
        )
    ).one()
    with EngagementsService(session) as service:
        try:
            service.share_engagement_as_manager(
                requestor=db_user,
                target_user_cisco_cco_id=new_user_email,
                dc_engagement_id=payload.booking_contract,
                tracker=tracker,
                flow_service=flow_service,
            )
            session.commit()
        except ServiceException as e:
            session.rollback()
            raise HTTPException(status_code=e.code, detail=e.msg) from e

    return session.exec(query_claimed_booking(payload.booking_contract)).one()


@router.put("", response_model=V2ClaimedBookingContractsModel, tags=["PrefectV3"])
def put_booking_assignments(
    payload: V2VerifiedBookingAssignmentModify,
    db_user: GetUserDep,
    session: GetSessionDep,
    flow_service: FlowV3ServiceDep,
    tracker: ShareCanvasTracker,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """
    Set the allocations for a booking
    """

    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            newly_shared_users = service.set_booking_allocations(
                booking_contract=payload.booking_contract,
                payload=payload,
                requestor=db_user,
            )
            session.commit()
        except ServiceException as e:
            session.rollback()
            raise HTTPException(status_code=e.code, detail=e.msg) from e

    if not newly_shared_users:
        result = session.exec(query_claimed_booking(payload.booking_contract)).one()
        return result

    user_emails = session.exec(
        select(V2User.user_id, V2User.cisco_cco_id).where(
            V2User.user_id.in_([user_id for user_id, _ in newly_shared_users])
        )
    ).all()

    id2email = {row.user_id: row.cisco_cco_id for row in user_emails}

    for shared_user_id, target_engagement in newly_shared_users:
        user_email = id2email[shared_user_id]
        if not user_email:
            logger.error("User %s has no cisco_cco_id - skipping", shared_user_id)
            continue
        with EngagementsService(session) as service:
            try:
                service.share_engagement_as_manager(
                    requestor=db_user,
                    target_user_cisco_cco_id=id2email[shared_user_id],
                    dc_engagement_id=target_engagement,
                    tracker=tracker,
                    flow_service=flow_service,
                )
                session.commit()
            except ServiceException as e:
                session.rollback()
                raise HTTPException(status_code=e.code, detail=e.msg) from e

    return session.exec(query_claimed_booking(payload.booking_contract)).one()
