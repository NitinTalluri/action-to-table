from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from snowflake.sqlalchemy import MergeInto
from sqlalchemy import Integer, String, column, func, values
from sqlmodel import select
from starlette.status import HTTP_400_BAD_REQUEST

from api.dependencies import (
    GetSessionDep,
    GetUserDep,
    ManagerBookingsServiceTypesDep,
    is_manager_or_pool_manager,
)
from api.v2.models import (
    V2BulkSalesLevelAssignment,
    V2BulkSalesLevelAssignmentResponse,
    V2ClaimedBookingContractsModel,
    V2EngagementRead,
    V2ModifyBookingDefaultEngagement,
)
from api.v2.orm import V2Engagement
from api.v2.orm.bookings import V2BookingContracts, V2SalesLevel
from api.v2.queries import QueryMembership
from api.v2.queries.manager.bookings import (
    query_claimed_booking,
    query_claimed_bookings,
)
from api.v2.queries.manager.bookings_sales_level import bulk_assign_sales_levels
from api.v2.services import ManagerBookingsService, ServiceException

router = APIRouter(dependencies=[Depends(is_manager_or_pool_manager)])


@router.get("/claimed", response_model=list[V2ClaimedBookingContractsModel])
def get_claimed_bookings(
    db_user: GetUserDep,
    session: GetSessionDep,
):
    """
    Get a list of claimed bookings that the manager has claimed either implicitly or explicitly

    Parameters
    ----------
    """

    query_bookings = query_claimed_bookings(db_user.user_id)
    bookings_result = session.exec(query_bookings).all()
    return bookings_result


@router.patch(
    "/claimed/{booking_contract}",
    response_model=V2ClaimedBookingContractsModel,
)
def update_booking_defaults(
    booking_contract: Annotated[int, Path(title="Booking Contract ID")],
    payload: V2ModifyBookingDefaultEngagement,
    db_user: GetUserDep,
    session: GetSessionDep,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """Modify a claimed booking's defaults. Currently, this only allows changing the DC Engagement ID default."""

    if booking_contract != payload.booking_contract:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Booking contract in URL does not match booking contract in payload",
        )

    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            service.update_booking_defaults(
                booking_contract=booking_contract, requestor=db_user, payload=payload
            )
        except ServiceException as e:
            session.rollback()
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()

    booking_query = query_claimed_booking(booking_contract=booking_contract)
    booking_result = session.exec(booking_query).one()
    return booking_result


@router.get("/engagements", response_model=list[V2EngagementRead])
def get_available_engagements(
    session: GetSessionDep,
):
    """
    Get a list of engagements that a manager can associate with a booking.
    We do NOT limit what is shown based on permissions.
    """

    query = (
        select(V2Engagement)
        .where(V2Engagement.is_deleted == "F")
        .where(V2Engagement.engagement_name.isnot(None))
        .where(V2Engagement.created_by.isnot(None))
    )

    result = session.exec(query).all()
    return result


@router.post("/sales_levels", response_model=V2BulkSalesLevelAssignmentResponse)
def assign_sales_levels_bulk(
    payload: V2BulkSalesLevelAssignment,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    """Bulk assign sales levels to booking contracts"""
    result = bulk_assign_sales_levels(
        session=session,
        assignments=payload.assignments,
        requestor_cco_id=db_user.cisco_cco_id,
    )
    session.commit()
    return result
