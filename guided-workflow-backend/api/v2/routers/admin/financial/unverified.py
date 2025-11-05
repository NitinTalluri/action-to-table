from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import distinct, func
from sqlalchemy.orm import with_expression
from sqlmodel import select

from api.dependencies import GetSessionDep, GetSettingsDep, UserRequest
from api.v2.models import (
    V2BookingId,
    V2UnverifiedBookingResponse,
    V2VerifyBooking,
)
from api.v2.orm import V2BookingContractsFinancialAdmin
from api.v2.queries.utils import GET_logged_user

router = APIRouter()


@router.get("")
def get_unverified_bookings(
    session: GetSessionDep,
) -> list[V2UnverifiedBookingResponse]:
    query = (
        select(V2BookingContractsFinancialAdmin)
        .where(V2BookingContractsFinancialAdmin.is_verified == False)
        .where(V2BookingContractsFinancialAdmin.is_deleted == "F")
        .order_by(V2BookingContractsFinancialAdmin.booking_contract)
    )

    from api.v2.orm import V2BookingContractsLineage

    # noinspection PyTypeChecker,PydanticTypeChecker
    renewal_cte = select(
        distinct(V2BookingContractsLineage.child_booking_contract).label(
            "booking_contract"
        ),
        func.iff(
            func.array_size(V2BookingContractsLineage.parent_booking_contract) > 0,
            True,
            False,
        ).label("is_renewal"),
    ).cte()

    query = query.outerjoin(
        renewal_cte,
        V2BookingContractsFinancialAdmin.booking_contract
        == renewal_cte.c.booking_contract,
    ).options(
        with_expression(
            V2BookingContractsFinancialAdmin.is_renewal,
            func.nvl(renewal_cte.c.is_renewal, False),
        )
    )

    db_bookings = session.exec(query).all()
    return db_bookings


@router.post("")
def verify_booking(
    req: UserRequest,
    session: GetSessionDep,
    booking: V2VerifyBooking,
    settings: GetSettingsDep,
    logged_user: Optional[str] = None,
) -> V2BookingId:
    """
    User submits a booking for verification. Reply with the booking_id if it was successfully verified
    """
    logged_user = GET_logged_user(req, logged_user)
    query = (
        select(V2BookingContractsFinancialAdmin)
        .where(
            V2BookingContractsFinancialAdmin.booking_contract
            == booking.booking_contract
        )
        .where(V2BookingContractsFinancialAdmin.is_deleted == "F")
    )
    db_booking = session.exec(query).one()
    if db_booking.is_verified:
        raise HTTPException(status_code=400, detail="Booking already verified")

    db_booking.sold_as_service_type_id = booking.sold_as_service_type_id
    db_booking.booked_theater_id = booking.booked_theater_id
    db_booking.sold_as_pricing_type_id = booking.sold_as_pricing_type_id
    db_booking.buying_program_type_id = booking.buying_program_type_id
    db_booking.sold_as_sw_allocation = booking.booked_sw
    db_booking.sold_as_hw_allocation = booking.booked_hw
    db_booking.updated_by = logged_user
    db_booking.update_dtm = (
        datetime.now().astimezone(settings.db_timezone).replace(tzinfo=None)
    )

    session.add(db_booking)
    session.commit()
    return V2BookingId(booking_contract=db_booking.booking_contract)
