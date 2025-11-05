from sqlalchemy import Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase


class SDPTriggerEvent(V2MetadataBase):
    """
    The idea of this table is to store triggering events. The implementation of this table is TBD.

    """

    __tablename__ = "dc_sdp_typ_trigger_event"

    trigger_event_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_sdp"), primary_key=True
    )
    trigger_event_desc: Mapped[str] = mapped_column(
        String(5000), default="", unique=True, nullable=False
    )
    trigger_event_link: Mapped[str | None] = mapped_column(String(5000))
    trigger_event_type: Mapped[str | None] = mapped_column(String(5000))
    trigger_logic: Mapped[str | None] = mapped_column(String(5000))
