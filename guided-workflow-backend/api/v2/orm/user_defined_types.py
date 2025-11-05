from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Sequence, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import V2MetadataBase

if TYPE_CHECKING:
    from sqlmodel import Session

    from ..models import V2UserDefinedTypeCreate


class V2UserDefinedType(V2MetadataBase):
    __tablename__ = "dc_user_defined_type"
    id: Mapped[int] = mapped_column(
        Integer,
        Sequence("seq_dc_user_defined_type"),
        server_default=Sequence("seq_dc_user_defined_type").next_value(),
        primary_key=True,
    )
    value: Mapped[str] = mapped_column(String)
    field_name: Mapped[str] = mapped_column(String)
    dc_engagement_id: Mapped[int] = mapped_column(
        ForeignKey("dc_engagement_hdr.dc_engagement_id")
    )

    __table_args__ = (UniqueConstraint("dc_engagement_id", "field_name", "value"),)

    @classmethod
    def create_from_model(
        cls, model: "V2UserDefinedTypeCreate", logged_user: str, session: "Session"
    ):
        model = cls(
            **model.dict(),
            created_by=logged_user,
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        return model
