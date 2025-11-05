import datetime
from typing import TYPE_CHECKING, Union

from snowflake.sqlalchemy import TIMESTAMP_TZ
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    column,
    table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.v2.orm import V2Base

from . import V2MetadataBase
from .json_varchar import JSONVarchar

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.v2.models import V3CanvasCreate, V3CanvasRebuild


class V2Canvas(V2MetadataBase):
    __tablename__ = "dc_canvas_hdr"
    canvas_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_canvas"), primary_key=True
    )
    canvas_name: Mapped[str] = mapped_column(String)
    canvas_desc: Mapped[str] = mapped_column(String)
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    canvas_status: Mapped[str] = mapped_column(String, default="running")
    file_path: Mapped[str] = mapped_column(String)
    file_upload_status: Mapped[str] = mapped_column(String)
    canvas_type: Mapped[str] = mapped_column(String, default="unified view canvas")
    source_data_date_filter: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    notification_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_wf_notification.notification_id"), nullable=True
    )
    current_snapshot_name: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="References DC_SNAPSHOT_DATA.NAME"
    )
    historical_snapshot_name: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="References DC_SNAPSHOT_DATA.NAME"
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="TRUE")
    rowcount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engagement = relationship("V2Engagement", back_populates="canvases")

    @classmethod
    def create_from_model(
        cls,
        model: "V3CanvasCreate",
        logged_user: str,
        session: "Session",
    ):
        db_model = cls(
            canvas_name=model.canvas_name,
            canvas_desc=model.canvas_desc,
            dc_engagement_id=model.dc_engagement_id,
            canvas_type=str(model.canvas_type),
            source_data_date_filter=None,
            current_snapshot_name=model.current_snapshot_name,
            historical_snapshot_name=model.historical_snapshot_name,
            created_by=logged_user,
        )
        session.add(db_model)
        session.commit()
        session.refresh(db_model)
        return db_model

    def update_from_model(
        self,
        model: "V3CanvasRebuild",
        logged_user: str,
        session: "Session",
    ) -> "V2Canvas":
        self.canvas_name = model.canvas_name
        self.canvas_desc = model.canvas_desc
        self.canvas_type = str(model.canvas_type)
        self.current_snapshot_name = model.current_snapshot_name
        self.historical_snapshot_name = model.historical_snapshot_name
        self.updated_by = logged_user
        self.update_dtm = datetime.datetime.utcnow()
        session.add(self)
        session.commit()
        session.refresh(self)
        return self


class V2DataSource(V2Base):
    __tablename__ = "dc_data_sources"
    remote_system_customer_identifier: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    file_name: Mapped[str] = mapped_column(String)
    folder_path: Mapped[str] = mapped_column(String)
    file_source: Mapped[str] = mapped_column(String)
    file_type: Mapped[str] = mapped_column(String)
    num_records: Mapped[int] = mapped_column(Integer)
    date_sourced: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    last_processed_date: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    remote_system: Mapped[str] = mapped_column(String, primary_key=True)
    file_number: Mapped[int] = mapped_column(Integer)
    display_name: Mapped[str] = mapped_column(String)
    request_id: Mapped[int] = mapped_column(Integer)


class V2SnapshotData(V2MetadataBase):
    __tablename__ = "dc_snapshot_data"
    name: Mapped[str] = mapped_column(String, primary_key=True)
    snapshot_date: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP_TZ, nullable=False
    )
    snapshot_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )

    def __init__(
        self,
        name: str,
        snapshot_date: datetime.datetime,
        snapshot_version: int,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.name = name
        self.snapshot_date = snapshot_date
        self.snapshot_version = snapshot_version


canvas_create_run_log_table = table(
    "dc_canvas_create_run_log",
    column("canvas_id", Integer),
    column("input_parameters", JSONVarchar),
    column("run_date", DateTime),
    column("flow_run_id", String),
    column("created_by", String),
    column("create_dtm", DateTime),
    column("update_dtm", DateTime),
    column("updated_by", String),
    column("is_deleted", String),
)


__all__ = [
    "V2Canvas",
    "V2DataSource",
    "V2SnapshotData",
    "canvas_create_run_log_table",
]
