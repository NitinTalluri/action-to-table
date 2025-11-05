from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from dateutil import relativedelta
from pydantic.v1 import Field, condecimal, confloat, conint, root_validator

from api.v2.models.admin.financial.unverified import V2BookingId

from . import BookingContractType, Model, V2RecordMetaData


class V2ContractRead(V2RecordMetaData):
    contract_number: int
    dc_engagement_id: int
    booking_contract: Optional[str]
    cams: Optional[str]
    am_start_date: Optional[date]
    am_end_date: Optional[date]
    allowed_service_levels: Optional[str]
    service_contract_type_id: Optional[int] = 1
    asset_management_type_id: Optional[int] = 1
    monitor_reason_type_id: Optional[int] = 1


class V2ContractCreate(Model):
    contract_number: int
    booking_contract: Optional[str]
    cams: Optional[str]
    am_start_date: Optional[date]
    am_end_date: Optional[date]
    allowed_service_levels: Optional[str]
    service_contract_type_id: Optional[int] = 1
    asset_management_type_id: Optional[int] = 1
    monitor_reason_type_id: Optional[int] = 1


class V2ContractDelete(Model): ...


class V2ContractWrite(Model):
    contract_number: Optional[conint(ge=0)]
    dc_engagement_id: conint(ge=0)
    booking_contract: Optional[str] = None
    cams: Optional[str] = None
    am_start_date: Optional[date] = None
    am_end_date: Optional[date] = None
    allowed_service_levels: Optional[str] = None
    service_contract_type_id: Optional[conint(ge=0)] = 1
    asset_management_type_id: Optional[conint(ge=0)] = 1
    monitor_reason_type_id: Optional[conint(ge=0)] = 1


class V2ContractUpdate(Model):
    booking_contract: Optional[str] = None
    cams: Optional[str] = None
    am_start_date: Optional[date] = None
    am_end_date: Optional[date] = None
    allowed_service_levels: Optional[str] = None
    service_contract_type_id: Optional[conint(ge=0)] = 1
    asset_management_type_id: Optional[conint(ge=0)] = 1
    monitor_reason_type_id: Optional[conint(ge=0)] = 1


####################################################################################################
# the list of service contracts inside of a booking record
class V2ManagedContractRead(V2RecordMetaData):
    contract_number: int
    allowed_service_levels: Optional[str]
    contract_name: Optional[str]
    notes: Optional[str]
    is_owner: Optional[str]
    user: Optional[str]


class V2ManagedContractCreate(Model):
    contract_number: int
    allowed_service_levels: Optional[str] = ""
    contract_name: Optional[str] = ""
    notes: Optional[str] = ""
    booking_contract: conint(ge=0)
    dc_engagement_id: conint(ge=0)
    dc_user_id: int


# this is the nested
class V2BookingContract_Update_Read(Model):
    booking_contract: int
    cams: Optional[str] = None
    am_start_date: Optional[date] = None
    am_end_date: Optional[date] = None
    allowed_service_levels: Optional[str] = None
    dc_engagement_id: conint(ge=0)
    service_contract_type_id: Optional[conint(ge=0)] = 1
    asset_management_type_id: Optional[conint(ge=0)] = 1
    monitor_reason_type_id: Optional[conint(ge=0)] = 1
    service_contracts: Optional[List[V2ManagedContractRead]]


class V2BookingContract_POST(Model):
    booking_contract: int
    dc_engagement_id: conint(ge=0)
    account_name: Optional[str] = None
    cams: Optional[str] = None
    agreement_start_date: Optional[date] = None
    agreement_end_date: Optional[date] = None
    managed_contracts: Optional[List[V2ManagedContractRead]]


# unmanaged based watch contracts


class V2MonitorContract_Update_Create(Model):
    contract_number: int
    created_by: Optional[str]
    monitor_type_id: Optional[int] = 1
    monitor_notes: Optional[str] = None


