from sqlalchemy import ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column

from . import V2MetadataBase

seq_dc_announcement_links = Sequence(
    name="seq_dc_announcement_links",
    metadata=V2MetadataBase.metadata,
    start=1,
    increment=1,
)


class V2AnnouncementLink(V2MetadataBase):
    __tablename__ = "dc_announcement_link"

    id: Mapped[int] = mapped_column(
        Integer,
        seq_dc_announcement_links,
        server_default=seq_dc_announcement_links.next_value(),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(1 << 10), nullable=False)
    href: Mapped[str] = mapped_column(String(1 << 16), nullable=False)
    announcement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_announcements.id")
    )
