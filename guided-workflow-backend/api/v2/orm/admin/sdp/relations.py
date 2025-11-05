from sqlalchemy import ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase


class SDPTaskToSubTask(V2MetadataBase):
    __tablename__ = "dc_sdp_b_task_sub_task"

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("dc_sdp_typ_task.task_id"))
    sub_task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_sdp_typ_subtask.sub_task_id")
    )

    __table_args__ = (PrimaryKeyConstraint("task_id", "sub_task_id"),)


class SDPTaskToDeliverable(V2MetadataBase):
    __tablename__ = "dc_sdp_b_task_to_deliverable"

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("dc_sdp_typ_task.task_id"))
    deliverable_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_sdp_typ_deliverable.deliverable_id")
    )

    __table_args__ = (PrimaryKeyConstraint("task_id", "deliverable_id"),)
