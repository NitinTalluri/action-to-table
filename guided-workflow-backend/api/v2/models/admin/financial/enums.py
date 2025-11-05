from enum import Enum
from typing import Literal


class RevenueType(str, Enum):
    CXEA = "cxea"
    HTEC = "htec"
    COGS = "cogs"

    def __str__(self) -> str:
        return str.__str__(self)


TRevenueType = Literal["cxea", "htec", "cogs"]

__all__ = [
    "RevenueType",
    "TRevenueType",
]
