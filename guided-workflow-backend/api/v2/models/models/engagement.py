from __future__ import annotations

from typing import Optional

from pydantic.v1 import conint, validator

from . import Model, TrueFalse, V2RecordMetaData


class V2EngagementBase(Model):
    engagement_name: Optional[str] = None
    is_sfc: Optional[TrueFalse] = None
    sfc_agreement_type: Optional[int] = None
    is_cxea: Optional[TrueFalse] = None
    is_software: Optional[TrueFalse] = None
    notes: Optional[str] = None


class V2EngagementRead(V2RecordMetaData):
    dc_engagement_id: int
    engagement_name: Optional[str]
    is_sfc: Optional[TrueFalse]
    is_cxea: Optional[TrueFalse]
    is_software: Optional[TrueFalse]
    sfc_agreement_type: Optional[int]
    notes: Optional[str]

    @validator("is_sfc", "is_cxea", "is_software", pre=True)
    def parse_truthy(cls, v):
        """
        Coerce values like 'Y', 'Yes', 'T', 'True' to TrueFalse
        """
        if isinstance(v, str):
            v = v.lower()
            if v in {"y", "yes", "t", "true"}:
                return TrueFalse.T
            elif v in {"n", "no", "f", "false"}:
                return TrueFalse.F
        return v


class V2EngagementUpdate(V2EngagementBase):
    engagement_name: Optional[str] = None
    is_sfc: Optional[TrueFalse] = None
    is_cxea: Optional[TrueFalse] = None
    is_software: Optional[TrueFalse] = None
    sfc_agreement_type: Optional[conint(gt=0)] = None
    notes: Optional[str] = None


class V2EngagementCreate(V2EngagementBase):
    engagement_name: str
    is_sfc: Optional[TrueFalse]
    is_cxea: Optional[TrueFalse]
    is_software: Optional[TrueFalse]
    sfc_agreement_type: Optional[conint(gt=0)]
    notes: Optional[str]


class V2EngagementDelete(Model):
    dc_engagement_id: int


class V2UserRead(Model):
    cisco_cco_id: Optional[str]
    user_title: Optional[str]
    user_id: Optional[int]
