import logging
from decimal import Decimal

from sqlalchemy import Float, TypeDecorator

logger = logging.getLogger("api")


class PyDecimal(TypeDecorator):
    """Values are stored as floats in Snowflake, but we want to use Decimal in Python"""

    impl = Float

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Decimal(str(value))

    def process_bind_param(self, value, dialect):
        match value:
            case None:
                return None
            case str():
                return float(value)
            case Decimal():
                return float(value)
            case int():
                return float(value)
            case float():
                return value
            case _:
                raise ValueError(f"Unsupported type: {type(value)}")


__all__ = ["PyDecimal"]
