from typing import Optional

from pydantic.v1 import Field, conint

from . import Model


class V2DisengagementModel(Model):
    disengagement_reason_id: conint(ge=0) = Field(
        ..., description="The disengagement reason id"
    )
    booking_contract: conint(ge=0) = Field(..., description="The booking contract id")
    notes: Optional[str] = Field(None, description="Notes about the disengagement")


class V2DisengagementResponse(V2DisengagementModel):
    dc_user_id: int = Field(
        ..., description="The user id of the user who disengaged the booking contract"
    )
