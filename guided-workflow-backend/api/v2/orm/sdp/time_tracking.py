import datetime

from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    Integer,
    Sequence,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase


class SDPUserTimeEntry(V2MetadataBase):
    __tablename__ = "dc_sdp_time_entry"

    entry_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("seq_dc_generic"),
        primary_key=True,
        server_default=Sequence("dc_seq_generic").next_value(),
    )
    booking_contract: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract"), nullable=True
    )
    dc_engagement_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), nullable=True
    )
    dc_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_users.user_id"), nullable=False
    )
    deliverable_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_sdp_typ_deliverable.deliverable_id"), nullable=True
    )
    abstract_deliverable_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("dc_sdp_typ_abstract_deliverable.abstract_deliverable_id"),
        nullable=True,
    )
    hours: Mapped[float] = mapped_column(
        Float, default=0, server_default=text("0.0"), nullable=False
    )
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
