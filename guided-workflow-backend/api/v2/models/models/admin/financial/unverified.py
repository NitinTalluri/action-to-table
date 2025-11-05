from datetime import date
from typing import Optional

from pydantic.v1 import Field, conint

from .. import Model


class V2BookingId(Model):
    booking_contract: int = Field(
        ..., description="Booking Contract ID", example=1005559000
    )


class V2BookedAllocation(Model):
    booked_sw: float = Field(
        ..., description="Booked Software - Allocation of CAM", example=130
    )
    booked_hw: float = Field(
        ..., description="Booked Hardware - Allocation of CAM", example=70
    )


class V2BookingRenewal(Model):
    is_renewal: bool = Field(
        ..., description="Whether or not this is a renewal", example=True
    )


class V2BookingDetailsPartial(V2BookedAllocation, V2BookingRenewal):
    """
    Partial Booking Details Model

    Allows for the *_id fields to be null/None but are still required to be explicitly passed
    """

    account_name: str = Field(..., example="Booking Name")
    booked_theater_id: Optional[int] = Field(..., example=1)
    sold_as_service_type_id: Optional[int] = Field(..., example=2)
    sold_as_pricing_type_id: Optional[int] = Field(..., example=1)
    buying_program_type_id: Optional[int] = Field(..., example=2)
    agreement_start_date: Optional[date] = Field(None, example="2022-01-01")
    agreement_end_date: Optional[date] = Field(None, example="2024-12-31")


class V2BookingDetails(V2BookedAllocation):
    """
    Booking Details Model

    Use for when all *_id fields are required

    Does not include is_renewal (read only)
    """

    account_name: str = Field(..., example="Booking Name")
    booked_theater_id: conint(ge=0) = Field(..., example=1)
    sold_as_service_type_id: conint(ge=0) = Field(..., example=2)
    sold_as_pricing_type_id: conint(ge=0) = Field(..., example=6)
    buying_program_type_id: conint(ge=-1) = Field(..., example=2)
    agreement_start_date: Optional[date] = Field(None, example="2022-01-01")
    agreement_end_date: Optional[date] = Field(None, example="2024-12-31")


class V2UnverifiedBookingResponse(V2BookingId, V2BookingDetailsPartial):
    """Combines BookingId, BookedAllocation, and BookingDetailsPartial"""

    pass


class V2VerifyBooking(V2BookingId, V2BookingDetails):
    """
    Combines BookingId, BookedAllocation, and BookingDetails

    User wants to verify a booking
    """

    ...
