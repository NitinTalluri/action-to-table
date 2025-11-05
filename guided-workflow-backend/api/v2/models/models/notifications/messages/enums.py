from enum import Enum


class MessageType(str, Enum):
    text = "text"
    download = "download"
    table = "table"
    code = "code"
    parameters = "parameters"

    def __str__(self) -> str:
        return str.__str__(self)
