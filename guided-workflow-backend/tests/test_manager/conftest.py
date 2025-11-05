from typing import Optional, List
import getpass
import pytest
from fastapi import Request
from snowflake.sqlalchemy import URL
from sqlmodel import Session, create_engine
from starlette.authentication import AuthCredentials

from utils import MockPrefectClient, MockS3Client

@pytest.fixture(scope="session")
def username(request):
    """Fixture to provide the local username for testing purposes."""
    return getattr(request, "param", f"{getpass.getuser()}@cisco.com")

@pytest.fixture(scope="session")
def scopes(request):
    return {"dc_manager"}

def make_patch_login(username, scopes):
    from api.dependencies import DataCanvasUser

    def _decode_bearer(r: Request):
        user = DataCanvasUser(username=username, email=username, scopes=scopes)
        cred = AuthCredentials(scopes=list(user.scopes))
        r.scope["user"] = user
        r.scope["auth"] = cred
        return user

    _decode_bearer.__name__ = "decode_bearer_override"

    return _decode_bearer

@pytest.fixture()
def patch_login(username, scopes):
    from api.dependencies.security import decode_bearer
    return {decode_bearer: make_patch_login(username, scopes)}

@pytest.fixture(scope="session")
def db_user_uri(username):
    """
    Use local auth vs secretsmanager
    """
    db_uri = URL(
        user=username,
        account="cisco.us-east-1",
        warehouse="CPS_DSCI_ETL_EXT2_WH",
        database="CPS_DB",
        schema="CPS_DSCI_BR",
        authenticator="externalbrowser",
    )
    return db_uri

@pytest.fixture(scope="session")
def db_engine(db_user_uri):

    engine = create_engine(url=db_user_uri, connect_args={"log_query_max_length": 1e9,
                                                          "session_parameters": {"abort_detached_query": True, "statement_timeout_in_seconds": 1800, "client_session_keep_alive": False}})
    yield engine

@pytest.fixture
def db_session(db_engine):
    session = Session(bind=db_engine)
    yield session

def make_test_app(overrides:Optional[dict] = None):
    from api.main import app
    if overrides is not None:
        for override, func in overrides.items():
            app.dependency_overrides[override] = func
    return app

@pytest.fixture()
def test_app(patch_login, request):

    overrides = getattr(request, "param", {})

    dep_overrides = {**patch_login, **overrides}
    app = make_test_app(dep_overrides)
    yield app
    app.dependency_overrides.clear()

@pytest.fixture()
def test_client(request):
    test_app = request.getfixturevalue("test_app")
    from fastapi.testclient import TestClient

    with TestClient(test_app) as client:
        yield client

