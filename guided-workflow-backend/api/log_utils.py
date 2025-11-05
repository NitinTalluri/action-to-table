import json
import logging
import logging.config
import re
import time
from contextvars import ContextVar
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from uvicorn.logging import AccessFormatter

if TYPE_CHECKING:
    from starlette.types import Scope

request_scope_var: ContextVar[Optional["Scope"]] = ContextVar(
    "request_scope_var", default=None
)


class SnowflakeQueryFilterLegacy(logging.Filter):
    """
    Filter for snowflake query logs. Written as class to make checks for if this is already added to a logger easier.

    This filter is intended to work with snowflake-connector python v3.7.1 and below.

    Notes
    -----
    By default, this filter will filter out the following lines:
    - Rollback and commit statements
    - Desc table statements, which are used to get table metadata
    - Current database and current schema statements, which are used to get the current database and schema
    """

    substr_ignore_pattern = re.compile(
        r"""  
                    ^# Matches start of string
                    (?:rollback|commit|desc\stable)  # Matches 'rollback', 'commit', 'desc table' at start. 
                    |                                 # or
                    (?:current_database|current_schema) # Matches 'current_database', 'current_schema'.
                    """,
        re.IGNORECASE | re.VERBOSE,
    )

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter for snowflake query logs. Hardcoded parameters for now, but could be made more flexible in __init__.
        """
        if not isinstance(record.msg, str):
            return False
        if not record.msg.startswith("running query"):
            return False
        record_args = record.args
        if not record_args:
            return False
        try:
            query = record_args[0]
        except (IndexError, TypeError):
            return False
        if not isinstance(query, str):
            return False
        if self.substr_ignore_pattern.search(query):
            return False
        record.msg = "%s"
        return True


class SnowflakeQueryFilter:
    """
    Filter for snowflake query logs. Written as class to make checks for if this is already added to a logger easier.

    This filter is intended to work with snowflake-connector python v3.7.1 and below.

    Notes
    -----
    By default, this filter will filter out the following lines:
    - Rollback and commit statements
    - Desc table statements, which are used to get table metadata
    - Current database and current schema statements, which are used to get the current database and schema
    """

    substr_ignore_pattern = re.compile(
        r"""  
                    ^# Matches start of string
                    (?:rollback|commit|desc\stable)  # Matches 'rollback', 'commit', 'desc table' at start. 
                    |                                 # or
                    (?:current_database|current_schema) # Matches 'current_database', 'current_schema'.
                    """,
        re.IGNORECASE | re.VERBOSE,
    )

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter for snowflake query logs. Hardcoded parameters for now, but could be made more flexible in __init__.
        """
        record_args = record.args

        if not record_args:
            return False
        record_msg = record.msg
        if not isinstance(record_msg, str):
            return False
        if not record_msg.startswith("running query"):
            return False
        try:
            query = record_args[0]
        except (IndexError, TypeError):
            return False
        if not isinstance(query, str):
            return False
        if self.substr_ignore_pattern.search(query):
            return False
        record.msg = "%s"
        record.levelno = logging.INFO
        record.levelname = "INFO"
        return True


class UserNameFilter(logging.Filter):
    """
    Injects the username into the log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        extra_scope = request_scope_var.get() or {}
        if not extra_scope:
            record.user = "Unknown User"
            return True
        user = extra_scope.get("user", None)
        cisco_cco_id = user.username if user else None
        username = (
            cisco_cco_id.removesuffix("@cisco.com") if cisco_cco_id else "Unknown User"
        )
        record.user = username
        return True


class ApiAccessFormatter(AccessFormatter):
    """
    This formatter is used to keep the access logging from uvicorn timestamp consistent with the rest of the logs.
    """

    def formatTime(self, record, datefmt=None):
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))


class ApiFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "user"):
            record.user = "Unknown User"
        return super().format(record)

    def formatTime(self, record, datefmt=None):
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))


def exclude_routes_filter(routes: list[str]):
    """
    Called from a logging config file to create a filter for a specific route.
    Mainly used to filter out health checks from access logs.

    Parameters
    ----------
    *routes : str
        One or more routes to exclude from the logs.

    Notes
    -----
    Exact matches are used by default. For wildcard matches, use a '*' at the end of the route.
    """

    def make_route_matcher(route):
        route_prefixed = route if route.startswith("/") else f"/{route}"
        if route_prefixed.endswith("*"):
            return lambda uri: uri.startswith(route[:-1])
        return lambda uri: uri == route

    def filter_record(record: logging.LogRecord, matchers: list[Callable[[str], bool]]):
        try:
            _, _, full_path, _, _ = record.args

            return not any(matcher(full_path) for matcher in matchers)
        except Exception:
            return True

    route_matchers = [make_route_matcher(route) for route in routes]
    filter_routes = partial(filter_record, matchers=route_matchers)

    return filter_routes


def setup_logging():
    logger = logging.getLogger("api")
    if logger.hasHandlers():
        # The logger is already set up via the uvicorn logger
        logger.info("Logging already set up")
        return

    log_path = Path(__file__).parent.parent / "logging.json"
    if log_path.exists():
        config = json.loads(log_path.read_text(encoding="utf-8"))
        logging.config.dictConfig(config)

    logger.info("Logging Setup")
