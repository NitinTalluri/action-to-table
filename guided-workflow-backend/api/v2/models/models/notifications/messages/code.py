from typing import Literal

from pydantic.v1 import Field

from . import MessageType, Model


class CodeMessage(Model):
    type: Literal["code"] = Field(MessageType.code.value, const=True)
    data: list[dict] | dict | str
