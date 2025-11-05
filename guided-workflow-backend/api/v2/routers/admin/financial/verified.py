import logging
from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import distinct, func, literal, text, union_all
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import joinedload, with_expression
from sqlmodel import select

from api.dependencies import GetSessionDep, GetUserDep, UserRequest
from api.v2.models.contracts import (
    V2VerifiedBookingAllocationModify,
    V2VerifiedBookingAssignmentModify,
    V2VerifiedBookingDcTypesModify,
    V2VerifiedBookingResponse,
)
from api.v2.orm import (
    V2BookingContractsFinancialAdmin,
    V2BookingContractsLineage,
    V2BuyingPrograms,
    V2PricingModel,
    V2ServicePlans,
    V2Theater,
)
from api.v2.queries import GET_logged_user

if TYPE_CHECKING:
    from sqlmodel.sql.expression import SelectOfScalar

router = APIRouter()
logger = logging.getLogger("api")


def get_booking_contracts_query(
    booking_contract: Optional[int],
) -> "SelectOfScalar[V2BookingContractsFinancialAdmin]":
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

    query = (
        select(V2BookingContractsFinancialAdmin)
        .where(V2BookingContractsFinancialAdmin.is_verified == True)
        .where(V2BookingContractsFinancialAdmin.is_deleted == "F")
    )

    if booking_contract:
        query = query.where(
            V2BookingContractsFinancialAdmin.booking_contract == booking_contract
        )

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

    return query


# noinspection PyTypeChecker
def get_valid_dc_types_query(
    booked_theater_id: Optional[int],
    sold_as_service_type_id: Optional[int],
    sold_as_pricing_type_id: Optional[int],
    buying_program_type_id: Optional[int],
):
    # noinspection PydanticTypeChecker
    query_theater = (
        select(
            V2Theater.theater_id.label("id"), literal("booked_theater_id").label("type")
        )
        .where(V2Theater.theater_id == booked_theater_id)
        .where(V2Theater.is_deleted == "F")
        .select_from(V2Theater)
    )
    # noinspection PydanticTypeChecker
    query_service = (
        select(
            V2ServicePlans.service_type_id.label("id"),
            literal("sold_as_service_type_id").label("type"),
        )
        .where(V2ServicePlans.service_type_id == sold_as_service_type_id)
        .where(V2ServicePlans.is_deleted == "F")
        .select_from(V2ServicePlans)
    )
    # noinspection PydanticTypeChecker
    query_pricing = (
        select(
            V2PricingModel.pricing_type_id.label("id"),
            literal("sold_as_pricing_type_id").label("type"),
        )
        .where(V2PricingModel.pricing_type_id == sold_as_pricing_type_id)
        .where(V2PricingModel.is_deleted == "F")
        .select_from(V2PricingModel)
    )
    # noinspection PydanticTypeChecker
    query_buying = (
        select(
            V2BuyingPrograms.buying_program_type_id.label("id"),
            literal("buying_program_type_id").label("type"),
        )
        .where(V2BuyingPrograms.buying_program_type_id == buying_program_type_id)
        .where(V2BuyingPrograms.is_deleted == "F")
        .select_from(V2BuyingPrograms)
    )

    queries = []
    if booked_theater_id:
        queries.append(query_theater)
    if sold_as_service_type_id:
        queries.append(query_service)
    if sold_as_pricing_type_id:
        queries.append(query_pricing)
    if buying_program_type_id:
        queries.append(query_buying)

    return union_all(*queries)


@router.get("", response_model=list[V2VerifiedBookingResponse])
def get_verified_bookings(
    session: GetSessionDep,
):
    """
    Get all verified bookings
    """

    query = get_booking_contracts_query(booking_contract=None).options(
        joinedload(V2BookingContractsFinancialAdmin.assignments)
    )

    db_verified_bookings = session.exec(query).unique().all()
    return db_verified_bookings


@router.get("/{booking_contract}", response_model=V2VerifiedBookingResponse)
def get_verified_booking(session: GetSessionDep, booking_contract: int):
    """
    Get a verified booking by booking_contract
    """
    query = get_booking_contracts_query(booking_contract=booking_contract).options(
        joinedload(V2BookingContractsFinancialAdmin.assignments)
    )
    try:
        db_verified_booking = session.exec(query).one()
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail="Booking not found") from e
    return db_verified_booking


