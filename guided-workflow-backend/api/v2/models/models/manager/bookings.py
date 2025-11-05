from datetime import date
from decimal import Decimal
from typing import Literal, Optional, TypedDict

from pydantic.v1 import Field, condecimal, confloat, conint, conlist, root_validator

from . import Model


class V2ClaimBooking(Model):
    booking_contract: conint(ge=0) = Field(
        ..., description="The booking contract id to claim"
    )
    renewed_from: Optional[conlist(item_type=conint(ge=0), unique_items=True)] = Field(
        ..., description="The booking contract ids that this booking is renewed from"
    )

    dc_engagement_id_default: Optional[int] = Field(
        default=None,
        description="The default engagement id for this booking",
    )

    booking_override_reason_id: Optional[int] = Field(
        default=None,
        description="The reason ID for overriding the understanding that CXEA Scale bookings are not typically claimed",
    )

    @root_validator
    def validate_renewed_from(cls, values):
        if values["booking_contract"] in values.get("renewed_from", []):
            raise ValueError("Cannot renew from self")
        return values


class V2ModifyBookingDcTypes(Model):
    booking_contract: int = Field(..., description="The booking contract id to modify")

    booked_theater_id: conint(ge=1) = Field(
        ..., description="The new booked theater id"
    )

    sold_as_service_type_id: conint(ge=1) = Field(
        ..., description="The new sold as service type id"
    )
    sold_as_pricing_type_id: conint(ge=1) = Field(
        ..., description="The new sold as pricing type id"
    )
    buying_program_type_id: conint(ge=1) = Field(
        ..., description="The new buying program type id"
    )


class V2ModifyBookingDefaultEngagement(Model):
    booking_contract: int = Field(..., description="The booking contract id to modify")
    dc_engagement_id_default: int = Field(
        ..., description="The new default engagement id for this booking"
    )


class V2ModifyBookingAllocationRatio(Model):
    booking_contract: int = Field(..., description="The booking contract id to modify")

    allocation_fte_sw_ratio: condecimal(ge=Decimal("0.0"), le=Decimal("1.0")) = Field(
        ..., description="The new software allocation ratio"
    )
    allocation_fte_hw_ratio: condecimal(ge=Decimal("0.0"), le=Decimal("1.0")) = Field(
        ..., description="The new hardware allocation ratio"
    )

    @root_validator
    def validate_allocation_ratios(cls, values):
        if values["allocation_fte_sw_ratio"] + values[
            "allocation_fte_hw_ratio"
        ] != Decimal("1.0"):
            raise ValueError("Allocation ratios must sum to 1.0")
        return values


class V2EngagementList(Model):
    engagement_name: str = Field(..., description="The engagement name")
    dc_engagement_id: int = Field(..., description="The engagement id")


class V2RenewableBookingResponse(Model):
    """Lighter-weight view of available bookings for renewal"""

    booking_contract: int = Field(..., description="The booking contract id")
    account_name: str = Field(..., description="The account name")
    agreement_start_date: date = Field(..., description="The agreement start date")
    agreement_end_date: date = Field(..., description="The agreement end date")
    effective_end_date: date = Field(
        ..., description="The effective end date after considering extensions"
    )

    engagements: Optional[list[V2EngagementList]] = Field(
        ..., description="The engagements associated with this booking"
    )
    renewed_from: list[int] = Field(
        ..., description="The booking contract ids that this booking is renewed from"
    )
    buying_program_type_id: conint(ge=-1)
    sold_as_service_type_id: conint(ge=1)
    sold_as_pricing_type_id: conint(ge=1)
    booking_contract_type_id: conint(ge=1)
    manager_name: Optional[str] = None
    employee_names: Optional[list[str]] = None
    sales_level_id: int
    node_level1: str = Field("", description="Sales Level 1")
    node_level2: str = Field("", description="Sales Level 2")
    node_level3: str = Field("", description="Sales Level 3")
    node_level4: str = Field("", description="Sales Level 4")
    node_segment: str = Field("", description="Sales Level Segment")


class V2ProspectiveBookingPayload(Model):
    account_name: str
    buying_program_type_id: conint(ge=1)
    sold_as_service_type_id: conint(ge=1)
    sold_as_pricing_type_id: conint(ge=1)
    booking_contract_type_id: conint(ge=1) = Field(
        ...,
        description="The booking contract type id. Can be any valid id from the booking_contract_type with is_prospective == true",
        examples=[2, 3],
    )
    booked_theater_id: conint(ge=1)
    agreement_start_date: date
    agreement_end_date: date
    booked_usd: float = Field(0.0)
    booking_country: Optional[str] = None
    cam_revenue_usd: float = Field(0.0)
    cam_cost_usd: float = Field(0.0)
    sourced_allocation: float = Field(0.0)
    quote_for_audit: Literal[None] = Field(None, const=True)
    booked_date: Literal[None] = Field(None, const=True)
    sold_as_sw_allocation: Decimal = Field("0.0")
    sold_as_hw_allocation: Decimal = Field("0.0")


class V2ProspectiveBookingEditPayload(Model):
    booking_contract: conint(lt=0)
    account_name: Optional[str] = None
    buying_program_type_id: Optional[conint(ge=1)] = None
    sold_as_service_type_id: Optional[conint(ge=1)] = None
    sold_as_pricing_type_id: Optional[conint(ge=1)] = None
    booked_theater_id: Optional[conint(ge=1)] = None
    agreement_start_date: Optional[date] = None
    agreement_end_date: Optional[date] = None
    booked_usd: Optional[float] = None
    booking_country: Optional[str] = None
    cam_revenue_usd: Optional[float] = None
    cam_cost_usd: Optional[float] = None
    sourced_allocation: Optional[float] = None
    sold_as_sw_allocation: Optional[Decimal] = None
    sold_as_hw_allocation: Optional[Decimal] = None
    dc_engagement_id_default: Optional[int] = None


class SalesLevelAssignmentError(TypedDict):
    booking_contract: int
    sales_level_id: int
    message: str


class V2SalesLevelAssignment(Model):
    booking_contract: int = Field(
        ..., description="The booking contract id", examples=[12345, 67890]
    )
    sales_level_id: int = Field(
        ..., description="The sales level id (0 for unassigned)", examples=[0]
    )


class V2BulkSalesLevelAssignment(Model):
    assignments: list[V2SalesLevelAssignment] = Field(
        ...,
        description="List of sales level assignments",
        examples=[[{"booking_contract": 12345, "sales_level_id": 0}]],
    )


class V2BulkSalesLevelAssignmentResponse(Model):
    has_errors: bool = Field(..., description="Whether any errors occurred")
    errors: list[SalesLevelAssignmentError] = Field(
        ...,
        description="List of assignment errors",
        examples=[
            [
                {
                    "booking_contract": 12345,
                    "sales_level_id": 0,
                    "message": "Duplicate booking contract",
                }
            ]
        ],
    )
    assignments: dict[int, int] = Field(
        ...,
        description="Successful assignments mapping booking_contract to sales_level_id",
        examples=[{12345: 0, 67890: 1}],
    )
