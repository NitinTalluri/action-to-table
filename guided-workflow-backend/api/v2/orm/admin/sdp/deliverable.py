from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    PrimaryKeyConstraint,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase

if TYPE_CHECKING:
    from api.v2.models import AdminSDPDeliverableCreate, AdminSDPDeliverableEdit


if TYPE_CHECKING:
    from sqlmodel import Session


class SDPDeliverable(V2MetadataBase):
    """
    A deliverable is a tangible output that is part of the service delivery plan.

    For example:
        - A Review of Installed Equipment
            - Subtasks:
                - Generate some report
                - Review the report and submit any findings
                - Generate a final report
                - User confirmation

    """

    __tablename__ = "dc_sdp_typ_deliverable"

    deliverable_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_sdp"), primary_key=True
    )
    deliverable_desc: Mapped[str] = mapped_column(
        String(5000), default="", unique=True, nullable=False
    )
    deliverable_doc_link: Mapped[str] = mapped_column(
        String(5000), default="", nullable=False, server_default=""
    )

    @classmethod
    def create_from_model(
        cls, model: "AdminSDPDeliverableCreate", logged_user, session: "Session"
    ):
        db_model = cls(
            deliverable_desc=model.deliverable_desc,
            deliverable_doc_link=model.deliverable_doc_link,
        )
        session.add(db_model)
        session.commit()
        session.refresh(db_model)

        return db_model

    def update_from_model(
        self, model: "AdminSDPDeliverableEdit", logged_user, session: "Session"
    ):
        self.deliverable_desc = model.deliverable_desc
        self.deliverable_doc_link = model.deliverable_doc_link
        self.updated_by = logged_user
        session.add(self)
        session.commit()
        session.refresh(self)
        return self


class SDPAbstractDeliverable(V2MetadataBase):
    """
    An abstract deliverable is an intangible part of the service delivery plan.

    It will not have associated tasks or subtasks or even booking or engagements.

    Instead, it will be used solely for time tracking purposes. Applicable entries are
    those such as 'PTO', 'Innovation', 'Training', etc.

    When querying for time tracking entries, we will join this table so that these entries
    can be included in the time tracking report.
    """

    __tablename__ = "dc_sdp_typ_abstract_deliverable"

    abstract_deliverable_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_sdp")
    )
    abstract_deliverable_desc: Mapped[str] = mapped_column(
        String(5000), default="", server_default="", nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint("abstract_deliverable_id"),
        UniqueConstraint("abstract_deliverable_desc"),
    )
