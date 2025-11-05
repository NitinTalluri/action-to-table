from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm.users import V2User

from . import V2MetadataBase


class V2UserAnnouncement(V2MetadataBase):
    __tablename__ = "dc_user_to_announcement"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(V2User.user_id), primary_key=True, nullable=False
    )
    announcement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_announcements.id"), primary_key=True, nullable=False
    )
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
