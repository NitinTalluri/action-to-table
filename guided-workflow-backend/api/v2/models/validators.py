import json
import logging
import re
from datetime import date
from functools import lru_cache
from typing import Optional, Union

from dateutil.parser import parse
from pydantic.v1 import ValidationError

logger = logging.getLogger("api")


@lru_cache(maxsize=10_000)
def process_date(date_str: Union[str, date]) -> date:
    """
    Process a date string.

    Parameters
    ----------
    date_str

    Returns
    -------

    """
    match date_str:
        case date():
            return date_str
        case str():
            return parse(date_str).date()
    return parse(date_str).date()


def try_process_date(date_str: Union[str, date, None]) -> Optional[date]:
    """
    Try to process a date string, return None if it fails.

    Parameters
    ----------
    date_str

    Returns
    -------

    """
    match date_str:
        case str():
            try:
                return process_date(date_str)
            except Exception:
                return None
        case date():
            return date_str
        case None:
            return None
        case _:
            return None


def parse_json_data(data):
    match data:
        case str():
            return json.loads(data)
        case _:
            return data


def coerce_notification_data(cls, v, values):
    from api.v2.models import (
        CreateMessage,
        DownloadMessage,
        TableMessage,
        TextMessageCreate,
    )

    def parse_item(sub_item):
        match sub_item:
            case str(msg):
                yield TextMessageCreate(type="text", data=msg)
            case {"excel_location": str(url), **rest} if not rest:
                yield DownloadMessage.parse_obj(
                    {
                        "type": "download",
                        "data": {"label": "Download Results", "url": url},
                    }
                )
            case {"excel_location": str(url), **rest} if rest:
                yield TableMessage(type="table", data=rest)
                yield DownloadMessage.parse_obj(
                    {
                        "type": "download",
                        "data": {"label": "Download Results", "url": url},
                    }
                )
            case dict():
                try:
                    yield CreateMessage.parse_obj(sub_item).dict()
                except ValidationError as e:
                    logger.debug(
                        "notification_id:'%s' Failed to parse message: %r with error: %r",
                        values.get("notification_id", "Unknown Id"),
                        sub_item,
                        e.errors(),
                    )
                except Exception:
                    logger.debug(
                        "notification_id:'%s'Failed to parse message: %r. Ignoring",
                        values.get("notification_id", "Unknown Id"),
                        sub_item,
                    )
            case list(items):
                for item in items:
                    yield from parse_item(item)

    match v:
        case None:
            return []
        case list(items):
            return [item for sub_item in items for item in parse_item(sub_item)]
        case _:
            return [parse_item(v)]


def parse_currency(value) -> float | int | str | None:
    match value:
        case float() | int() | None:
            return value
        case str():
            # Does it have numbers at all?
            if not re.search(r"\d", value):
                return None
            # Before removing non-digits, check if it's wrapped in parentheses. If so, it's negative.
            is_negative = "(" in value and ")" in value
            if is_negative:
                value = value.replace("(", "").replace(")", "")
            # Remove all non-digits and non-decimals

            parsed = re.sub(r"[^\d.]", "", value)

            if is_negative:
                return f"-{float(parsed):.2f}"
            return f"{float(parsed):.2f}"
        case _:
            raise ValueError(f"Invalid currency value: {value}")


__all__ = [
    "coerce_notification_data",
    "parse_currency",
    "parse_json_data",
    "process_date",
    "try_process_date",
]