class V2Responsible_User_Contract_Link(Model):
    booking_contract: conint(ge=0)
    dc_user_id: conint(ge=0)
    dc_engagement_id: conint(ge=0)


class V2BookingContractsModel(Model):
    booking_contract: int = Field(..., description="Booking Contract")
    account_name: str = Field(..., description="Account Name")
    booked_sav_1: Optional[str] = Field(..., description="Booked SAV 1")
    booked_sav_2: Optional[str] = Field(..., description="Booked SAV 2")
    booked_sav_3: Optional[str] = Field(..., description="Booked SAV 3")
    booked_theater_id: int = Field(..., description="Booked Theater ID")
    booking_contract_type_id: int = Field(..., description="Booking Contract Type ID")
    sold_as_service_type_id: int = Field(..., description="Sold As Service Type ID")
    sold_as_pricing_type_id: int = Field(..., description="Sold As Pricing Type ID")
    buying_program_type_id: int = Field(..., description="Buying Program Type ID")
    booked_usd: Optional[float] = Field(..., description="Booked USD")
    agreement_start_date: date = Field(..., description="Agreement Start Date")
    agreement_end_date: date = Field(..., description="Agreement End Date")
    effective_end_date: date = Field(
        ..., description="Effective End Date (Agreement End + Any Extension)"
    )
    booking_country: Optional[str] = Field(..., description="Booking Country")
    cam_revenue_usd: Optional[float] = Field(..., description="CAM Revenue USD")
    cam_cost_usd: Optional[float] = Field(..., description="CAM Cost USD")
    sourced_allocation: Optional[float] = Field(..., description="Sourced Allocation")
    booked_date: Optional[date] = Field(..., description="Booked Date")
    booked_sw: float = Field(..., description="Sold As SW Allocation")
    booked_hw: float = Field(..., description="Sold As HW Allocation")
    renewed_from: Optional[list[int]]
    quote_for_audit: Optional[str] = Field(..., description="Quote For Audit")
    is_disengaged: bool
    is_virtual: bool = Field(
        ...,
        description="Virtual contracts are used for forecasting. They are indicated by a negative booking_contract",
    )
    derived_new_renew: Optional[BookingContractType] = Field(
        ...,
        description="Indicates if the booking is *believed* to be a new or renewal booking",
    )
    extended_count: int = Field(
        ...,
        description="Number of times the booking has been extended",
    )
    sales_level_id: int = Field(..., description="Sales Level ID")
    node_level1: str = Field("", description="Sales Level 1")
    node_level2: str = Field("", description="Sales Level 2")
    node_level3: str = Field("", description="Sales Level 3")
    node_level4: str = Field("", description="Sales Level 4")
    node_segment: str = Field("", description="Sales Level Segment")
    is_cxea: bool = Field(False, description="Whether this booking is CXEA Scale")
    dc_engagement_id_default: int | None = Field(
        ..., description="Default engagement id"
    )


class V2ClaimedBookingContractsModel(V2BookingContractsModel):
    dc_engagement_id: Optional[int]
    engagement_name: Optional[str]
    is_cxea: bool
    delivery_status: str
    dc_engagement_id_default: Optional[int] = Field(
        ..., description="Default engagement id"
    )
    claimed_and_managed_by: Optional[int] = Field(
        None,
        description="Cisco CCO ID of the user who claimed and manages the booking. This can be used to determine if "
        "the booking was explicitly claimed by the user or implicitly claimed by the user",
    )
    assignments: list[V2BookingNamedUserAssignment]
    allocation_fte_total: Decimal = Field(
        description="Total Allocation FTE. The Sum of booked_sw and booked_hw",
        example=1,
    )
    allocation_fte_hw_ratio: Decimal = Field(
        1,
        description="Hardware Allocation Ratio. When 1.0, allocation_fte_total is 100% HW",
        example=1,
    )
    allocation_fte_sw_ratio: Decimal = 0

    is_current_and_unassigned: bool = Field(
        default=False,
        description="Computed field that is True when agreement_end_date > 30 days and no assignments",
        example=True,
    )

    @root_validator()
    def validate_computed_fields(cls, values):
        # Running these here removes several correlated subqueries in sql. 250 ms vs 12 seconds
        assignments = values.get("assignments", [])
        is_current = values.get("agreement_end_date") > (
            date.today() + relativedelta.relativedelta(days=30)
        )
        unassigned = len(assignments) == 0
        is_current_and_unassigned = is_current and unassigned
        values["is_current_and_unassigned"] = is_current_and_unassigned
        return values


