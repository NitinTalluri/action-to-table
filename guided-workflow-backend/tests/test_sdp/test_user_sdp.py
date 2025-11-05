import getpass
from operator import itemgetter

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


user_login = make_patch_login(f"{getpass.getuser()}@cisco.com", {"dc_admin"})


class TestUserSdp:
    @pytest.fixture()
    def sdp_client(self, test_app):
        prev_decode_bearer = test_app.dependency_overrides.pop(decode_bearer, None)
        test_app.dependency_overrides[decode_bearer] = user_login
        yield TestClient(test_app)
        test_app.dependency_overrides[decode_bearer] = prev_decode_bearer

    @pytest.mark.parametrize("dc_engagement_id", [94])
    @pytest.mark.parametrize(
        "logged_user",
        [f"{getpass.getuser()}@cisco.com", "benjacob@cisco.com"],
        ids=["self", "other"],
    )
    def test_get_sdp(self, sdp_client, dc_engagement_id, logged_user):
        """
        Given Authenticated Client
        Call the get_user_engagement_deliverables endpoint
        Check that the response is 200, JSON, and has a list of dictionaries
        """

        uri = sdp_client.app.url_path_for(
            "get_user_engagement_deliverables", dc_engagement_id=dc_engagement_id
        )
        uri = f"{uri}?logged_user={logged_user}"

        response = sdp_client.get(uri)

        assert response.status_code == 200
        data = response.json()
        assert data is not None

        assert isinstance(data, list)
        assert all(isinstance(item, dict) for item in data)

    @pytest.mark.parametrize("dc_engagement_id", [94])
    @pytest.mark.parametrize(
        "logged_user",
        [f"{getpass.getuser()}@cisco.com", "benjacob@cisco.com"],
        ids=["self", "other"],
    )
    def test_get_scheduled_sdp(self, sdp_client, dc_engagement_id, logged_user):
        uri = sdp_client.app.url_path_for(
            "get_user_engagement_scheduled_deliverables",
            dc_engagement_id=dc_engagement_id,
        )
        uri = f"{uri}?logged_user={logged_user}"
        response = sdp_client.get(uri)
        assert response.status_code == 200
        data = response.json()
        assert data is not None

        get_task_user = itemgetter("cisco_cco_id")
        get_deliverable_ids = itemgetter(
            "booking_contract",
            "dc_engagement_id",
            "deliverable_id",
            "due_date",
            "sub_task_id",
            "task_id",
        )

        # Check that the response only contains tasks for the logged user
        for header in data:
            for task in header["tasks"]:
                assert get_task_user(task) == logged_user

        # Check that the response does not contain duplicate deliverables
        seen_deliverables = set()
        for header in data:
            for task in header["tasks"]:
                deliverable_ids = get_deliverable_ids(task)
                assert deliverable_ids not in seen_deliverables, (
                    f"Duplicate deliverable found: {deliverable_ids}"
                )
                seen_deliverables.add(deliverable_ids)

    @pytest.mark.parametrize("dc_engagement_id", [94])
    @pytest.mark.parametrize(
        "logged_user",
        [f"{getpass.getuser()}@cisco.com", "benjacob@cisco.com"],
        ids=["self", "other"],
    )
    def test_get_closed_sdp(self, sdp_client, dc_engagement_id, logged_user):
        uri = sdp_client.app.url_path_for(
            "get_user_engagement_closed_deliverables",
            dc_engagement_id=dc_engagement_id,
        )
        uri = f"{uri}?logged_user={logged_user}"

        response = sdp_client.get(uri)
        assert response.status_code == 200
        data = response.json()
        assert data is not None

        get_task_user = itemgetter("cisco_cco_id")

        # Check that the response only contains tasks for the logged user
        for header in data:
            for task in header["tasks"]:
                assert get_task_user(task) == logged_user

        # Check that the response does not contain duplicate deliverables
        seen_deliverables = set()
        get_deliverable_ids = itemgetter(
            "booking_contract",
            "dc_engagement_id",
            "deliverable_id",
            "due_date",
            "sub_task_id",
            "task_id",
        )
        for header in data:
            for task in header["tasks"]:
                deliverable_ids = get_deliverable_ids(task)
                assert deliverable_ids not in seen_deliverables, (
                    f"Duplicate deliverable found: {deliverable_ids}"
                )
                seen_deliverables.add(deliverable_ids)

    @pytest.mark.parametrize("dc_engagement_id", [94])
    @pytest.mark.parametrize(
        "logged_user",
        [f"{getpass.getuser()}@cisco.com", "benjacob@cisco.com"],
        ids=["self", "other"],
    )
    def test_get_active_sdp(self, sdp_client, dc_engagement_id, logged_user):
        """
        Given Authenticated Client
        Call the get_user_engagement_active_deliverables endpoint
        Check that the response is 200, JSON, and has a list of dictionaries
        """

        uri = sdp_client.app.url_path_for(
            "get_user_engagement_active_deliverables", dc_engagement_id=dc_engagement_id
        )
        uri = f"{uri}?logged_user={logged_user}"

        response = sdp_client.get(uri)

        assert response.status_code == 200
        data = response.json()
        assert data is not None
        
        get_deliverable_ids = itemgetter(
            "booking_contract",
            "dc_engagement_id",
            "deliverable_id",
            "due_date",
            "sub_task_id",
            "task_id",
        )
        seen_deliverables = set()
        for header in data:
            for task in header["tasks"]:
                deliverable_ids = get_deliverable_ids(task)
                assert deliverable_ids not in seen_deliverables, (
                    f"Duplicate deliverable found: {deliverable_ids}"
                )
                seen_deliverables.add(deliverable_ids)
        

        
        
        
        

    @pytest.mark.parametrize("dc_engagement_id", [6224])
    @pytest.mark.parametrize("logged_user", ["palbabu@cisco.com"])
    def test_get_active_sdp_not_duplicated(
        self, sdp_client, dc_engagement_id, logged_user
    ):
        """
        Specific test case for engagement 6224.
        Given the specific engagement and user, call the get_user_engagement_active_deliverables endpoint
        Check that the response is 200, JSON, and has a list of dictionaries
        Moreover, check that the response does not contain duplicate deliverables using the following fields:
            - booking_contract
            - cycle_iterator
            - deliverable_id
            - header_name
            - sub_task_id
            - task_id
        """

        uri = sdp_client.app.url_path_for(
            "get_user_engagement_active_deliverables",
            dc_engagement_id=dc_engagement_id,
        )
        uri = f"{uri}?logged_user={logged_user}"

        response = sdp_client.get(uri)

        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert isinstance(data, list)
        assert all(isinstance(item, dict) for item in data)

        seen = set()
        for record in data:
            header_name = record["header_name"]
            tasks = record["tasks"]
            for task in tasks:
                task_keys = (
                    task["booking_contract"],
                    task["cycle_iterator"],
                    task["deliverable_id"],
                    task["header_name"],
                    task["sub_task_id"],
                    task["task_id"],
                )
                assert task_keys not in seen, (
                    f"Duplicate deliverable found in header: {header_name=}: {task_keys}"
                )
                seen.add(task_keys)

    @pytest.mark.parametrize("dc_engagement_id", [94])
    @pytest.mark.parametrize(
        "logged_user",
        [f"{getpass.getuser()}@cisco.com", "benjacob@cisco.com"],
        ids=["self", "other"],
    )
    def test_get_scheduled_sdp(self, sdp_client, dc_engagement_id, logged_user):
        """
        Given Authenticated Client
        Call the get_user_engagement_scheduled_deliverables endpoint
        Check that the response is 200, JSON, and has a list of dictionaries
        """

        uri = sdp_client.app.url_path_for(
            "get_user_engagement_scheduled_deliverables",
            dc_engagement_id=dc_engagement_id,
        )
        uri = f"{uri}?logged_user={logged_user}"

        response = sdp_client.get(uri)

        assert response.status_code == 200
        data = response.json()
        assert data is not None

        assert isinstance(data, list)
        assert all(isinstance(item, dict) for item in data)

    @pytest.mark.parametrize("dc_engagement_id", [94])
    @pytest.mark.parametrize(
        "logged_user",
        [f"{getpass.getuser()}@cisco.com", "benjacob@cisco.com"],
        ids=["self", "other"],
    )
    def test_get_closed_deliverables(self, sdp_client, dc_engagement_id, logged_user):
        """
        Given Authenticated Client
        Call the get_user_engagement_closed_deliverables endpoint
        Check that the response is 200, JSON, and has a list of dictionaries
        """

        uri = sdp_client.app.url_path_for(
            "get_user_engagement_closed_deliverables", dc_engagement_id=dc_engagement_id
        )
        uri = f"{uri}?logged_user={logged_user}"

        response = sdp_client.get(uri)

        assert response.status_code == 200
        data = response.json()
        assert data is not None

        assert isinstance(data, list)
        assert all(isinstance(item, dict) for item in data)

    @pytest.mark.parametrize("logged_user", ["benjacob@cisco.com"])
    @pytest.mark.parametrize("dc_engagement_id", [94])
    @pytest.fixture(params=[("benjacob@cisco.com", 94)])
    def sampled_completion(self, test_app, request):
        """
        Retrieve an 'active' completion for the logged user
        """
        logged_user, dc_engagement_id = request.param

        uri = test_app.url_path_for(
            "get_user_engagement_active_deliverables", dc_engagement_id=dc_engagement_id
        )
        uri = f"{uri}?logged_user={logged_user}"

        response = TestClient(test_app).get(uri)
        data = response.json()
        assert data is not None
        assert isinstance(data, list)
        return data[0]["tasks"][0]

    def test_put_sdp_completion_with_non_existent_fk_fails(
        self,
        sdp_client,
    ):
        """
        Given Authenticated Client
        Try to call the put_sdp_completion endpoint with non-existent FKs (sub_task_ids, booking_contract, cycle_iterator, completion_type_id, dc_engagement_id)
        Check that the response is 404
        """
        from api.v2.models import UserSDPCompletionDeliverablePayload

        uri = sdp_client.app.url_path_for("put_sdp_completion")

        payload = UserSDPCompletionDeliverablePayload(
            sub_task_id=1,
            booking_contract=1,
            cycle_iterator=1,
            completion_type_id=1,
            dc_engagement_id=1,
            is_completed=True,
        )

        response = sdp_client.put(uri, json=payload.dict())
        assert response.status_code == 404
