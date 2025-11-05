import datetime
from typing import TYPE_CHECKING, Union

from sqlalchemy import Column, Date, ForeignKey, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from .. import V2MetadataBase

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.v2.models import V2DeferredSignOffAPI, V2SignedOffAPI


class V2WfSignoffMethod(V2MetadataBase):
    __tablename__ = "dc_typ_signoff_method"
    signoff_method_id: Mapped[int] = mapped_column(
        Integer, nullable=False, primary_key=True
    )
    signoff_method: Mapped[str] = mapped_column(
        String(5000), nullable=False, unique=True
    )


class V2WfSignoffEvent(V2MetadataBase):
    __tablename__ = "dc_typ_signoff_event"
    signoff_event_id: Mapped[int] = mapped_column(
        Integer, nullable=False, primary_key=True
    )
    signoff_event: Mapped[str] = mapped_column(
        String(5000), nullable=False, unique=True
    )


class V2WfSignoffIdentity(V2MetadataBase):
    __tablename__ = "dc_typ_sign_off_identity"
    sign_off_identity_id: Mapped[int] = mapped_column(
        Integer, nullable=False, primary_key=True
    )
    sign_off_identity: Mapped[str] = mapped_column(
        String(5000), nullable=False, unique=True
    )


class V2WfDeferSignoffReason(V2MetadataBase):
    __tablename__ = "dc_typ_defer_signoff_reason"
    defer_signoff_reason_id: Mapped[int] = mapped_column(
        Integer, nullable=False, primary_key=True
    )
    defer_signoff_reason: Mapped[str] = mapped_column(
        String(5000), nullable=False, unique=True
    )


class V2WfSignoff(V2MetadataBase):
    __tablename__ = "dc_wf_ib_signoff"
    signoff_method_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_typ_signoff_method.signoff_method_id"), nullable=False
    )
    signoff_event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_typ_signoff_event.signoff_event_id"), nullable=False
    )
    sign_off_identity_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dc_typ_sign_off_identity.sign_off_identity_id"),
        nullable=False,
    )
    defer_signoff_reason_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dc_typ_defer_signoff_reason.defer_signoff_reason_id"),
        nullable=False,
    )
    booking_contract: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract"), nullable=False
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), nullable=False
    )
    effective_date: Mapped[datetime.date | None] = mapped_column(Date(), nullable=True)
    dc_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_users.user_id"), nullable=False
    )
    notes: Mapped[str] = mapped_column(String(5000), default="")

    __table_args__ = (
        PrimaryKeyConstraint(
            "booking_contract", "dc_engagement_id", "dc_user_id", "create_dtm"
        ),
    )

    @classmethod
    def create_from_model(
        cls,
        model: Union["V2SignedOffAPI", "V2DeferredSignOffAPI"],
        logged_user: str,
        session: "Session",
    ) -> "V2WfSignoff":
        from api.v2.models import V2DeferredSignOffAPI, V2SignedOffAPI

        match model:
            case V2DeferredSignOffAPI():  # Deferred
                data = {
                    **model.dict(exclude={"is_deferred"}),
                    **{
                        "signoff_method_id": 7,
                        "sign_off_identity_id": 1,
                        "signoff_event_id": 1,
                    },
                }
                model = cls(**data, created_by=logged_user)
            case V2SignedOffAPI():  # Not Deferred
                data = {
                    **model.dict(exclude={"is_deferred"}),
                    **{"defer_signoff_reason_id": 1},
                }
                model = cls(**data, created_by=logged_user)
            case _:
                raise ValueError("Invalid model type")

        session.add(model)
        session.commit()
        session.refresh(model)
        return model
