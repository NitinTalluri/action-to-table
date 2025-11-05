import json
import logging

from fastapi.encoders import jsonable_encoder
from sqlalchemy import VARCHAR, TypeDecorator

logger = logging.getLogger("api")


class JSONVarchar(TypeDecorator):
    impl = VARCHAR
    sf_size_limit = 16_777_216

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return json.loads(value)
        except Exception:
            logger.exception("Row contains invalid JSON: %r, returning None", value)
            return None

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        try:
            result = json.dumps(jsonable_encoder(value), separators=(",", ":"))
            if len(result) >= self.sf_size_limit:
                logger.warning(
                    "JSON size exceeds Snowflake limit of %d bytes", self.sf_size_limit
                )
            return result
        except (TypeError, ValueError):
            logger.exception("Invalid JSON: %r", value)
            return None


__all__ = ["JSONVarchar"]
