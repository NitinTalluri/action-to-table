from __future__ import annotations

from pydantic.v1 import Field, constr

from .. import Model


class V2SuperCustomerCreatePayload(Model):
    super_customer_name: constr(
        min_length=1, regex="^[a-zA-Z0-9_ ]+$", strip_whitespace=True
    )
    dc_engagement_ids: set[int] = Field(
        default_factory=set,
        description="List of dc_engagement_ids to associate. Pre-existing engagements will be dropped",
    )


class V2SuperCustomerUpdatePayload(V2SuperCustomerCreatePayload):
    """Model for updating (renaming) a super customer"""

    super_customer_id: int = Field(..., description="The super customer id")


class V2SuperCustomer(Model):
    super_customer_id: int = Field(..., description="The super customer id")
    super_customer_name: str = Field(..., description="The super customer name")
    dc_engagement_ids: set[int] = Field(
        ..., description="List of dc_engagement_ids associated with the super customer"
    )


class V2SuperCustomerResponse(Model):
    super_customers: list[V2SuperCustomer] = Field(
        default_factory=list, description="List of super customers"
    )
    names: dict[str, str] = Field(
        default_factory=dict,
        description="Map of Engagement Id : Engagement Name",
        example={"123": "Engagement 123", "456": "My Engagement"},
    )
    available_dc_engagement_ids: set[int] = Field(
        default_factory=set,
        description="List of dc_engagement_ids not associated with any super customer",
    )


class V2SuperCustomerDelete(Model):
    """Model for deleting a super customer"""

    super_customer_id: int


__all__ = [
    "V2SuperCustomerCreatePayload",
    "V2SuperCustomerDelete",
    "V2SuperCustomerResponse",
    "V2SuperCustomerUpdatePayload",
]
