import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Sequence,
    String,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from .. import JSONVarchar
from . import V2MetadataBase

seq_dc_announcements = Sequence(
    name="seq_dc_announcements", metadata=V2MetadataBase.metadata, start=1, increment=1
)


class V2Announcement(V2MetadataBase):
    __tablename__ = "dc_announcements"

    id: Mapped[int] = mapped_column(
        Integer,
        seq_dc_announcements,
        server_default=seq_dc_announcements.next_value(),
        primary_key=True,
    )
    title: Mapped[str] = mapped_column(String(1 << 10), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(1 << 16))
    body: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String(1 << 6), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    push_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    expiration_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    audience = Column(JSONVarchar, nullable=False)

    @hybrid_property
    def is_dismissed_by_user(self) -> bool:
        if not self.users:
            return False
        return self.users[0].is_dismissed_by_user
