from typing import Literal

from pydantic.v1 import conint, validator

from api.v2.models import Model, V2TagRead

from .reserved_words import RESERVED_TAGSET_NAMES, clean_strings


class V2CreateEngagementTagset(Model):
    """Create a new engagement level tagset."""

    tagset_name: str
    tagset_desc: str
    scope: Literal["Engagement"] = "Engagement"
    cardinality: Literal["1:1"] = "1:1"
    tagset_type: Literal[1] = 1
    dc_engagement_id: int

    @validator("tagset_name")
    def validate_tagset_name_not_reserved(cls, v):
        cleaned = clean_strings(v)
        if cleaned.upper() in RESERVED_TAGSET_NAMES:
            raise ValueError(f"Tagset name '{v}' is reserved")
        return cleaned

    @validator("tagset_type", pre=True)
    def validate_tagset_type_is_int(cls, v):
        match v:
            case int():
                return v
            case str():
                return int(v)
            case _:
                return v


class V2CreateGlobalTagset(Model):
    """Create a new global tagset."""

    tagset_name: str
    tagset_desc: str
    scope: Literal["Global"] = "Global"
    cardinality: Literal["1:1"] = "1:1"
    tagset_type: Literal[1] = 1
    dc_engagement_id: Literal[1] = 1

    @validator("tagset_name")
    def validate_tagset_name_not_reserved(cls, v):
        cleaned = clean_strings(v)
        if cleaned.upper() in RESERVED_TAGSET_NAMES:
            raise ValueError(f"Tagset name '{v}' is reserved")
        return cleaned


class V2TagsetResponse(Model):
    tagset_name: str
    tagset_desc: str
    scope: Literal["Engagement", "Global"]
    cardinality: Literal["1:1"] = "1:1"
    tagset_type: Literal[1] = 1
    dc_engagement_id: int
    tagset_id: int


class V2TagsetResponseWithTags(V2TagsetResponse):
    tags: list[V2TagRead]


class V2UpdateEngagementTagset(Model):
    tagset_id: int
    dc_engagement_id: conint(gt=1)
    tagset_desc: str
    scope: Literal["Engagement"] = "Engagement"


class V2UpdateGlobalTagset(Model):
    tagset_id: int
    tagset_desc: str
