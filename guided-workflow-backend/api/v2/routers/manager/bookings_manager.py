from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from starlette.status import HTTP_400_BAD_REQUEST

from api.dependencies import (
    GetSessionDep,
    GetSettingsDep,
    GetUserDep,
    ManagerBookingsServiceTypesDep,
    is_manager,
)
from api.v2.models import (
    V2BookingContractsModel,
    V2ClaimBooking,
    V2ClaimedBookingContractsModel,
    V2DisengagementModel,
    V2DisengagementResponse,
    V2ModifyBookingAllocationRatio,
    V2ModifyBookingDcTypes,
    V2ProspectiveBookingEditPayload,
    V2ProspectiveBookingPayload,
    V2RenewableBookingResponse,
)
from api.v2.queries.manager.bookings import (
    query_available_to_renew_from,
    query_claimed_booking,
    query_unclaimed_bookings,
)
from api.v2.services import ManagerBookingsService, ServiceException

router = APIRouter(dependencies=[Depends(is_manager)])


@router.patch(
    "/claimed/{booking_contract}/dc_types",
    response_model=V2ClaimedBookingContractsModel,
)
def update_claimed_booking_dc_types(
    booking_contract: int,
    payload: V2ModifyBookingDcTypes,
    db_user: GetUserDep,
    session: GetSessionDep,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """Modify the DC types of a claimed booking"""

    if booking_contract != payload.booking_contract:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Booking contract in URL does not match booking contract in payload",
        )

    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            service.update_booking_dc_types(
                booking_contract=booking_contract, requestor=db_user, payload=payload
            )
        except ServiceException as e:
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()

    booking_query = query_claimed_booking(booking_contract=booking_contract)
    booking_result = session.exec(booking_query).one()
    return booking_result


@router.patch(
    "/claimed/{booking_contract}/allocation_ratio",
    response_model=V2ClaimedBookingContractsModel,
)
def update_claimed_booking_allocation_ratios(
    booking_contract: int,
    payload: V2ModifyBookingAllocationRatio,
    db_user: GetUserDep,
    session: GetSessionDep,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """Modify the allocation ratios of a claimed booking"""

    if booking_contract != payload.booking_contract:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Booking contract in URL does not match booking contract in payload",
        )

    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            service.update_booking_allocation_ratios(
                booking_contract=booking_contract,
                requestor=db_user,
                allocation_fte_hw_ratio=payload.allocation_fte_hw_ratio,
                allocation_fte_sw_ratio=payload.allocation_fte_sw_ratio,
            )
        except ServiceException as e:
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()

    booking_query = query_claimed_booking(booking_contract=booking_contract)
    booking_result = session.exec(booking_query).one()
    return booking_result


@router.get("/unclaimed", response_model=list[V2BookingContractsModel])
def get_unclaimed_bookings(
    db_session: GetSessionDep,
):
    """
    Get a list of unclaimed bookings (bookings that have not been claimed by a manager).

    Notable exception is CXEA - Scale bookings, which are treated as 'available' to claim.
    """

    query = query_unclaimed_bookings()
    result = db_session.exec(query).all()

    return result


@router.get("/renewals", response_model=list[V2RenewableBookingResponse])
def get_available_to_renew_from(
    db_session: GetSessionDep,
):
    """Get a list of booking contracts that are available to renew from"""
    query = query_available_to_renew_from()
    result = db_session.exec(query).all()

    return result


@router.post("/claim/{booking_contract}", response_model=V2ClaimedBookingContractsModel)
def claim_booking(
    booking_contract: int,
    payload: V2ClaimBooking,
    db_user: GetUserDep,
    session: GetSessionDep,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """Claim a booking"""
    if booking_contract != payload.booking_contract:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Booking contract in URL does not match booking contract in payload",
        )

    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            service.claim_booking(
                requestor=db_user,
                booking_contract=booking_contract,
                renewal_sources=payload.renewed_from,
                dc_engagement_id_default=payload.dc_engagement_id_default,
                booking_override_reason_id=payload.booking_override_reason_id,
            )
        except ServiceException as e:
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()

    booking_query = query_claimed_booking(booking_contract=booking_contract)
    booking_result = session.exec(booking_query).one()
    return V2ClaimedBookingContractsModel.from_orm(booking_result)


