from datetime import datetime
from typing import Union

from pydantic.v1 import Field

from .. import Model
from .enums import MessageType
from .download import DownloadMessage, DownloadData
from .table import TableMessage
from .code import CodeMessage
from .text import TextMessage, TextMessageCreate
from .parameters import ParametersMessage, ParametersMessageCreate
from ...base import isoformat_utc


class CreateMessage(Model):
    __root__: Union[
        DownloadMessage,
        TableMessage,
        CodeMessage,
        TextMessageCreate,
        ParametersMessageCreate,
    ] = Field(discriminator="type")

    class Config:
        smart_union = True

    def dict(self, **kwargs):
        return self.__root__.dict(**kwargs)


class Message(Model):
    __root__: Union[
        DownloadMessage, TableMessage, CodeMessage, TextMessage, ParametersMessage
    ] = Field(discriminator="type")

    class Config:
        smart_union = True
        json_encoders = {datetime: isoformat_utc}

    def dict(self, **kwargs):
        return self.__root__.dict(**kwargs)


TCreateMessage = Union[
    DownloadMessage,
    TableMessage,
    CodeMessage,
    TextMessageCreate,
    ParametersMessageCreate,
]

TMessage = Union[
    DownloadMessage, TableMessage, CodeMessage, TextMessage, ParametersMessage
]


__all__ = [
    "CodeMessage",
    "CreateMessage",
    "DownloadData",
    "DownloadMessage",
    "Message",
    "MessageType",
    "ParametersMessage",
    "ParametersMessageCreate",
    "TCreateMessage",
    "TMessage",
    "TableMessage",
    "TextMessage",
    "TextMessageCreate",
]
