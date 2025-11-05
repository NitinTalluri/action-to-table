from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import V2MetadataBase

if TYPE_CHECKING:
    from ..models import V2TagUpdate, V2TagWrite


class V2Tags(V2MetadataBase):
    __tablename__ = "dc_tags"
    tag_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_tags"), primary_key=True
    )
    tag_name: Mapped[str] = mapped_column(String(1 << 16))
    tag_desc: Mapped[str] = mapped_column(String(1 << 16))
    tagset_id: Mapped[int] = mapped_column(Integer, ForeignKey("dc_tagset.tagset_id"))
    tagset = relationship("V2Tagset", back_populates="tags")

    @classmethod
    def create_from_model(cls, model: "V2TagWrite", logged_user, session):
        return super().create_from_model(model, logged_user, session)

    def update_from_model(self, model: "V2TagUpdate", logged_user, session):
        return super().update_from_model(model, logged_user, session)
