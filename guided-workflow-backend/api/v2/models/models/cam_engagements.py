from typing import Optional

from . import Model, V2RecordMetaData


class V2CamEngagementBase(Model):
    user_id: Optional[int] = None
    dc_engagement_id: Optional[int] = None


class V2CamEngagementRead(V2RecordMetaData):
    user_id: int
    dc_engagement_id: int


class V2CamEngagementWrite(Model):
    user_id: int
    dc_engagement_id: int
