from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from . import V2MetadataBase


class V2BookingResponsibleUsers(V2MetadataBase):
    __tablename__ = "dc_bookings_contracts_responsible_users"
    booking_contract: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract"), primary_key=True
    )
    dc_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_users.user_id"), primary_key=True
    )
    sub_allocation_hw: Mapped[float] = mapped_column(Float, default=0)
    sub_allocation_sw: Mapped[float] = mapped_column(Float, default=0)
    service_role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_user_role.bookings_role_id"), default=1
    )
    notes: Mapped[str | None] = mapped_column(String, default=None)


class V2BookingToEngagementResponsibleUser(V2MetadataBase):
    __tablename__ = "dc_engagement_to_bookings_responsible_user"
    booking_contract: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract"), primary_key=True
    )
    dc_user_id: Mapped[int] = mapped_column(
        ForeignKey("dc_users.user_id"), primary_key=True
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )


class V2BookingsUserRole(V2MetadataBase):
    __tablename__ = "dc_bookings_user_role"
    bookings_role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bookings_role: Mapped[str] = mapped_column(String)


__all__ = [
    "V2BookingResponsibleUsers",
    "V2BookingToEngagementResponsibleUser",
    "V2BookingsUserRole",
]
