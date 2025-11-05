import json
import logging
import random
from datetime import datetime
from enum import Enum
from itertools import zip_longest
from math import ceil
from typing import Any, Generic, TypeVar
from zoneinfo import ZoneInfo

from fastapi.encoders import jsonable_encoder
from pydantic.v1 import BaseModel

UTC = ZoneInfo("UTC")
DataT = TypeVar("DataT")

logger = logging.getLogger("api")


def isoformat_utc(o: datetime) -> str:
    """
    If a python datetime is naive, assume it is UTC.
    Can be used with pydantic's json_encoders.

    2021-09-01T12:30:00 -> 2021-09-01T12:30:00+00:00

    Example:
        class Config:
            json_encoders = {datetime: isoformat_utc}

    Note that .replace is used rather than ``.astimezone`` so that the timezone is always UTC.
    """
    if o.tzinfo is None:
        return o.replace(tzinfo=UTC).isoformat()
    return o.isoformat()


class Model(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True
        anystr_max_length = 1 << 16
        allow_population_by_field_name = True
        json_encoders = {datetime: isoformat_utc}


def estimate_sample_size(size: int) -> int:
    """
    Estimate the sample size needed to accurately estimate the row bytes.
    """

    if size == 0:
        msg = f"Cannot estimate sample size for {size} rows."
        raise ZeroDivisionError(msg)

    z_score, margin_of_error, variance_estimate = 1.96, 0.01, 0.5
    # Calculates the base sample size needed for estimating a population proportion
    # #with a specified confidence level (95% with z_score=1.96) and margin of error (0.01):
    n = (z_score**2 * variance_estimate * (1 - variance_estimate)) / margin_of_error**2

    # Adjust for finite population
    n = n / (1 + (n - 1) / size)
    return ceil(n)


def estimate_row_bytes(collection: list[Any]) -> int:
    size = len(collection)
    sample_size = estimate_sample_size(size=size)
    sample = random.choices(collection, k=sample_size)
    # Use .to_json() and count the number of bytes
    sample_json = json.dumps(jsonable_encoder(sample), separators=(",", ":"))
    return ceil(len(sample_json) / sample_size)


class BatchifyMixin(BaseModel, Generic[DataT]):
    """
    Mixin to determine the size of a batch of data so that it's JSON representation fits within
    a certain size.
    """

    __root__: list[DataT]

    def batchify(self, max_bytes=16_777_216, margin=0.5):
        """
        Generate batches of data that are less than or equal to the max_bytes * margin
        """
        size = len(self.__root__)
        if size <= 0:
            logger.info("%s cannot be batched. No data.", self.__class__.__name__)
            return
        estimated_row_bytes = estimate_row_bytes(collection=self.__root__)
        logger.info("Estimated row bytes: %d bytes/row", estimated_row_bytes)
        batch_size: int = ceil((max_bytes * margin) / estimated_row_bytes)
        logger.info(
            "Batch size: %d Rows - %dB", batch_size, batch_size * estimated_row_bytes
        )

        batched_rows = [
            list(filter(None, batch))
            for batch in zip_longest(*[iter(self.__root__)] * batch_size)
        ]

        for i, rows in enumerate(batched_rows, start=1):
            logger.info("Batch %d of %d", i, len(batched_rows))
            yield self.__class__.construct(__root__=rows)


class StrEnum(str, Enum):
    """
    A base class for string enums.
    """

    def __str__(self) -> str:
        return str.__str__(self)


__all__ = [
    "BatchifyMixin",
    "Model",
    "StrEnum",
    "estimate_row_bytes",
    "estimate_sample_size",
]
