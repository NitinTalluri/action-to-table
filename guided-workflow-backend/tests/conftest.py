from typing import Optional

import pytest
import sqlglot
from fastapi import Request
from snowflake.sqlalchemy.snowdialect import SnowflakeDialect
from sqlmodel import Session
from starlette.authentication import AuthCredentials

from utils import MockPrefectClient, MockS3Client

@pytest.fixture()
def username(request):
    import getpass
    username = getattr(request, "param", f"{getpass.getuser()}@cisco.com")
    return username


@pytest.fixture()
def scopes(request):
    scopes = getattr(request, "param", {})
    return scopes


@pytest.fixture()
def user_scopes(request):
    default_scopes = request.getfixturevalue("scopes")
    return default_scopes

@pytest.fixture()
def admin_scopes(request):
    _ = request.getfixturevalue("scopes")
    return {"dc_admin"}

@pytest.fixture()
def manager_scopes(request):
    _ = request.getfixturevalue("scopes")
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


@pytest.fixture()
def patch_user_login(username):
    from api.dependencies.security import decode_bearer
    return {decode_bearer: make_patch_login(username, set())}


@pytest.fixture()
def patch_manager_login(username):
    from api.dependencies.security import decode_bearer
    return {decode_bearer: make_patch_login(username, {"dc_manager"})}


@pytest.fixture()
def patch_prefect_client():
    from api.dependencies.prefect import get_prefect_client
    def _get_prefect_client():
        return MockPrefectClient()
    _get_prefect_client.__name__ = "get_prefect_client_override"
    return {get_prefect_client: _get_prefect_client}


@pytest.fixture()
def patch_s3_client():
    from api.dependencies.aws import get_s3_client
    def _get_s3_client():
        return MockS3Client()
    _get_s3_client.__name__ = "get_s3_client_override"
    return {get_s3_client: _get_s3_client}


@pytest.fixture
def db_session():
    """Create a connection to the test database"""

    from api.dependencies.database import get_engine
    from api.dependencies import get_settings
    
    engine = get_engine(get_settings())
    session = Session(bind=engine)
    yield session
    
def make_test_app(overrides:Optional[dict] = None):
    from api.main import app
    if overrides is not None:
        for override, func in overrides.items():
            app.dependency_overrides[override] = func
    return app

@pytest.fixture()
def test_app(patch_login, patch_s3_client,patch_prefect_client, request):
    
    overrides = getattr(request, "param", {})
    
    dep_overrides = {**patch_login, **patch_s3_client, **patch_prefect_client, **overrides}
    app = make_test_app(dep_overrides)
    yield app
    app.dependency_overrides.clear()
    
    
@pytest.fixture()
def test_client(request):
    test_app = request.getfixturevalue("test_app")
    from fastapi.testclient import TestClient

    with TestClient(test_app) as client:
        yield client

@pytest.fixture
def parse_stmt():
    def _parse_stmt(s):
        return sqlglot.parse_one(
            str(
                s.compile(
                    compile_kwargs={"literal_binds": True}, dialect=SnowflakeDialect()
                )
            )
        )

    return _parse_stmt