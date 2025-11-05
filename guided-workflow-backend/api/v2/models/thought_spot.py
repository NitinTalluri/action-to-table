from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic.v1 import Field, conint, root_validator, validator

from . import (
    ExtractState,
    Model,
    V2ConfigTagStrategy,
    V2RecordMetaData,
    V2TagAction,
)


class V2ThoughtSpotExtractType(str, Enum):
    STANDARD = "STANDARD"
    EXTENDED = "EXTENDED"
    ADVANCED = "ADVANCED"
    EMEA = "EMEA"

    def __str__(self) -> str:
        return str.__str__(self)


class V2ThoughtSpotTask(V2RecordMetaData):
    thoughtspot_id: Optional[int]
    tag_id: Optional[int]
    tagset_id: Optional[int]
    comment: Optional[str]
    canvas_id: Optional[int]
    user_action: Optional[str]
    count_instances: Optional[int]
    list_of_instances: Optional[str]
    file_location: Optional[str]


class V2ThoughtSpotInstanceRequestsModel(Model):
    tag_names: Optional[list[str]]
    tag_ids: Optional[list[int]]
    tagset_names: Optional[list[str]]
    tagset_ids: Optional[list[int]]
    thoughtspot_id: int
    canvas_id: int
    canvas: str
    dc_engagement_id: int
    count_instances: int
    comment: Optional[str]
    create_dtm: Optional[datetime]
    created_by: Optional[str]
    user_action: V2TagAction
    extract_state: ExtractState


class V2ThoughtSpotTaskList(Model):
    idList: Optional[List[int]]
    columnsToExtract: V2ThoughtSpotExtractType
    dc_engagement_id: int = Field(alias="engagementId")


class RunEntry(Model):
    thoughtspot_id: conint(ge=0)
    config_strategy: Optional[V2ConfigTagStrategy] = None


class V2ThoughtSpotTaskListWrite(Model):
    requests: list[RunEntry]

    @root_validator()
    def check_requests(cls, values):
        requests = values.get("requests")
        if len(requests) != len({r.thoughtspot_id for r in requests}):
            raise ValueError("Duplicate thoughtspot_id in requests")
        return values


class V2ThoughtSpotTaskListResult(Model):
    user_action: V2TagAction
    success: bool
    thoughtspot_id: int
    dc_engagement_id: int
    tag_ids: Optional[list[int]] = None
    tagset_ids: Optional[list[int]] = None
    canvas_id: Optional[int] = None


class V2ThoughtSpotTaskListResults(Model):
    results: list[V2ThoughtSpotTaskListResult]


class V2ThoughtSpotTaskContext(Model):
    answer_url: Optional[str] = Field(default=None, alias="answerUrl")
    action_type: Optional[str] = Field(default=None, alias="actionType")
    viz_name: Optional[str] = Field(default=None, alias="vizName")
    type: Optional[str] = Field(default=None, alias="type")


class V2ThoughtSpotTaskUploadWrite(Model):
    canvas_id: int
    comment: Optional[str] = None
    engagement_id: int
    tag_ids: list[int] = Field(default_factory=list)
    tagset_ids: list[int] = Field(default_factory=list)
    user_action: V2TagAction
    context: Optional[V2ThoughtSpotTaskContext] = None

    @validator("tag_ids", "tagset_ids", pre=True)
    def ensure_list(cls, v):
        match v:
            case None:
                return []
            case _:
                return v

    @root_validator
    def check_tags(cls, values):
        user_action = values.get("user_action")
        if user_action == V2TagAction.extract:
            return values
        tag_ids = values.get("tag_ids")
        tagset_ids = values.get("tagset_ids")
        if not tag_ids and not tagset_ids:
            raise ValueError(
                "Either tag_ids or tagset_ids must be provided, unless user_action is 'extract'"
            )
        return values


class V2ThoughtSpotRefreshTagsRequest(Model):
    dc_engagement_id: int = Field(..., description="Engagement ID")
    canvas_id: int = Field(..., description="Canvas ID to refresh")


class V2ThoughtSpotDiscoveryRequest(V2ThoughtSpotRefreshTagsRequest): ...


class V2ThoughtSpotDeleteTasksRequest(Model):
    """Request to delete one or more thoughtspot tasks."""

    thoughtspot_ids: list[int] = Field(
        ..., description="List of thoughtspot task IDs to delete"
    )


class V2ThoughtSpotDeleteTasksResponse(V2ThoughtSpotDeleteTasksRequest):
    """Return response for delete thoughtspot tasks."""

    ...


class V2WriteTagInstances(Model):
    tag_id: conint(ge=0) = Field(default=None, title="Tag ID")
    instance_ids: list[conint(ge=0)] = Field(default=None, title="Instance IDs")
    engagement_id: conint(ge=0) = Field(default=None, title="Engagement ID")
    comment: str = Field(default="", title="Comment")


class V2WriteTags(Model):
    tag_ids: list[conint(ge=0)] = Field(..., title="Tag IDs", example=[100])
    engagement_id: conint(ge=0) = Field(..., title="Engagement ID", example=94)
    config_strategy: Optional[V2ConfigTagStrategy] = Field(
        None, title="Config Strategy", example="config-all"
    )
    comment: str = Field(default="", title="Comment")

    @root_validator()
    def check_tag_ids(cls, values):
        tag_ids = values.get("tag_ids")
        if not tag_ids:
            raise ValueError("tag_ids must be provided")
        if len(tag_ids) != len(set(tag_ids)):
            raise ValueError("Duplicate tag_ids found")
        return values


class TagsetTagModel(Model):
    tagset_id: int
    tag_id: int


class V2WriteUntagInstances(Model):
    tagset_ids: list[conint(ge=0)] = Field(default=None, title="Tagset IDs")
    instance_ids: list[conint(ge=0)] = Field(default=None, title="Instance IDs")
    engagement_id: conint(ge=0) = Field(default=None, title="Engagement ID")


class V2WriteUntagInstancesResponse(Model):
    tagset_ids: list[conint(ge=0)] = Field(default=None, title="Tagset IDs")
    instance_ids: list[conint(ge=0)] = Field(
        default=None, alias="instances", title="Instance IDs"
    )
    engagement_id: conint(ge=0) = Field(
        default=None, alias="engagementId", title="Engagement ID"
    )


class V2WriteTagInstancesResponse(Model):
    success: bool = True
    tag_ids: list[conint(ge=0)] = Field(default=None, alias="tagId", title="Tag ID")
    instance_ids: list[conint(ge=0)] = Field(
        default=None, alias="instances", title="Instance IDs"
    )


__all__ = [
    "TagsetTagModel",
    "V2ThoughtSpotDeleteTasksRequest",
    "V2ThoughtSpotDeleteTasksResponse",
    "V2ThoughtSpotDiscoveryRequest",
    "V2ThoughtSpotExtractType",
    "V2ThoughtSpotInstanceRequestsModel",
    "V2ThoughtSpotRefreshTagsRequest",
    "V2ThoughtSpotTask",
    "V2ThoughtSpotTaskContext",
    "V2ThoughtSpotTaskList",
    "V2ThoughtSpotTaskListResult",
    "V2ThoughtSpotTaskListResults",
    "V2ThoughtSpotTaskListWrite",
    "V2ThoughtSpotTaskUploadWrite",
    "V2WriteTagInstances",
    "V2WriteTagInstancesResponse",
    "V2WriteTags",
    "V2WriteUntagInstances",
    "V2WriteUntagInstancesResponse",
]
