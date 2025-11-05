import json
import logging
from threading import Lock
from typing import TYPE_CHECKING, Annotated, Optional

import boto3
from fastapi import Depends
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from . import GetSettingsDep  # noqa F401

if TYPE_CHECKING:
    from api.settings import AppSettings

logger = logging.getLogger("api")


def get_secret(settings: "AppSettings"):
    secret_name = settings.db_string_secret.get_secret_value()
    region_name = settings.aws_region
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name,
    )
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logger.exception("Failed to retrieve secret")
        raise e

        # Secrets Manager decrypts the secret value using the associated KMS CMK
        # Depending on whether the secret was a string or binary, only one of these fields will be populated
    if "SecretString" in get_secret_value_response:
        text_secret_data = get_secret_value_response["SecretString"]
        return text_secret_data
    else:
        binary_secret_data = get_secret_value_response["SecretBinary"]
        return binary_secret_data


def get_db_url(settings: "AppSettings") -> str:
    secret = get_secret(settings)
    db_url = json.loads(secret)[settings.db_string_secret.get_secret_value()].format(
        schema=settings.db_schema, wh=settings.db_warehouse
    )
    return db_url


ENGINE: Optional[Engine] = None
ENGINE_LOCK = Lock()


def get_engine(settings: GetSettingsDep) -> Engine:
    """
    Get either a Global instance of Engine (if not None) or create a new Engine instance

    Engine creation is gated by a lock to prevent multiple threads from creating multiple engines while waiting for the
    get_db_url() function to return the database URL
    """

    global ENGINE  # noqa: PLW0603
    if ENGINE is not None:
        return ENGINE

    with ENGINE_LOCK:
        if ENGINE is not None:
            # Another thread already created the engine while we were waiting for the lock
            return ENGINE
        session_params = (
            settings.db_session_parameters if settings.db_session_parameters else {}
        ) | {
            "query_tag": f"DC-{settings.env!s}",
        }
        ENGINE = create_engine(
            get_db_url(settings),
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_pool_max_overflow,
            pool_pre_ping=settings.db_pool_pre_ping,
            pool_recycle=5,
            pool_logging_name="api.db_pool",
            connect_args={
                "log_max_query_length": 10_000,
                "session_parameters": session_params,
                "disable_ocsp_checks": True,  # Required for PrivateLink + certifi 2025.04.26
            },
        )

        return ENGINE


GetEngineDep = Annotated[Engine, Depends(get_engine)]


def get_session(engine: GetEngineDep) -> Session:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


GetSessionDep = Annotated[Session, Depends(get_session)]


__all__ = ["GetSessionDep", "get_session"]
