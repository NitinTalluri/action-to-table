from datetime import datetime
from typing import Literal, Optional

from pydantic.v1 import Field

from . import MessageType, Model


class TextMessage(Model):
    type: Literal["text"] = Field(MessageType.text.value, const=True)
    data: str
    timestamp: Optional[datetime]


class TextMessageCreate(TextMessage):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
