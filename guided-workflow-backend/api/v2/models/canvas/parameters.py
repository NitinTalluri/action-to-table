from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic.v1 import Field

from . import CanvasType, Model, V2CanvasPredefinedFiles


class CurrentParametersResponse(Model):
    canvas_id: int
    dc_engagement_id: int
    canvas_name: Optional[str] = Field("", example="MyCanvas")
    canvas_type: Literal[CanvasType.current_view_canvas] = Field(
        CanvasType.current_view_canvas, const=True, example="current view canvas"
    )
    source_data_date_filter: Optional[datetime]
    files: list[V2CanvasPredefinedFiles]
    tag_ids: list[int]
    customer_files: list[int]
    collector_files: list[int]
    create_dtm: Optional[datetime]


class UnifiedParametersResponse(Model):
    canvas_id: int
    canvas_name: Optional[str] = Field("", example="MyCanvas")
    canvas_type: Literal[CanvasType.unified_view_canvas] = Field(
        CanvasType.unified_view_canvas, const=True, example="unified view canvas"
    )
    dc_engagement_id: int
    files: list[V2CanvasPredefinedFiles]
    tag_ids: list[int]
    current_snapshot_name: str | None = Field(None, example=None)
    historical_snapshot_name: str | None = Field(None, example=None)


class V2SourcedCanvasFile(Model):
    name: str
    loc: str = Field(..., example="s3://some-bucket/some-file.csv")
    date: date


class SourcedParametersResponse(Model):
    canvas_id: int
    dc_engagement_id: int
    canvas_name: Optional[str] = Field("", example="MyCanvas")
    canvas_desc: Optional[str] = Field("", example="MyCanvas Short Description")
    canvas_type: Literal["sourced file canvas"] = Field(
        CanvasType.sourced_file_canvas.value, const=True, example="sourced file canvas"
    )
    files: list[V2SourcedCanvasFile]
    create_dtm: Optional[datetime]


__all__ = [
    "CurrentParametersResponse",
    "SourcedParametersResponse",
    "UnifiedParametersResponse",
]
