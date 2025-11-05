from typing import Optional

from pydantic.v1 import Field

from . import Model


class V2ManagerUser(Model):
    cisco_cco_id: str
    user_id: int
    user_title: str
    display_name: Optional[str]
    is_direct_report: bool
    theater: Optional[str]
    total_utilization: float = Field(
        description="The sum of the 'total_share_booking' field from the 'V2SubAllocationReport' table divided by 100 for Bookings that are active today"
    )
    starting_bookings: float = Field(
        description="The sum of the 'total_share_booking' field from the 'V2SubAllocationReport' table divided by 100 for Bookings that are starting between tomorrow and the projected days (30)"
    )
    expiring_bookings: float = Field(
        description="The sum of the 'total_share_booking' field from the 'V2SubAllocationReport' table divided by 100 for Bookings that are expiring between today and the projected days (30)"
    )
    projected_utilization: float
