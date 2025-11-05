from sqlalchemy import ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column

from .. import V2MetadataBase

BookingOverrideSeq = Sequence("seq_dc_typ_booking_override")


class V2BookingOverrideReason(V2MetadataBase):
    __tablename__ = "dc_typ_booking_override"

    booking_override_reason_id: Mapped[int] = mapped_column(
        Integer,
        BookingOverrideSeq,
        primary_key=True,
        server_default=BookingOverrideSeq.next_value(),
    )
    booking_override_reason: Mapped[str] = mapped_column(
        String(5000), nullable=False, unique=True
    )


class V2BookingOverride(V2MetadataBase):
    __tablename__ = "dc_booking_override"

    booking_contract: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dc_bookings_contracts.booking_contract"),
        primary_key=True,
    )
    booking_override_reason_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_typ_booking_override.booking_override_reason_id")
    )


__all__ = ["V2BookingOverride", "V2BookingOverrideReason"]
