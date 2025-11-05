from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Literal

from pydantic.v1 import Field

from api.v2.models import CanvasStatus, CanvasType, Model

from .parameters import (
    CurrentParametersResponse,
    SourcedParametersResponse,
    UnifiedParametersResponse,
)

logger = logging.getLogger("api")


class V2Pinboard(Model):
    guid: str = Field(..., example="f313b165-d692-4d79-8374-4cdef2ea5538")
    pinboard_name: str | None = Field("", example="MyPinboard")


class V2CanvasRead(Model):
    canvas_desc: str | None = Field("", example="MyCanvas")
    canvas_id: int = Field(..., example=5000)
    canvas_name: str = Field(..., example="MyCanvas")
    canvas_status: CanvasStatus | str = Field("success", example="success")
    canvas_type: CanvasType = Field(..., example="unified view canvas")
    create_dtm: datetime = Field(..., example="2023-01-01T00:00:00")
    current_snapshot_name: str | None = Field(None, example=None)
    historical_snapshot_name: str | None = Field(None, example="Snapshot 2024_12_20")
    dc_engagement_id: int = Field(..., example=94)
    pinboards: list[V2Pinboard] = Field(
        default_factory=list,
        description="List of pinboards in the canvas",
    )
    extract_actions: int = Field(
        0,
        example=10000,
        description="Number of extract actions associated with the canvas",
    )
    tag_actions: int = Field(
        0,
        example=10000,
        description="Number of tag actions associated with the canvas",
    )
    notification_id: int | None = Field(
        None,
        example=10000,
        description="Most recent notification ID of the canvas",
    )
    enabled: bool = Field(
        default=True,
        example=True,
        description="Whether the canvas is enabled for data view output",
    )


class V2CanvasEvidenceUploadResponse(Model):
    request_id: int
    effective_date: date
    source: str | None
    note: str | None
    file_name_id: int
    dc_engagement_id: int
    type: Literal["collector", "customer"]
    file_name: str


class V2CanvasParametersResponse(Model):
    __root__: (
        CurrentParametersResponse
        | SourcedParametersResponse
        | UnifiedParametersResponse
    ) = Field(
        discriminator="canvas_type",
    )


class V2SnapshotDataModel(Model):
    """Model for `api.v2.orm.canvas.V2SnapshotData`"""

    name: str
    snapshot_date: datetime


class V2SnapshotDataResponse(Model):
    __root__: list[V2SnapshotDataModel] = Field(
        ...,
        example=[
            {"name": "FY2024 Snapshot", "snapshot_date": "2024-01-01"},
            {"name": "Q2FY2024 Snapshot", "snapshot_date": "2024-04-01"},
        ],
    )


__all__ = [
    "V2CanvasEvidenceUploadResponse",
    "V2CanvasParametersResponse",
    "V2CanvasRead",
    "V2SnapshotDataModel",
    "V2SnapshotDataResponse",
]
