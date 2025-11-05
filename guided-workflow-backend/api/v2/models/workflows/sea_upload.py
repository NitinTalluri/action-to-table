from typing import Optional

from pydantic.v1 import BaseModel, Field

from .. import Model


class V2SEAUploadPayload(Model):
    dc_engagement_id: int = Field(..., title="DC Engagement ID")
    comment: Optional[str] = Field("", title="Comment")


class V2SEAUploadRowSchema(BaseModel):
    device_covered: Optional[str] = Field(None, description="Device Covered")
    product_id: str = Field(None, description="Product ID")
    serial_number: Optional[str] = Field(None, description="Serial Number")
    instance_number: Optional[int] = Field(None, description="Instance Number")
    major_minor: Optional[str] = Field(None, description="Major/Minor")
    parent_instance_number: Optional[int] = Field(
        None, description="Parent Instance Number"
    )
    service_type: Optional[str] = Field(None, description="Service Type")
    service_sku: Optional[str] = Field(None, description="Service SKU")
    cost_of_covered: Optional[int] = Field(None, description="Cost of Covered")
    remaining_value_of_purchased_coverage: Optional[int] = Field(
        None, description="Remaining Value of Purchased Coverage"
    )
    remaining_one_time_discount_uncovered_asset_credit: Optional[int] = Field(
        None, description="Remaining One Time Discount/Uncovered Asset Credit"
    )
    cost_of_added_device: Optional[int] = Field(
        None, description="Cost of Added Device"
    )
    discount: Optional[str] = Field(None, description="Discount")
    list_price: Optional[int] = Field(None, description="List Price")
    price_protected: Optional[str] = Field(None, description="Price Protected")
    contract_number: Optional[int] = Field(None, description="Contract Number")
    subscription_id: Optional[str] = Field(None, description="Subscription ID")
    tf_start_date: Optional[str] = Field(None, description="TF Start Date")
    ea_end_date: Optional[str] = Field(None, description="EA End Date")
    customer_location: Optional[str] = Field(None, description="Customer Location")
    last_date_of_support: Optional[str] = Field(
        None, description="Last Date Of Support"
    )
    so_mso_number: Optional[str] = Field(None, description="SO/MSO Number")
    po_pso_number: Optional[str] = Field(None, description="PO/PSO Number")
    status: Optional[str] = Field(None, description="Status")
    transaction_type: Optional[str] = Field(None, description="Transaction Type")
    transaction_source: Optional[str] = Field(None, description="Transaction Source")
    install_site_country: Optional[str] = Field(
        None, description="Install Site Country"
    )
    install_site_location: Optional[str] = Field(
        None, description="Install Site Location"
    )
    product_family: Optional[str] = Field(None, description="Product Family")
    service_suite: Optional[str] = Field(None, description="Service Suite")
    service_level: Optional[str] = Field(None, description="Service Level")
    service_start_date: Optional[str] = Field(None, description="Service Start Date")
    service_end_date: Optional[str] = Field(None, description="Service End Date")
    terminated_date: Optional[str] = Field(None, description="Terminated Date")
    ship_date: Optional[str] = Field(None, description="Ship Date")
    unit_list_price: Optional[str] = Field(None, description="Unit List Price")
    duration: Optional[str] = Field(None, description="Duration")


__all__ = [
    "V2SEAUploadPayload",
    "V2SEAUploadRowSchema",
]
