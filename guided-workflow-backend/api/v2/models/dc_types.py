from typing import Optional

from pydantic.v1 import validator

from . import Model, TrueFalse


class V2TypeMapping(Model):
    id: int
    value: str
    is_deleted: bool
    extra: Optional[dict] = None

    @validator("is_deleted", pre=True, always=True)
    def validate_is_deleted(cls, v: Optional[TrueFalse]) -> bool:
        if isinstance(v, str):
            if v.lower() in {"y", "yes", "t", "true"}:
                return True
            elif v.lower() in {"n", "no", "f", "false"}:
                return False
            else:
                raise ValueError(f"Cannot convert {v} to boolean")
        elif isinstance(v, bool):
            return v
        try:
            return bool(v)
        except ValueError as e:
            raise ValueError(f"Cannot convert {v} to boolean") from e


class V2TableTypeMapping(Model):
    table_name: str
    mappings: list[V2TypeMapping]
