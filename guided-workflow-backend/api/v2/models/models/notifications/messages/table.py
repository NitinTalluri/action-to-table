from typing import Literal

from pydantic.v1 import Field

from . import Model
from .enums import MessageType


class TableMessage(Model):
    type: Literal["table"] = Field(MessageType.table.value, const=True)
    data: dict = Field(
        ...,
        description="The data to be displayed in the table.",
        example={"id": 1, "name": "Collector File #1"},
    )
