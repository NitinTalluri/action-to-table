from datetime import date
from typing import Literal, Optional

from pydantic.v1 import Field, validator

from .. import Model


class V2SignedOffAPI(Model):
    is_deferred: Literal[False]
    signoff_method_id: int = Field(
        ..., description="Signoff method id", alias="signoff_method", ge=0
    )
    signoff_event_id: int = Field(
        ..., description="Signoff event id", alias="signoff_event", ge=0
    )
    sign_off_identity_id: int = Field(
        ..., description="Signoff identity id", alias="sign_off_identity", ge=0
    )
    effective_date: date
    booking_contract: int = Field(..., description="Booking contract id")
    dc_engagement_id: int = Field(..., description="DC engagement id")
    dc_user_id: int = Field(..., description="DC user id")
    notes: str = Field(..., description="Notes", max_length=5000)


class V2DeferredSignOffAPI(Model):
    is_deferred: Literal[True]
    defer_signoff_reason_id: int = Field(
        ..., description="Defer signoff reason id", alias="defer_signoff_reason", ge=0
    )
    booking_contract: int = Field(..., description="Booking contract id")
    dc_engagement_id: int = Field(..., description="DC engagement id")
    dc_user_id: int = Field(..., description="DC user id")
    notes: str = Field(..., description="Notes", max_length=5000)


class V2SignOffAPIResponse(Model):
    signoff_method_id: int = Field(
        ..., description="Signoff method id", alias="signoff_method", ge=0
    )
    signoff_event_id: Optional[int] = Field(
        ..., description="Signoff event id", alias="signoff_event"
    )
    sign_off_identity_id: int = Field(
        ..., description="Signoff identity id", alias="sign_off_identity", ge=0
    )
    defer_signoff_reason_id: int = Field(
        ..., description="Defer signoff reason id", alias="defer_signoff_reason", ge=0
    )
    effective_date: Optional[date] = None
    is_deferred: bool = False
    booking_contract: int = Field(..., description="Booking contract id")
    dc_engagement_id: int = Field(..., description="DC engagement id")
    dc_user_id: int = Field(..., description="DC user id")
    notes: str = Field(..., description="Notes", max_length=5000)

    @validator("is_deferred", pre=True)
    def calculate_is_deferred(cls, v, values):
        signoff_method_id = values.get("signoff_method_id")
        sign_off_identity_id = values.get("sign_off_identity_id")
        if not all(
            (val is not None for val in (signoff_method_id, sign_off_identity_id))
        ):
            raise ValueError("Signoff method and signoff identity are required")

        return bool(sign_off_identity_id == 7 and signoff_method_id == 1)
