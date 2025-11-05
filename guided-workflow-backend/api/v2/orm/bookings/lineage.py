from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import V2MetadataBase


class V2BookingContractsLineage(V2MetadataBase):
    __tablename__ = "dc_bookings_contracts_lineage"

    parent_booking_contract: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract"), primary_key=True
    )
    child_booking_contract: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract"), primary_key=True
    )

    child = relationship("V2BookingContracts", foreign_keys=[child_booking_contract])
    parent = relationship("V2BookingContracts", foreign_keys=[parent_booking_contract])

    __table_args__ = (
        UniqueConstraint(
            "parent_booking_contract", "child_booking_contract", name="unique_lineage"
        ),
    )


__all__ = [
    "V2BookingContractsLineage",
]
