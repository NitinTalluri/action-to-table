from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic.v1 import Field

from api.v2.models.stored_proc import Model


class LbType(str, Enum):
    canvas = "canvas"
    engagement = "engagement"
    user = "user"

    def __str__(self) -> str:
        return str.__str__(self)


class V2FileManagementChangeRequest(Model):
    currently_in_ts: dict = Field(default_factory=dict)
    custom_eng: dict = Field(default_factory=dict)
    custom_user: dict = Field(default_factory=dict)
    delete: dict = Field(default_factory=dict)
    common: dict = Field(default_factory=dict)


class V2ArchivedFile(Model):
    """
    Archived File
    """

    lb_type: LbType = Field(..., example="eng_94")
    liveboard_id: int = Field(..., example=127212)
    display_name: str = Field(..., example="2. - Coverage Overview")
    create_dtm: Optional[datetime] = Field(..., example="2024-04-04T14:30:48.646061")
    location: str = Field(
        ...,
        example="s3://dc-ts-file-management/prod/backup/engagement/eng_727/2023-01-17/11111.tml",
    )
    value: str = Field(..., example="eng_727")


class V2ArchivedFilesResponse(Model):
    """
    Response Returned for Archived Liveboards
    """

    engagement_id: int = Field(..., example=727)
    canvas_id: int = Field(..., example=11111)
    live_boards: list[V2ArchivedFile]
