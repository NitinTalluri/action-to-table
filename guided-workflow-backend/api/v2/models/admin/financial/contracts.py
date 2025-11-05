from datetime import date

from pydantic.v1 import Field, conint, validator

from ... import Model, process_date


class V2BookedContractsEntry(Model):
    class Config:
        orm_mode = True
        use_enum_values = True
        anystr_max_length = 1 << 16
        anystr_strip_whitespace = True

    booking_contract: conint(ge=0) = Field(..., description="Booking Contract Number")
    account_name: str = Field(..., description="Account Name")
    booked_sav_1: str = Field(..., description="Booked SAV 1")
    booked_sav_2: str = Field(..., description="Booked SAV 2")
    booked_sav_3: str = Field(..., description="Booked SAV 3")
    booked_theater_id: int = Field(
        ..., description="Booked Theater ID", alias="booked_theater"
    )
    sold_as_service_type_id: int = Field(
        ..., description="Sold As Service Type ID", alias="sold_as_service_type"
    )
    sold_as_pricing_type_id: int = Field(
        ..., description="Sold As Pricing Type ID", alias="sold_as_pricing_type"
    )
    buying_program_type_id: int = Field(
        ..., description="Buying Program Type ID", alias="buying_program_type"
    )
    calculated_sw: float = Field(
        ..., description="IB Calc SW Allocation", alias="ib_calc_sw_allocation"
    )
    calculated_hw: float = Field(
        ..., description="IB Calc HW Allocation", alias="ib_calc_hw_allocation"
    )
    booked_sw: float = Field(
        ..., description="Sold As SW Allocation", alias="sold_as_sw_allocation"
    )
    booked_hw: float = Field(
        ..., description="Sold As HW Allocation", alias="sold_as_hw_allocation"
    )
    agreement_start_date: date = Field(..., description="Agreement Start Date")
    agreement_end_date: date = Field(..., description="Agreement End Date")
    booking_country: str = Field(..., description="Booking Country")
    cam_revenue_usd: float = Field(..., description="CAM Revenue USD")

    _parse_dates = validator(
        "agreement_start_date", "agreement_end_date", allow_reuse=True, pre=True
    )(process_date)


class V2BookedContractsStoredProcParams(Model):
    __root__: list[V2BookedContractsEntry]


class V2BookedContractsResponse(Model):
    count: int = Field(..., description="Count")