class V2BookingAllocationCalculated(Model):
    """
    For a verified booking, references the calculated SW / HW of the entire booking

    These are stored as percentanges, i.e. 100 == 100%
    """

    calculated_sw: confloat(ge=0.0, le=1000.0) = Field(
        ..., description="Calculated Software Allocation for Booking", example=120
    )
    calculated_hw: confloat(ge=0.0, le=1000.0) = Field(
        ..., description="Calculated Hardware Allocation for Booking", example=70
    )


class V2BookingAllocationActual(Model):
    booked_sw: float = Field(
        ...,
        description="Booked Software - Allocation of CAM",
        example=130,
    )
    booked_hw: float = Field(
        ...,
        description="Booked Hardware - Allocation of CAM",
        example=70,
    )


class V2UserAllocation(Model):
    """
    For a verified booking, references the assigned SW / HW for the user-booking relationship

    Notes
    -----
    total_fte_allocation: 10
    total_fte_hw_ratio: 0.5
    total_fte_sw_ratio: 0.5
    assignments: [
        {sub_allocation_sw: 0.9, sub_allocation_hw: 0.1},
        {sub_allocation_sw: 0.1, sub_allocation_hw: 0.9},
    ]
    """

    sub_allocation_sw: condecimal(ge=Decimal("0.0"), le=Decimal("1.0")) = Field(
        ..., description="Software Allocation for User", example=0.9
    )
    sub_allocation_hw: condecimal(ge=Decimal("0.0"), le=Decimal("1.0")) = Field(
        ..., description="Hardware Allocation for User", example=0.1
    )


class V2UserAssignment(Model):
    dc_user_id: int = Field(..., example=832, description="The numeric user id")

    service_role_id: int = Field(
        ..., description="User Role as Defined in Assignment Scope", example=1
    )


class V2BookingUserAssignment(V2UserAllocation, V2UserAssignment, V2BookingId):
    """
    Expected model when user wants to assign a user to a booking. Used as part of V2VerifiedBookingAssignmentModify

    Attributes
    ----------
    dc_user_id
    service_role_id
    sub_allocation_sw
    sub_allocation_hw
    booking_contract
    """

    ...


class V2BookingNamedUserAssignment(V2BookingUserAssignment):
    display_name: Optional[str] = Field(
        None, description="The display name of the user, if found"
    )
    dc_engagement_id: int
    engagement_name: str


class V2BookingEngagementAssignment(V2UserAssignment, V2UserAllocation):
    dc_engagement_id: int


class V2VerifiedBookingAssignmentModify(V2BookingId):
    """
    User wants to update the assignments to a booking

    Notes
    -----
    Modifications to assignments require passing all assignments to booking

    Delete - Remove assignments
    Add - Find V2BookingUserAssignment
    Modify - Find V2BookingUserAssignment and compare sw_allocation and hw_allocation
    """

    assignments: list[V2BookingEngagementAssignment]

    @root_validator
    def validate_assignments(cls, values):
        # A booking is one to many with engagements
        # A booking is one to many with users
        # A booking user is one to one with engagements (Can't have a user associated with 2+ engagements)

        # Validate that the user is not assigned to multiple engagements
        user_engagements = [
            (assignment.dc_user_id, assignment.dc_engagement_id)
            for assignment in values["assignments"]
        ]
        if len(user_engagements) != len(set(user_engagements)):
            raise ValueError("User is assigned to multiple engagements")
        return values