@router.delete("/claim/{booking_contract}")
def unclaim_booking(
    booking_contract: int,
    db_user: GetUserDep,
    session: GetSessionDep,
    booking_types: ManagerBookingsServiceTypesDep,
):
    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            service.unclaim_booking(
                requestor=db_user,
                booking_contract=booking_contract,
            )
        except ServiceException as e:
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()
    return {"message": f"Booking Contract {booking_contract} unclaimed"}


@router.post("/disengage/{booking_contract}", response_model=V2DisengagementResponse)
def disengage_booking(
    booking_contract: int,
    payload: V2DisengagementModel,
    db_user: GetUserDep,
    session: GetSessionDep,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """
    Disengage a booking
    """
    if not booking_contract == payload.booking_contract:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Booking contract in URL does not match booking contract in payload",
        )

    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            result = service.disengage_booking_contract(
                payload=payload, requestor=db_user
            )
        except ServiceException as e:
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()

    return result


@router.post(
    "/extend/{booking_contract}", response_model=V2ClaimedBookingContractsModel
)
def extend_booking_contract(
    booking_contract: int,
    db_user: GetUserDep,
    session: GetSessionDep,
    settings: GetSettingsDep,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """Extend a booking"""
    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            service.extend_booking_contract(
                booking_contract=booking_contract,
                requestor=db_user,
                duration_days=settings.booking_extension_days,
                extension_count_limit=settings.booking_extension_count_limit,
            )
        except ServiceException as e:
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()

    booking_query = query_claimed_booking(booking_contract=booking_contract)
    booking_result = session.exec(booking_query).one()
    return V2ClaimedBookingContractsModel.from_orm(booking_result)


@router.post("/prospective", response_model=V2ClaimedBookingContractsModel)
def create_prospective_booking(
    payload: V2ProspectiveBookingPayload,
    db_user: GetUserDep,
    session: GetSessionDep,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """
    Create a prospective booking
    ----

    Currently, there are two types:
    - Prospective Booking Without Allocation
        - This is a booking in which a service is performed without revenue. Therefore, it does not have allocation.
    - Prospective Booking With Allocation
        - This is a booking in which a service is performed with revenue. Its source is outside the system.

    These types are indicated by the booking_contract_type_id.
    This corresponds to the ``.extra`` field ``is_prospective`` and ``is_budgeted``.

    If the booking_contract_type_id corresponds to a booking type that is not prospective, an error will be raised.
    If the booking_contract_type_id corresponds to a booking type that is not budgeted, and non-zero allocation are
     provided, they will be ignored.

    """
    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            booking_contract_id = service.create_prospective_booking(
                payload=payload, requestor=db_user
            )
        except ServiceException as e:
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()

    booking_query = query_claimed_booking(booking_contract=booking_contract_id)
    booking_result = session.exec(booking_query).one()
    return V2ClaimedBookingContractsModel.from_orm(booking_result)


@router.patch(
    "/prospective/{booking_contract}", response_model=V2ClaimedBookingContractsModel
)
def update_prospective_booking(
    payload: V2ProspectiveBookingEditPayload,
    db_user: GetUserDep,
    session: GetSessionDep,
    booking_contract: int,
    booking_types: ManagerBookingsServiceTypesDep,
):
    """
    Update an existing prospective booking

    Notes
    -----
    All fields in the payload are optional except for `booking_contract`. Fields that are not set will not be updated.
    """
    if booking_contract != payload.booking_contract:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Booking contract in URL does not match booking contract in payload",
        )

    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            service.update_prospective_booking(payload=payload, requestor=db_user)
        except ServiceException as e:
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()

    booking_query = query_claimed_booking(booking_contract=payload.booking_contract)
    booking_result = session.exec(booking_query).one()
    return V2ClaimedBookingContractsModel.from_orm(booking_result)


@router.delete("/prospective/{booking_contract}")
def delete_prospective_booking(
    db_user: GetUserDep,
    session: GetSessionDep,
    booking_types: ManagerBookingsServiceTypesDep,
    booking_contract: Annotated[int, Path(title="The booking contract ID", lt=0)],
):
    with ManagerBookingsService(
        session, booking_types=booking_types, ignore_dispatch=False
    ) as service:
        try:
            service.delete_prospective_booking(
                booking_contract=booking_contract,
                requestor=db_user,
            )
        except ServiceException as e:
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

        session.commit()
    return {"message": f"Booking Contract {booking_contract} deleted"}
