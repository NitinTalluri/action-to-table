import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path
from sqlalchemy import select
from starlette.status import HTTP_400_BAD_REQUEST

from api.dependencies import (
    FlowV3ServiceDep,
    GetSessionDep,
    GetUserDep,
    ManagerBookingsServiceTypesDep,
)
from api.v2.models.contracts import V2VerifiedBookingAssignmentModify
from api.v2.models.manager import V2GetSDPForBooking, V2RebuildSDPForBookingPayload
from api.v2.orm import V2User
from api.v2.queries.manager import query_manager_sdp
from api.v2.routers.engagements import ShareCanvasTracker
from api.v2.services import EngagementsService
from api.v2.services.manager_bookings import (
    ManagerBookingsService,
    ServiceException,
)

router = APIRouter()
logger = logging.getLogger("api")


@router.get("/{booking_contract}", response_model=list[V2GetSDPForBooking])
def get_sdp_for_booking(
    booking_contract: Annotated[int, Path(title="Booking Contract")],
    session: "GetSessionDep",
):
    """
    Get a list of all SDP subtasks appropriate for a given booking_contract.
    Include a list of all responsible users that already have subtasks scheduled
    """

    query_bookings = query_manager_sdp(booking_contract=booking_contract)
    bookings_result = session.exec(query_bookings).all()
    return bookings_result


@router.post(
    "/{booking_contract}", tags=["PrefectV3"], response_model=list[V2GetSDPForBooking]
)
def rebuild_sdp_for_booking(
    booking_contract: Annotated[int, Path(title="Booking Contract")],
    payload: V2RebuildSDPForBookingPayload,
    db_user: GetUserDep,
    session: "GetSessionDep",
    tracker: ShareCanvasTracker,
    flow_service: FlowV3ServiceDep,
    booking_types: "ManagerBookingsServiceTypesDep",
):
    """
    Put booking assignment and then rebuild SDP for a given booking_contract and a list of sub_tasks.
    This is used only for Scale bookings which have specific SDP subtasks added manually from the UI.
    """

    if booking_contract != payload.booking_contract:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Booking contract in URL does not match booking contract in payload",
        )

    try:
        payload_allocations = V2VerifiedBookingAssignmentModify(
            booking_contract=booking_contract, assignments=payload.assignments
        )
    except ValueError as e:
        logger.exception("Invalid payload for booking assignment")
        raise ServiceException(
            msg="Invalid payload for booking assignment", code=HTTP_400_BAD_REQUEST
        ) from e

    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=True
    ) as service:
        try:
            newly_shared_users = service.set_booking_allocations(
                booking_contract=booking_contract,
                payload=payload_allocations,
                requestor=db_user,
            )
            service.rebuild_sdp_for_booking_contract(
                booking_contract=booking_contract, sub_task_ids=payload.sub_task_ids
            )

        except ServiceException as e:
            session.rollback()
            raise HTTPException(status_code=e.code, detail=e.msg) from e

    if not newly_shared_users:
        return session.exec(query_manager_sdp(booking_contract=booking_contract)).all()

    user_emails = session.exec(
        select(V2User.user_id, V2User.cisco_cco_id).where(
            V2User.user_id.in_([item.dc_user_id for item in newly_shared_users])
        )
    ).all()

    id2email = {row.user_id: row.cisco_cco_id for row in user_emails}

    for item in newly_shared_users:
        shared_user_id = item.dc_user_id
        target_engagement = item.dc_engagement_id
        user_email = id2email[shared_user_id]
        if not user_email:
            msg = f"User {shared_user_id} has no cisco_cco_id - skipping"
            logger.error(msg)
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

    return session.exec(query_manager_sdp(booking_contract=booking_contract)).all()
