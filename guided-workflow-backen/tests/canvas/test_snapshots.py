import pytest
from fastapi.testclient import TestClient
from starlette.authentication import AuthCredentials
from starlette.requests import Request
from tests.conftest import parse_stmt


class TestCanvasSnapshots:
    @pytest.fixture
    def test_app(self, username):
        from api.main import app
        from api.dependencies.security import decode_bearer
        from api.dependencies import DataCanvasUser

        def decode_bearer_override(r: Request):
            user = DataCanvasUser(username=username, email=username, scopes={})
            cred = AuthCredentials(scopes=list(user.scopes))
            r.scope["user"] = user
            r.scope["auth"] = cred
            return user

        overrides = app.dependency_overrides
        app.dependency_overrides = {**overrides, decode_bearer: decode_bearer_override}
        yield app
        app.dependency_overrides = overrides

    @pytest.fixture()
    def client(self, test_app):
        with TestClient(test_app) as client:
            yield client


    def test_get_snapshots_endpoint(self, client):
        """
        Test the get_snapshots endpoint to ensure it returns a valid response.
        """

        response = client.get(client.app.url_path_for("get_snapshots"))
        assert response.status_code < 400


def test_query_available_snapshots_compiles(parse_stmt):
    """
    Test that the query_available_snapshots function compiles without errors.
    Ensure the API schema is used.
    """

    from api.v2.queries import query_available_snapshots
    stmt = query_available_snapshots()
    parsed_stmt = parse_stmt(stmt)
    assert parsed_stmt is not None
    print(parsed_stmt.sql(dialect='snowflake', pretty=True))
    assert 'CPS_DSCI_API' in str(parsed_stmt.args.get('from'))


def test_query_latest_snapshot_compiles(parse_stmt):
    """
    Test that the query_latest_snapshot function compiles without errors.
    Ensure the API schema is used.
    """

    from api.v2.queries import query_latest_snapshot
    stmt = query_latest_snapshot()
    parsed_stmt = parse_stmt(stmt)
    assert parsed_stmt is not None
    print(parsed_stmt.sql(dialect='snowflake', pretty=True))
    assert 'CPS_DSCI_API' in str(parsed_stmt.args.get('from'))