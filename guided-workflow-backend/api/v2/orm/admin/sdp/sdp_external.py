"""
Link SDP items to External Items
"""

from sqlalchemy import (
    Column,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
)

from api.v2.orm import V2MetadataBase

sdp_typ_task_external_items = Table(
    "dc_sdp_typ_task_external_items",
    V2MetadataBase.metadata,
    Column("ext_id", Integer, nullable=False, comment="External System Identifier"),
    Column("ext_type", String(), nullable=False),
    Column("ext_sys", String(), nullable=False),
    Column("sdp_id", Integer, nullable=False),
    PrimaryKeyConstraint("ext_id", "ext_sys", "ext_type", "sdp_id"),
    ForeignKeyConstraint(("sdp_id",), ["dc_sdp_typ_task.task_id"]),
    comment="This table stores external items linked to SDP Tasks",
)


sdp_typ_subtask_external_items = Table(
    "dc_sdp_typ_subtask_external_items",
    V2MetadataBase.metadata,
    Column("ext_id", Integer, nullable=False, comment="External System Identifier"),
    Column("ext_type", String(), nullable=False),
    Column("ext_sys", String(), nullable=False),
    Column("sdp_id", Integer, nullable=False),
    PrimaryKeyConstraint("ext_id", "ext_sys", "ext_type", "sdp_id"),
    ForeignKeyConstraint(("sdp_id",), ["dc_sdp_typ_subtask.sub_task_id"]),
    comment="This table stores external items linked to SDP SubTasks",
)

__all__ = ["sdp_typ_subtask_external_items", "sdp_typ_task_external_items"]
