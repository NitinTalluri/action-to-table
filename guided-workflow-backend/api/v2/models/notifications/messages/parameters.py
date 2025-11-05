from datetime import datetime
from typing import Literal, Optional

from pydantic.v1 import Field

from . import MessageType, Model


class ParametersMessage(Model):
    type: Literal["parameters"] = Field(MessageType.parameters.value, const=True)
    data: dict = Field(..., description="The human readable parameters")
    timestamp: Optional[datetime]
    form_data: Optional[dict] = Field(
        None,
        description="The form data that can be used to rehydrate the form."
        "For form metadata, keys are prefixed with `__`",
    )


class ParametersMessageCreate(ParametersMessage):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
