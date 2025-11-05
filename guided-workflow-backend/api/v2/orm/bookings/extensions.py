import datetime

from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase


class V2BookingContractsExtensions(V2MetadataBase):
    """Tracks when a contract is extended and by whom. Intent is to allow but limit this"""

    __tablename__ = "dc_booking_contracts_extensions"

    booking_contract: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract"), primary_key=True
    )
    extension_start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    extension_end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)


__all__ = [
    "V2BookingContractsExtensions",
]
