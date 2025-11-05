from typing import Optional

from pydantic.v1 import conint

from . import Model, V2RecordMetaData


class V2StakeholderRead(V2RecordMetaData):
    stakeholder_id: int
    stakeholder_type_id: int
    dc_engagement_id: int
    stakeholder_name: Optional[str]
    stakeholder_email: Optional[str]
    stakeholder_phone: Optional[str]


class V2StakeholderWrite(Model):
    stakeholder_type_id: conint(ge=0)
    dc_engagement_id: Optional[int]
    stakeholder_name: Optional[str] = None
    stakeholder_email: Optional[str] = None
    stakeholder_phone: Optional[str] = None


class V2StakeholderUpdate(Model):
    stakeholder_type_id: Optional[conint(ge=0)] = None
    stakeholder_name: Optional[str] = None
    stakeholder_email: Optional[str] = None
    stakeholder_phone: Optional[str] = None
