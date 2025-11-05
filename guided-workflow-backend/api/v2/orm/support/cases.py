import datetime
import logging

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    and_,
    case,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, column_property, mapped_column

from api.v2.models.enums import V2SupportStatus

from ..json_varchar import JSONVarchar
from . import V2MetadataBase

logger = logging.getLogger("api")


class SupportCase(V2MetadataBase):
    __tablename__ = "dc_support_cases"

    case_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("seq_dc_generic"),
        primary_key=True,
        server_default=Sequence("seq_dc_generic").next_value(),
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("dc_users.user_id"))
    path: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String)
    comments: Mapped[str] = mapped_column(String)
    support_evidence = Column(JSONVarchar)
    resolved_dtm: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    agent_comments: Mapped[str] = mapped_column(String)
    agent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_users.user_id"), nullable=True
    )
    root_cause_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_typ_root_causes.root_cause_id"), nullable=True
    )
    status = column_property(
        case(
            (
                and_(agent_id.is_(None), resolved_dtm.is_(None)),
                V2SupportStatus.unassigned.value,
            ),
            (
                and_(agent_id.isnot(None), resolved_dtm.is_(None)),
                V2SupportStatus.assigned.value,
            ),
            (resolved_dtm.isnot(None), V2SupportStatus.closed.value),
            else_=V2SupportStatus.unassigned.value,
        ).label("status")
    )

    @hybrid_property
    def is_closed(self):
        return self.resolved_dtm != None

    @is_closed.expression
    def is_closed(cls):
        return cls.resolved_dtm.isnot(None)


class RootCauseType(V2MetadataBase):
    __tablename__ = "dc_typ_root_causes"

    root_cause_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    root_cause: Mapped[str] = mapped_column(String, unique=True)
