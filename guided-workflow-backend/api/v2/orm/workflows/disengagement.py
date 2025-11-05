from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from .. import V2MetadataBase

if TYPE_CHECKING:
    from api.v2.models import V2DisengagementModel


class V2DisengagementReason(V2MetadataBase):
    __tablename__ = "dc_typ_disengage"

    disengagement_reason_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disengagement_reason: Mapped[str] = mapped_column(
        String(5000), nullable=False, unique=True
    )


class V2Disengagement(V2MetadataBase):
    __tablename__ = "dc_wf_disengage"
    disengagement_reason_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_typ_disengage.disengagement_reason_id")
    )
    booking_contract: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract")
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id")
    )
    dc_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("dc_users.user_id"))
    notes: Mapped[str] = mapped_column(String(1 << 16))

    __table_args__ = (
        PrimaryKeyConstraint(
            "booking_contract", "dc_engagement_id", "dc_user_id", "create_dtm"
        ),
    )

    # noinspection PyMethodOverriding
    @classmethod
    def create_from_model(
        cls,
        model: "V2DisengagementModel",
        logged_user: str,
        dc_engagement_id: int,
        user_id: int,
        session,
    ):
        model = cls(
            **model.dict(),
            created_by=logged_user,
            dc_user_id=user_id,
            dc_engagement_id=dc_engagement_id,
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        return model
