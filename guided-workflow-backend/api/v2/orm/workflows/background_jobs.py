from typing import TYPE_CHECKING, Optional, Union

from sqlalchemy import Column, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .. import V2MetadataBase
from ..json_varchar import JSONVarchar

if TYPE_CHECKING:
    from ...models import TUiEnum, UiEnum


class V2BackgroundJob(V2MetadataBase):
    __tablename__ = "dc_wf_background_job"
    request_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_request"), primary_key=True
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), nullable=False
    )
    dc_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_users.user_id"), nullable=False
    )
    canvas_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_canvas_hdr.canvas_id"), nullable=True
    )
    parameters = Column(JSONVarchar, comment="Data sent to external service")
    external_job_id: Mapped[str | None] = mapped_column(String(1 << 16), nullable=True)
    external_run_id: Mapped[str | None] = mapped_column(String(1 << 16), nullable=True)
    workflow_enum: Mapped[str | None] = mapped_column(String(1 << 16), nullable=True)
    workflow_data = Column(JSONVarchar, comment="Data received from client")

    notifications = relationship(
        "V2Notification",
        back_populates="background_job",
        primaryjoin="and_(V2BackgroundJob.request_id == V2Notification.request_id,"
        " V2Notification.is_deleted == 'F')",
        viewonly=True,
    )

    def __init__(
        self,
        dc_engagement_id: int,
        dc_user_id: int,
        parameters: Optional[dict],
        external_job_id: Optional[str],
        workflow_enum: Union["TUiEnum", "UiEnum", None],
        workflow_data: Optional[dict],
        created_by: str,
        external_run_id: Optional[str] = None,
        canvas_id: Optional[int] = None,
    ):
        self.dc_engagement_id = dc_engagement_id
        self.dc_user_id = dc_user_id
        self.parameters = parameters
        self.external_job_id = external_job_id
        self.external_run_id = external_run_id
        self.canvas_id = canvas_id
        self.workflow_enum = str(workflow_enum)
        self.workflow_data = workflow_data
        self.created_by = created_by