@router.patch(
    "/{booking_contract}/calculated", response_model=V2VerifiedBookingResponse
)
def update_verified_booking_calculated(
    session: GetSessionDep,
    booking_contract: int,
    booking: V2VerifiedBookingAllocationModify,
    request: UserRequest,
    logged_user: Optional[str] = None,
):
    """
    Update the calculated allocations for a verified booking
    """
    logged_user = GET_logged_user(request, logged_user)
    query = (
        select(V2BookingContractsFinancialAdmin)
        .where(V2BookingContractsFinancialAdmin.booking_contract == booking_contract)
        .where(V2BookingContractsFinancialAdmin.is_verified == True)
        .where(V2BookingContractsFinancialAdmin.is_deleted == "F")
    )

    db_booking = session.exec(query).one()
    db_booking.ib_calc_sw_allocation = booking.calculated_sw
    db_booking.ib_calc_hw_allocation = booking.calculated_hw
    db_booking.updated_by = logged_user
    session.add(db_booking)
    session.commit()

    query = get_booking_contracts_query(booking_contract=booking_contract).options(
        joinedload(V2BookingContractsFinancialAdmin.assignments)
    )
    db_booking = session.exec(query).unique().one()

    return db_booking


@router.patch("/{booking_contract}/dc_types", response_model=V2VerifiedBookingResponse)
def update_verified_booking_dc_types(
    session: GetSessionDep,
    booking_contract: int,
    booking: V2VerifiedBookingDcTypesModify,
    db_user: GetUserDep,
):
    """
    Update the DC Types for a verified booking
    """

    if booking_contract != booking.booking_contract:
        raise HTTPException(
            status_code=400,
            detail="booking_contract in path does not match booking_contract in body",
        )

    query = get_booking_contracts_query(booking_contract=booking_contract).options(
        joinedload(V2BookingContractsFinancialAdmin.assignments)
    )

    db_booking = session.exec(query).unique().one()

    diff = {
        k: v
        for k, v in booking.dict(
            include={
                "booked_theater_id",
                "sold_as_service_type_id",
                "sold_as_pricing_type_id",
                "buying_program_type_id",
            }
        ).items()
        if getattr(db_booking, k) != v
    }
    if not diff:
        return db_booking

    # Query the dc_types table to ensure the values are valid
    query_dc_types = get_valid_dc_types_query(
        booked_theater_id=diff.get("booked_theater_id"),
        sold_as_service_type_id=diff.get("sold_as_service_type_id"),
        sold_as_pricing_type_id=diff.get("sold_as_pricing_type_id"),
        buying_program_type_id=diff.get("buying_program_type_id"),
    )

    valid_types = session.exec(query_dc_types).all()
    for k, v in diff.items():
        if not any((v == vt.id and k == vt.type for vt in valid_types)):
            raise HTTPException(
                status_code=400, detail=f"{v} is not a valid type of {k}"
            )
    for k, v in diff.items():
        setattr(db_booking, k, v)
    db_booking.updated_by = db_user.cisco_cco_id
    session.add(db_booking)
    session.commit()

    db_booking = session.exec(query).unique().one()

    return db_booking


@router.patch(
    "/{booking_contract}/assignments",
)
def update_verified_booking_assignments(
    session: GetSessionDep,
    booking_contract: int,
    booking: V2VerifiedBookingAssignmentModify,
    request: UserRequest,
    logged_user: Optional[str] = None,
) -> V2VerifiedBookingResponse:
    """
    Update the assignments for a verified booking
    """
    logged_user = GET_logged_user(request, logged_user)

    # Ensure sub_allocation_* fields validate
    sw_total = sum((assignment.sub_allocation_sw for assignment in booking.assignments))
    if sw_total != 1:
        raise HTTPException(
            status_code=400, detail="Sub-allocations must sum to 1 for SW"
        )
    hw_total = sum((assignment.sub_allocation_hw for assignment in booking.assignments))
    if hw_total != 1:
        raise HTTPException(
            status_code=400, detail="Sub-allocations must sum to 1 for HW"
        )

    query_booking = get_booking_contracts_query(
        booking_contract=booking_contract
    ).options(joinedload(V2BookingContractsFinancialAdmin.assignments))

    try:
        db_booking = session.exec(query_booking).unique().one()
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail="Booking not found") from e
    except MultipleResultsFound as e:
        raise HTTPException(status_code=500, detail="Multiple bookings found") from e

    stmt = text(
        """
        CALL IDENTIFIER(:proc_name)(:booking, :logged_user, :booking_contract)
        """
    ).bindparams(
        proc_name="assign_responsible_users",
        booking=booking.json(),
        logged_user=logged_user,
        booking_contract=booking_contract,
    )

    with session as sp_session:
        try:
            sp_session.execute(stmt).scalar()
            sp_session.commit()
        except Exception as e:
            logger.exception("Error running stored procedure")
            sp_session.rollback()
            raise HTTPException(
                status_code=500, detail="Error running stored procedure"
            ) from e

    query = get_booking_contracts_query(booking_contract=booking_contract).options(
        joinedload(V2BookingContractsFinancialAdmin.assignments)
    )
    db_booking = session.exec(query).unique().one()
    return db_booking
