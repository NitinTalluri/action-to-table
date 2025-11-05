"""
These are ported from `common_prefect_next`.
"""

from enum import Enum
from typing import Literal, Optional, Union

from .. import TEnv
from . import Model


class EventStage(str, Enum):
    requested = "requested"

    def __str__(self) -> str:
        return str.__str__(self)


class CanvasEventType(str, Enum):
    canvas_delete = "datacanvas.canvas.delete"

    def __str__(self) -> str:
        return str.__str__(self)


class ThoughtSpotLiveboardEventType(str, Enum):
    manage_liveboards = "thoughtspot.liveboards.manage"
    discover_liveboards = "thoughtspot.liveboards.discover"

    def __str__(self) -> str:
        return str.__str__(self)


class EngagementEventType(str, Enum):
    engagement_share = "datacanvas.engagement.share"
    engagement_view_refresh = "datacanvas.engagement.refresh"

    def __str__(self) -> str:
        return str.__str__(self)


TEventType = Union[CanvasEventType, ThoughtSpotLiveboardEventType, EngagementEventType]


class ShareEngagementEventPayload(Model):
    env: TEnv
    dc_user_id: int
    dc_engagement_id: int
    notification_id: int
    request_id: int
    shared_with_dc_user_id: int


class RefreshEngagementEventPayload(Model):
    env: TEnv
    dc_user_id: int
    dc_engagement_id: int
    notification_id: int
    request_id: int


class DeleteCanvasEventPayload(Model):
    env: TEnv
    canvas_id: int
    dc_user_id: int
    dc_engagement_id: int
    notification_id: int
    request_id: Optional[int]


class ManageLiveboardsEventPayload(Model):
    env: TEnv
    canvas_id: int
    dc_user_id: int
    dc_engagement_id: int
    notification_id: int
    request_id: int


class DiscoverLiveboardsEventPayload(Model):
    env: TEnv
    canvas_id: int
    dc_user_id: int
    dc_engagement_id: int
    notification_id: int
    request_id: int


TEventPayload = Union[
    DeleteCanvasEventPayload,
    ManageLiveboardsEventPayload,
    ShareEngagementEventPayload,
    DiscoverLiveboardsEventPayload,
    RefreshEngagementEventPayload,
]
