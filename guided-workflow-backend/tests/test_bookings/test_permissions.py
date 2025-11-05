import pytest
from fastapi.testclient import TestClient
from starlette.authentication import AuthCredentials
from starlette.requests import Request


class TestBookingsAsManager:

    @pytest.fixture
    def test_app(self, request, username):
        from api.dependencies import DataCanvasUser
        from api.dependencies.security.auth import decode_bearer
        from api.main import app

        scope = request.param if hasattr(request, "param") else ""

        def decode_bearer_override(r: Request):
            user = DataCanvasUser(
                username=username,
                email=username,
                scopes={scope},
            )
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


    @pytest.mark.parametrize("test_app, name, params", [
        ("dc_manager", "get_manager_users", {}),
        ("dc_manager", "get_claimed_bookings", {}),
        ("dc_manager", "get_available_engagements", {}),
        ("dc_manager", "get_unclaimed_bookings", {}),
        ("dc_manager", "get_available_to_renew_from", {}),
        ("dc_manager", "get_super_customers", {}),
        ("dc_pool_manager", "get_manager_users", {}),
        ("dc_pool_manager", "get_claimed_bookings", {}),
        ("dc_pool_manager", "get_sdp_for_booking", {"booking_contract": 104338}),
    ], indirect=["test_app"])
    def test_access_allowed(self, client, name, params):
        """
        Given:
        - A manager or pool manager is logged in

        Action:
        - Access an endpoint that is gated for managers or pool managers

        Assertion:
        - The response status code should be 200, indicating access is allowed
        """

        response = client.get(client.app.url_path_for(name, **params))
        assert response.status_code == 200


    @pytest.mark.parametrize("test_app, name, params", [
        ("dc_pool_manager", "get_unclaimed_bookings", {}),
        ("dc_pool_manager", "get_available_to_renew_from", {}),
        ("dc_pool_manager", "get_super_customers", {}),
        ("dc_manager", "get_sdp_for_booking", {"booking_contract": 104338}),
    ], indirect=["test_app"])

    def test_access_denied(self, client, name, params):
        """
        Given:
        - A manager or pool manager is logged in

        Action:
        - Send GET request to an endpoint that is not accessible by the current user

        Assertion:
        - The response status code should be 401, indicating access is denied

        """

        response = client.get(client.app.url_path_for(name, **params))
        assert response.status_code == 401


    @pytest.mark.parametrize("test_app, booking_contract", [("dc_manager", 104338)], indirect=["test_app"])
    def test_dc_manager_access_denied_for_rebuild_sdp_for_booking(self, client, booking_contract):
        """
        Given:
        - A manager is logged in

        Action:
        - Send POST request to rebuild SDP for a booking contract

        Assertion:
        - The response status code should be 401, indicating access is denied
        """
        response = client.post(client.app.url_path_for("rebuild_sdp_for_booking", booking_contract=booking_contract))
        assert response.status_code == 401


    @pytest.mark.parametrize("test_app", ["dc_manager"], indirect=True)
    def test_dc_manager_access_denied_for_setting_pool_manager(self, client):
        """
        Given:
        - A manager is logged in

        Action:
        - Send PUT request to set pool manager

        Assertion:
        - The response status code should be 401, indicating access is denied
        """
        response = client.put(client.app.url_path_for("set_pool_manager"))
        assert response.status_code == 401


