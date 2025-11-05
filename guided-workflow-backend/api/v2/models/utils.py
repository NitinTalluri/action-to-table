import logging
from typing import Generic, Iterable, Optional, Type, TypeVar, get_args, get_origin

from pydantic.v1 import BaseModel

logger = logging.getLogger("api")


T = TypeVar("T", bound=Iterable[BaseModel])


def _get_collection_type(type_: Type[T]):
    origin = get_origin(type_)
    if not origin:
        logger.error("Type %r is not a collection type", type_)
        return list
    return origin


def safe_parse_collection(type_: Type[T], obj: Optional[Iterable]) -> T:
    collection_type = _get_collection_type(type_)
    model_class = get_args(type_)[0]
    parsed = []
    if obj is None:
        return collection_type(parsed)
    for item in obj:
        try:
            parsed.append(model_class.parse_obj(item))
        except Exception as e:
            logger.error("Failed to parse item %r as %r: %r", item, model_class, e)

    return collection_type(parsed)


def safe_parse_orm_collection(type_: Type[T], obj: Optional[Iterable]) -> T:
    collection_type = _get_collection_type(type_)
    model_class = get_args(type_)[0]
    parsed = []
    if obj is None:
        return collection_type(parsed)
    for item in obj:
        try:
            parsed.append(model_class.from_orm(item))
        except Exception as e:
            logger.error("Failed to parse item %r as %r: %r", item, model_class, e)

    return collection_type(parsed)


S = TypeVar("S")


class SingletonMeta(type, Generic[S]):
    _instances: dict[type, S] = {}

    def __call__(cls: type[S], *args, **kwargs) -> S:
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


__all__ = ["SingletonMeta", "safe_parse_collection", "safe_parse_orm_collection"]
