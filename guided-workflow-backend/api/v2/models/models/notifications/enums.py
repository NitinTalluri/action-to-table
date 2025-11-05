from enum import Enum


class NotificationCategory(str, Enum):
    """The category of the notification."""

    RESULT = "result"
    TASK = "task"
    ERROR = "error"
    PENDING = "pending"

    def __str__(self) -> str:
        return str.__str__(self)
