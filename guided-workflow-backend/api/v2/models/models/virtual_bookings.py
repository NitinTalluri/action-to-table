from datetime import date
from typing import Literal, Optional, Union

from pydantic.v1 import Field, conint, root_validator

from api.v2.models import Model, VirtualBookingType


class V2SyntheticBookingId(Model):
    booking_contract: conint(le=-1) = Field(
        ...,
        description="The synthetic booking contract number. This must be a negative number to differentiate it from "
        "real booking contracts.",
    )


class V2VirtualBody(Model):
    account_name: str = Field(..., description="Prospective booking account name")
    agreement_start_date: date = Field(..., description="Agreement start date")
    agreement_end_date: date = Field(..., description="Agreement end date")
    booked_sav_1: Optional[str]
    booked_sav_2: Optional[str]
    booked_sav_3: Optional[str]
    booked_theater_id: int
    sold_as_service_type_id: int = 1
    sold_as_pricing_type_id: int = 1
    buying_program_type_id: int = 1
    booking_contract_type_id: conint(gt=1) = Field(
        ...,
        description="Booking contract type ID. Must correspond to an id where is_prospective is true",
    )
    booked_usd: float = 0
    booking_contract_status: Optional[str]
    booking_country: Optional[str]
    sales_level_2_finance: Optional[str]
    sales_level_3_finance: Optional[str]
    cam_revenue_usd: float = 0
    cam_cost_usd: float = 0
    notes: Optional[str]
    booked_date: Optional[date]
    dc_engagement_id: Optional[int]

    @root_validator
    def validate_root(cls, values):
        if values.get("agreement_start_date") >= values.get("agreement_end_date"):
            raise ValueError("Agreement start date cannot be after agreement end date")


class V2ProspectiveAllocation(Model):
    """Cannot have real allocations"""

    ib_calc_sw_allocation: float = 0
    ib_calc_hw_allocation: float = 0
    sold_as_sw_allocation: float = 0
    sold_as_hw_allocation: float = 0


class V2CreateProspectiveBookingPayload(V2VirtualBody, V2ProspectiveAllocation):
    """Must have 0 allocations"""

    @root_validator
    def validate_agreement_dates_and_allocations(cls, values):
        agreement_start_date = values.get("agreement_start_date")
        agreement_end_date = values.get("agreement_end_date")
        if agreement_start_date >= agreement_end_date:
            raise ValueError("Agreement start date cannot be after agreement end date")
        for key in (
            "ib_calc_sw_allocation",
            "ib_calc_hw_allocation",
            "sold_as_sw_allocation",
            "sold_as_hw_allocation",
        ):
            if values.get(key) != 0:
                raise ValueError(f"{key} must be 0 for prospective bookings")
        return values


class V2CrossChargeBookingPayload(V2VirtualBody, V2ProspectiveAllocation):
    """Can have allocations"""

    @root_validator
    def validate_agreement_dates_and_allocations(cls, values):
        agreement_start_date = values.get("agreement_start_date")
        agreement_end_date = values.get("agreement_end_date")
        if agreement_start_date >= agreement_end_date:
            raise ValueError("Agreement start date cannot be after agreement end date")
        for key in (
            "ib_calc_sw_allocation",
            "ib_calc_hw_allocation",
            "sold_as_sw_allocation",
            "sold_as_hw_allocation",
        ):
            if values.get(key) != 0:
                raise ValueError(f"{key} must be 0 for prospective bookings")
        return values


class V2ProspectiveBookingModel(
    V2SyntheticBookingId, V2CreateProspectiveBookingPayload
):
    virtual_type: Literal[VirtualBookingType.prospective] = Field(
        VirtualBookingType.prospective, exclude=True, example="prospective"
    )


class V2CrossChargeBookingModel(V2SyntheticBookingId, V2CrossChargeBookingPayload):
    virtual_type: Literal[VirtualBookingType.cross_charge] = Field(
        VirtualBookingType.cross_charge, exclude=True, example="cross-charge"
    )


class V2VirtualBookingPayload(Model):
    __root__: Union[V2ProspectiveBookingModel, V2CrossChargeBookingModel] = Field(
        discriminator="virtual_type"
    )


__all__ = ["V2VirtualBookingPayload"]
