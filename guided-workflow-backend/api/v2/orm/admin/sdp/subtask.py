from typing import TYPE_CHECKING

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    Sequence,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.v2.models import AdminSDPSubTaskCreate, AdminSDPSubTaskEdit


class SDPSubTask(V2MetadataBase):
    """
    A sub-task is a low-level activity that is part of the service delivery plan. A sub-task can be linked to
     multiple tasks.

    Subtasks will be the primary user-facing entity in the service delivery plan.
    """

    __tablename__ = "dc_sdp_typ_subtask"

    sub_task_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_sdp"), primary_key=True
    )
    subtask_desc: Mapped[str] = mapped_column(String(5000), nullable=False)
    subtask_desc_long: Mapped[str | None] = mapped_column(String(20000))
    subtask_doc_link: Mapped[str] = mapped_column(
        String(5000), default="", nullable=False, server_default=""
    )
    hours: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    frequency: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    cycle_days: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    @classmethod
    def create_from_model(
        cls, model: "AdminSDPSubTaskCreate", logged_user: str, session: "Session"
    ):
        db_model = cls(
            subtask_desc=model.subtask_desc,
            subtask_doc_link=model.subtask_doc_link,
            subtask_desc_long=model.subtask_desc_long,
            hours=model.hours,
            frequency=model.frequency,
            cycle_days=model.cycle_days,
        )
        session.add(db_model)
        session.commit()
        session.refresh(db_model)

        return db_model

    def update_from_model(
        self, model: "AdminSDPSubTaskEdit", logged_user: str, session: "Session"
    ):
        self.subtask_desc = model.subtask_desc
        self.subtask_desc_long = model.subtask_desc_long
        self.subtask_doc_link = model.subtask_doc_link
        self.hours = model.hours
        self.frequency = model.frequency
        self.cycle_days = model.cycle_days
        self.updated_by = logged_user

        session.add(self)
        session.commit()
        session.refresh(self)
        return self


class SDPSubTaskServicePlans(V2MetadataBase):
    __tablename__ = "dc_sdp_sub_task_to_enab_sold_as"
    sub_task_id: Mapped[int] = mapped_column(
        ForeignKey("dc_sdp_typ_subtask.sub_task_id")
    )
    sold_as_service_type_id: Mapped[int] = mapped_column(
        ForeignKey("dc_sold_as_service_types.service_type_id"),
        name="sold_as_service_id",
    )

    __table_args__ = (PrimaryKeyConstraint("sub_task_id", "sold_as_service_id"),)


class SDPSubTaskPricingModels(V2MetadataBase):
    __tablename__ = "dc_sdp_sub_task_to_enab_pricing"
    sub_task_id: Mapped[int] = mapped_column(
        ForeignKey("dc_sdp_typ_subtask.sub_task_id")
    )
    pricing_type_id: Mapped[int] = mapped_column(
        ForeignKey("dc_pricing_model.pricing_type_id"), name="pricing_model_id"
    )

    __table_args__ = (PrimaryKeyConstraint("sub_task_id", "pricing_model_id"),)


class SDPSubTaskBuyingPrograms(V2MetadataBase):
    __tablename__ = "dc_sdp_sub_task_to_enab_buying"
    sub_task_id: Mapped[int] = mapped_column(
        ForeignKey("dc_sdp_typ_subtask.sub_task_id")
    )
    buying_program_type_id: Mapped[int] = mapped_column(
        ForeignKey("dc_buying_programs.buying_program_type_id"),
        name="buying_program_id",
    )

    __table_args__ = (PrimaryKeyConstraint("sub_task_id", "buying_program_id"),)
