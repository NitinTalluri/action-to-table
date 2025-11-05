from typing import TYPE_CHECKING, Literal, Optional

from pydantic.v1 import Field, PrivateAttr, validator

from api.v2.models import Model, V2EngagementLinks
from api.v2.models.enums import CanvasType, V2CanvasPredefinedFileNames

if TYPE_CHECKING:
    from api.v2.models import V2CanvasEvidenceUploadResponse


class V2CanvasPredefinedFiles(Model):
    name: V2CanvasPredefinedFileNames = Field(..., example="SMART_ACCOUNT")

    def __hash__(self):
        return hash(self.name)


class V3CanvasCreate(Model):
    canvas_name: str
    canvas_desc: str = ""
    canvas_type: Literal[CanvasType.unified_view_canvas] = Field(
        CanvasType.unified_view_canvas, const=True
    )
    dc_engagement_id: int
    files: list[V2CanvasPredefinedFiles] = Field(
        ..., description="Referred to as 'extensions' in the Prefect API"
    )
    tag_ids: list[int]
    current_snapshot_name: str | None = Field(
        None,
        description="The name of the snapshot to treat as the current snapshot."
        " If historical_snapshot_name is not None, this field defaults to the latest snapshot found.",
    )
    historical_snapshot_name: str | None = Field(
        ...,
        description="The name of the snapshot to treat as the historical snapshot."
        " If this field is not None, current_snapshot_name must not be None.",
    )
    customer_request_ids: list[int]
    collector_request_ids: list[int]

    _engagement_links: Optional[V2EngagementLinks] = PrivateAttr()
    _engagement_evidence_uploads: list["V2CanvasEvidenceUploadResponse"] = PrivateAttr(
        default_factory=list
    )

    @validator("files")
    def validate_files(cls, v) -> list[V2CanvasPredefinedFiles]:
        # We still accept but will internally remove the V2CanvasPredefinedFileNames.BASELINE_TAGS
        filtered = [
            file for file in v if file.name != V2CanvasPredefinedFileNames.baseline_tags
        ]
        seen = set()
        seen_add = seen.add
        return [
            file for file in filtered if not (file.name in seen or seen_add(file.name))
        ]

    class Config:
        schema_extra = {
            "examples": [
                {
                    "canvas_name": "My Canvas",
                    "canvas_desc": "A description of my canvas",
                    "dc_engagement_id": 94,
                    "files": [{"name": "ACAT"}, {"name": "MCE"}],
                    "tag_ids": [],
                    "current_snapshot_name": None,
                    "historical_snapshot_name": "Snapshot 2024_12_20",
                    "customer_request_ids": [],
                    "collector_request_ids": [],
                }
            ]
        }


class V3CanvasRebuild(V3CanvasCreate):
    canvas_id: int

    class Config:
        schema_extra = {
            "examples": [
                {
                    "canvas_id": 1000,
                    "canvas_name": "My Canvas",
                    "canvas_desc": "A description of my canvas",
                    "dc_engagement_id": 94,
                    "files": ["ACAT", "MCE"],
                    "tag_ids": [],
                    "current_snapshot_name": None,
                    "historical_snapshot_name": "Snapshot 2024_12_20",
                    "customer_request_ids": [],
                    "collector_request_ids": [],
                }
            ]
        }


__all__ = [
    "V2CanvasPredefinedFiles",
    "V3CanvasCreate",
    "V3CanvasRebuild",
]
