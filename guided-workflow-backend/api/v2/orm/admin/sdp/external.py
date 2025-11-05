from sqlalchemy import (
    Column,  # Keep for Table definition
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase


class ExternalItem(V2MetadataBase):
    __tablename__ = "dc_sdp_external_items"

    ext_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="External System Identifier",
    )
    ext_sys: Mapped[str] = mapped_column(
        String(),
        nullable=False,
        comment="External System Enum (openproject)",
    )
    ext_type: Mapped[str] = mapped_column(
        String(),
        nullable=False,
        comment="External System Type Enum (task, t_task, subtask, t_subtask, etc)",
    )
    ext_name: Mapped[str] = mapped_column(
        String(), nullable=False, comment="Name of the External Item"
    )

    __table_args__ = (
        PrimaryKeyConstraint(ext_id, ext_type, ext_sys),
        {
            "comment": "This table stores external items linked to DataCanvas via the SDP Interface"
        },
    )


class ExternalCollection(V2MetadataBase):
    __tablename__ = "dc_sdp_external_collections"

    ext_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="External System Collection Identifier",
    )
    ext_type: Mapped[str] = mapped_column(
        String(),
        nullable=False,
        comment="External System Collection Type",
    )
    ext_sys: Mapped[str] = mapped_column(
        String(),
        nullable=False,
        comment="External System Enum (openproject)",
    )
    ext_name: Mapped[str] = mapped_column(
        String(), nullable=False, comment="Name of the External Collection"
    )

    __table_args__ = (
        PrimaryKeyConstraint(ext_id, ext_type, ext_sys),
        {
            "comment": "Generic table to track external collections of items. I.e. OpenProject Boards and their Tasks"
        },
    )


ext_collection_relationships = Table(
    "dc_sdp_external_collection_items",
    V2MetadataBase.metadata,
    Column("id", Integer, primary_key=True),
    Column("ext_collection_id", Integer, nullable=False),
    Column("ext_collection_type", String(), nullable=False),
    Column("ext_collection_sys", String(), nullable=False),
    Column("ext_item_id", Integer, nullable=False),
    Column("ext_item_type", String(), nullable=False),
    Column("ext_item_sys", String(), nullable=False),
    ForeignKeyConstraint(
        ("ext_collection_id", "ext_collection_type", "ext_collection_sys"),
        [
            ExternalCollection.ext_id,
            ExternalCollection.ext_type,
            ExternalCollection.ext_sys,
        ],
    ),
    ForeignKeyConstraint(
        ("ext_item_id", "ext_item_type", "ext_item_sys"),
        [
            ExternalItem.ext_id,
            ExternalItem.ext_type,
            ExternalItem.ext_sys,
        ],
    ),
    comment="This table links external items to external collections",
)

__all__ = [
    "ExternalCollection",
    "ExternalItem",
    "ext_collection_relationships",
]
