import getpass
import random

import pytest
from starlette.authentication import AuthCredentials
from starlette.requests import Request
from starlette.testclient import TestClient

from api.dependencies.security import decode_bearer


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


admin_login = make_patch_login(f"{getpass.getuser()}@cisco.com", {"dc_admin"})


class TestAdminSdp:
    sdp_data = None
    sdp_task_id = None

    @pytest.fixture()
    def sdp_client(self, test_app):
        prev_decode_bearer = test_app.dependency_overrides.pop(decode_bearer, None)
        test_app.dependency_overrides[decode_bearer] = admin_login
        yield TestClient(test_app)
        test_app.dependency_overrides[decode_bearer] = prev_decode_bearer

    def test_get_sdp(self, sdp_client):
        """
        Given Authenticated Client
        Call the get_sdp endpoint
        Check that the response is 200, JSON, and has a list of dictionaries
        """

        uri = sdp_client.app.url_path_for("get_sdp")

        response = sdp_client.get(uri)

        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert len(data) > 0
        assert isinstance(data, list)
        assert all(isinstance(item, dict) for item in data)
        TestAdminSdp.sdp_data = data

    def test_get_sdp_task(self, sdp_client):
        """
        Given Authenticated Client and a randomly chosen task_id
        Call the get_sdp_task endpoint
        Check that the response is 200 and matches the expected schema and query
        """
        assert TestAdminSdp.sdp_data is not None
        task_id = random.choice(TestAdminSdp.sdp_data)["task_id"]
        uri = sdp_client.app.url_path_for("get_sdp_task", task_id=task_id)
        response = sdp_client.get(uri)

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert isinstance(data["sub_task_ids"], list)
        assert (
            len(data["sub_task_ids"]) > 0
        )  # Should have at least one sub-task (unknown)
        assert isinstance(data["deliverable_ids"], list)
        assert len(data["deliverable_ids"]) > 0
        TestAdminSdp.sdp_task_id = task_id
        
    def test_rebuild_sdp(self, sdp_client):
        """
        Given Authenticated Client
        Call the rebuild_sdp endpoint
        Check that the response is 202 (background task accepted)
        """
        uri = sdp_client.app.url_path_for("rebuild_sdp")
        response = sdp_client.post(uri)
        assert response.status_code == 202
