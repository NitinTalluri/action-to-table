from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    Sequence,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import TextualSelect
    from sqlmodel import Session

    from api.v2.models import AdminSDPTaskCreate, AdminSDPTaskEdit


class SDPTask(V2MetadataBase):
    """
    A task is a high-level activity that is part of the service delivery plan. It is a collection of sub-tasks.

    Notes
    -----
    We enforce some business logic for due_date_offset and cycle_iterator_id.

    If the cycle_iterator_id is a direct/one-time cycle, then due_date_offset can be non-zero.

    Otherwise, due_date_offset must be zero.
    """

    __tablename__ = "dc_sdp_typ_task"

    _direct_cycle_pattern = "%ONE%TIME%"

    task_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_sdp"), primary_key=True
    )
    task_desc: Mapped[str] = mapped_column(String(5000), nullable=False)
    task_desc_long: Mapped[str | None] = mapped_column(String(20000))
    task_doc_link: Mapped[str] = mapped_column(
        String(5000), default="", nullable=False, server_default=""
    )
    hours: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    frequency: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    due_date_offset: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    anchor_date_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_sdp_typ_anchor_date.anchor_date_id"), nullable=False
    )
    cycle_iterator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dc_sdp_typ_anchor_date_iterator.iterator_id"),
        nullable=False,
    )

    @classmethod
    def make_direct_type_iterator_query(cls, iterator_id: int) -> "TextualSelect":
        cycle_query = (
            text(
                """
            SELECT iterator_id, ITERATOR_DATE_NAME ILIKE :pattern AS is_direct
            FROM dc_sdp_typ_anchor_date_iterator
            WHERE iterator_id = :iterator_id
            AND IS_DELETED = 'F'
            LIMIT 1
            """
            )
            .bindparams(pattern=cls._direct_cycle_pattern, iterator_id=iterator_id)
            .columns(iterator_id=Integer, is_direct=Boolean)
        )
        return cycle_query

    @classmethod
    def create_from_model(
        cls, model: "AdminSDPTaskCreate", logged_user: str, session: "Session"
    ):
        cycle_query = cls.make_direct_type_iterator_query(model.cycle_iterator_id)
        db_cycle_row = session.execute(cycle_query).one_or_none()
        if not db_cycle_row:
            raise HTTPException(
                status_code=404,
                detail="Cycle iterator not found",
            )
        is_direct = db_cycle_row.is_direct

        db_model = cls(
            task_desc=model.task_desc,
            task_desc_long=model.task_desc_long,
            task_doc_link=model.task_doc_link,
            hours=model.hours,
            frequency=model.frequency,
            due_date_offset=model.due_date_offset if is_direct else 0,
            anchor_date_id=model.anchor_date_id,
            cycle_iterator_id=model.cycle_iterator_id,
            created_by=logged_user,
        )
        session.add(db_model)
        session.commit()
        session.refresh(db_model)

        return db_model

    def update_from_model(
        self, model: "AdminSDPTaskEdit", logged_user, session: "Session"
    ):
        cycle_query = self.make_direct_type_iterator_query(model.cycle_iterator_id)
        db_cycle_row = session.execute(cycle_query).one_or_none()
        if not db_cycle_row:
            raise HTTPException(
                status_code=404,
                detail="Cycle iterator not found",
            )
        is_direct = db_cycle_row.is_direct

        self.task_desc = model.task_desc
        self.task_doc_link = model.task_doc_link
        self.task_desc_long = model.task_desc_long
        self.hours = model.hours
        self.frequency = model.frequency
        self.anchor_date_id = model.anchor_date_id
        self.cycle_iterator_id = model.cycle_iterator_id
        self.updated_by = logged_user
        self.due_date_offset = model.due_date_offset if is_direct else 0
        session.add(self)
        session.commit()
        session.refresh(self)
        return self
