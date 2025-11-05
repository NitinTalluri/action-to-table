from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import V2MetadataBase

if TYPE_CHECKING:
    from ..models import V2CamEngagementWrite


class V2CamEngagement(V2MetadataBase):
    __tablename__ = "dc_cam_to_engagement"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("dc_users.user_id"), primary_key=True
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    user = relationship("V2User", back_populates="engagements")
    engagement = relationship("V2Engagement", back_populates="users")

    @classmethod
    def create_from_model(cls, model: "V2CamEngagementWrite", logged_user, session):
        return super().create_from_model(model, logged_user, session)
