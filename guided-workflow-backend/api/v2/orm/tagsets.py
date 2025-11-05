from typing import TYPE_CHECKING, Union

from sqlalchemy import ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import V2MetadataBase

if TYPE_CHECKING:
    from api.v2.models import (
        V2CreateEngagementTagset,
        V2CreateGlobalTagset,
        V2UpdateEngagementTagset,
        V2UpdateGlobalTagset,
    )


class V2Tagset(V2MetadataBase):
    __tablename__ = "dc_tagset"
    tagset_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_tagset"), primary_key=True
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )

    tagset_name: Mapped[str] = mapped_column(String(1 << 16))
    tagset_desc: Mapped[str] = mapped_column(String(1 << 16))
    scope: Mapped[str] = mapped_column(String(1 << 16))
    cardinality: Mapped[str] = mapped_column(String(1 << 16))
    # tagset_type references a foreign key, but we leave it as an integer for now
    tagset_type: Mapped[int] = mapped_column(Integer)

    engagement = relationship("V2Engagement", back_populates="tagsets")
    tags = relationship("V2Tags", back_populates="tagset")

    @classmethod
    def create_from_model(
        cls,
        model: Union["V2CreateEngagementTagset", "V2CreateGlobalTagset"],
        logged_user,
        session,
    ):
        return super().create_from_model(model, logged_user, session)

    def update_from_model(
        self,
        model: Union["V2UpdateEngagementTagset", "V2UpdateGlobalTagset"],
        logged_user,
        session,
    ):
        # Only allow updating the tagset_desc
        self.tagset_desc = model.tagset_desc
        self.updated_by = logged_user
        self.is_deleted = "F"
        session.commit()
        session.refresh(self)
        return self
