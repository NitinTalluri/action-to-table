from datetime import date

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import JSONVarchar, V2MetadataBase


class SDPTaskCompletionReason(V2MetadataBase):
    __tablename__ = "dc_sdp_typ_task_completion_reason"

    completion_id: Mapped[int] = mapped_column(
        "completion_id", Integer, primary_key=True
    )
    completion_desc: Mapped[str] = mapped_column("completion_desc", String)
    extra = Column(JSONVarchar, default='{"is_default": false}')

    @hybrid_property
    def is_default(self):
        return self.extra.get("is_default", False)

    @is_default.expression
    def is_default(cls):
        return (
            func.nvl(func.get_path(func.parse_json(cls.extra), "is_default"), False)
            == True
        )


class SDPTaskCompletion(V2MetadataBase):
    __tablename__ = "dc_completed_deliverables"

    sub_task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_sdp_typ_subtask.sub_task_id")
    )
    booking_contract: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract")
    )
    dc_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("dc_users.user_id"))
    cycle_iterator: Mapped[int] = mapped_column(Integer)
    completion_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dc_sdp_typ_task_completion_reason.completion_id"),
        default=1,
        server_default="1",
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id")
    )
    note: Mapped[str] = mapped_column(String, default="", server_default="")
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "sub_task_id", "booking_contract", "dc_user_id", "cycle_iterator"
        ),
        PrimaryKeyConstraint(
            "sub_task_id",
            "booking_contract",
            "dc_user_id",
            "cycle_iterator",
            "dc_engagement_id",
        ),
    )


__all__ = [
    "SDPTaskCompletion",
    "SDPTaskCompletionReason",
]
