from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column

from . import V2MetadataBase

if TYPE_CHECKING:
    from ..models import V2StakeholderUpdate, V2StakeholderWrite


class V2StakeholderType(V2MetadataBase):
    __tablename__ = "dc_engagement_stakeholder_types"
    stakeholder_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stakeholder_type: Mapped[str] = mapped_column(String(1 << 16))


class V2Stakeholder(V2MetadataBase):
    __tablename__ = "dc_engagement_stakeholders"
    stakeholder_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_stakeholders"), primary_key=True
    )
    stakeholder_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_stakeholder_types.stakeholder_type_id")
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    stakeholder_name: Mapped[str] = mapped_column(String(1 << 16))
    stakeholder_email: Mapped[str] = mapped_column(String(1 << 16))
    stakeholder_phone: Mapped[str] = mapped_column(String(1 << 16))

    @classmethod
    def create_from_model(cls, model: "V2StakeholderWrite", logged_user, session):
        return super().create_from_model(model, logged_user, session)

    def update_from_model(self, model: "V2StakeholderUpdate", logged_user, session):
        return super().update_from_model(model, logged_user, session)