class V2VerifiedBookingDcTypes(Model):
    booked_theater_id: conint(ge=0) = Field(
        ..., description="Booked Theater ID", example=2
    )
    sold_as_service_type_id: conint(ge=0) = Field(
        ..., description="Service Type ID", example=2
    )
    sold_as_pricing_type_id: conint(ge=0) = Field(
        ..., description="Sold As Pricing ID", example=6
    )
    buying_program_type_id: conint(ge=0) = Field(
        ..., description="Buying Program ID", example=2
    )


class V2VerifiedBookingResponse(
    V2BookingId,
    V2BookingAllocationCalculated,
    V2BookingAllocationActual,
    V2VerifiedBookingDcTypes,
):
    account_name: str = Field(..., example="Booking Name")
    agreement_start_date: Optional[date]
    agreement_end_date: Optional[date]

    is_renewal: bool = Field(
        ..., description="Whether or not this is a renewal", example=True
    )
    is_current_and_unassigned: bool = Field(
        ..., description="Whether or not this is current and unassigned", example=True
    )
    assignments: list[V2BookingUserAssignment]


class V2VerifiedBookingAllocationModify(V2BookingId, V2BookingAllocationCalculated):
    """
    User wants to change the Calculated Allocation applying to the entire booking

    Attributes
    ----------
    booking_contract
    calculated_sw
    calculated_hw
    """

    ...


class V2VerifiedBookingDcTypesModify(V2BookingId, V2VerifiedBookingDcTypes):
    """
    User wants to change the DC Types of a booking

    Attributes
    ----------
    booked_theater_id
    sold_as_service_type_id
    sold_as_pricing_type_id
    buying_program_type_id
    """

    ...


# Booking Contract Read Models for get_booking_contracts endpoint
class V2ManagedContractBookingRead(Model):
    """
    Individual Managed Contract Read model for booking contracts endpoint
    """
    
    contract_number: str
    allowed_service_levels: str
    contract_name: str
    notes: str


class V2ManagedContractsBookingRead(Model):
    """
    Managed Contracts Read model containing contract details for booking contracts endpoint
    """
    
    contracts: list[V2ManagedContractBookingRead]


class V2ResponsibleUserBookingRead(Model):
    """
    Responsible User Read model for users associated with booking contracts
    """
    
    responsible_user: int
    responsible_user_cco: str
    is_block_owner: str  # "T" or "F"
    managed_contracts: V2ManagedContractsBookingRead


class V2BookingContractRead(Model):
    """
    Booking Contract Read model for booking contract data with responsible users and managed contracts
    """
    
    booking_contract: int
    account_name: str
    agreement_start_date: date
    agreement_end_date: date
    effective_end_date: date
    sold_as_service_name: str
    sold_as_pricing_model: str
    sold_as_buying_program: str
    dc_engagement_id: int
    responsible_users: list[V2ResponsibleUserBookingRead]


V2ClaimedBookingContractsModel.update_forward_refs()

__all__ = [
    "V2BookingContract_POST",
    "V2BookingContract_Update_Read",
    "V2BookingContractRead",
    "V2BookingContractsModel",
    "V2BookingEngagementAssignment",
    "V2BookingNamedUserAssignment",
    "V2BookingUserAssignment",
    "V2ClaimedBookingContractsModel",
    "V2ContractCreate",
    "V2ContractRead",
    "V2ContractUpdate",
    "V2ContractWrite",
    "V2ManagedContractBookingRead",
    "V2ManagedContractCreate",
    "V2ManagedContractsBookingRead",
    "V2MonitorContract_Update_Create",
    "V2ResponsibleUserBookingRead",
    "V2Responsible_User_Contract_Link",
    "V2VerifiedBookingAllocationModify",
    "V2VerifiedBookingAssignmentModify",
    "V2VerifiedBookingDcTypesModify",
    "V2VerifiedBookingResponse",
]
