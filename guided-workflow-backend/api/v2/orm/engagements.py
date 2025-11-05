from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import V2MetadataBase

if TYPE_CHECKING:
    from ..models import V2EngagementCreate, V2EngagementUpdate


class V2Engagement(V2MetadataBase):
    __tablename__ = "dc_engagement_hdr"
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_engagements"), primary_key=True
    )
    engagement_name: Mapped[str] = mapped_column(String(1 << 16))
    is_sfc: Mapped[str] = mapped_column(String(1), default="F")
    sfc_agreement_type: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_sfc_types.sfc_type_id")
    )
    is_cxea: Mapped[str] = mapped_column(String(1), default="F")
    is_software: Mapped[str] = mapped_column(String(1), default="F")
    notes: Mapped[str] = mapped_column(String(1 << 16), default="")
    users = relationship("V2CamEngagement", back_populates="engagement", viewonly=True)
    tagsets = relationship("V2Tagset", back_populates="engagement", viewonly=True)
    contracts = relationship("V2Contract", back_populates="engagement", viewonly=True)
    acat_links = relationship("V2AcatLink", back_populates="engagement", viewonly=True)
    mce_links = relationship("V2MceLink", back_populates="engagement", viewonly=True)
    party_links = relationship(
        "V2PartyLink", back_populates="engagement", viewonly=True
    )
    smart_links = relationship(
        "V2SmartLink", back_populates="engagement", viewonly=True
    )
    canvases = relationship("V2Canvas", back_populates="engagement")

    @classmethod
    def create_from_model(cls, model: "V2EngagementCreate", logged_user, session):
        return super().create_from_model(model, logged_user, session)

    def update_from_model(self, model: "V2EngagementUpdate", logged_user, session):
        return super().update_from_model(model, logged_user, session)


class V2EngagementSFCType(V2MetadataBase):
    __tablename__ = "dc_engagement_sfc_types"
    sfc_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sfc_agreement_type: Mapped[str] = mapped_column(String(1 << 16))
