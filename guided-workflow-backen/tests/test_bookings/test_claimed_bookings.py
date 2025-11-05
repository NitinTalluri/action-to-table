import pytest
from fastapi.testclient import TestClient
from pydantic import parse_obj_as
from starlette.authentication import AuthCredentials
from starlette.requests import Request


class TestClaimedBookingsAsManager:
    @pytest.fixture
    def test_app(self, username):
        from api.main import app
        from api.dependencies.security import decode_bearer
        from api.dependencies import DataCanvasUser
        
        def decode_bearer_override(r: Request):
            user = DataCanvasUser(username=username, email=username, scopes={"dc_manager"})
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
            
        
    def test_manager_gated_endpoint(self, client):
        # If manager is logged in, they should be able to access the endpoint
        
        response = client.get(client.app.url_path_for("get_claimed_bookings"))
        assert response.status_code < 400
        
    def test_get_claimed_bookings(self, client):
        # Test that get claimed bookings returns a list of V2ClaimedBookingContractsModel
        from api.v2.models import V2ClaimedBookingContractsModel
        response = client.get(client.app.url_path_for("get_claimed_bookings"))
        assert response.status_code == 200
        parse_obj_as(list[V2ClaimedBookingContractsModel], response.json())

    @pytest.mark.parametrize("booking_contract, dc_engagement_id_default, status_code, expected_error",
                             [
                                 (104338, 20285, 200, None),
                                 (104338, 94, 200, None),
                              (104338, -1, 404, "Engagement ID -1 not found"),
                              (-1, 94, 404, "Booking Contract -1 not found")])
    def test_update_claimed_bookings(self, client, booking_contract, dc_engagement_id_default,
                                     status_code, expected_error):
        # Test that updates dc_engagement_id_default of a claimed booking
        from api.v2.models import V2ClaimedBookingContractsModel, V2ModifyBookingDefaultEngagement
        response = client.patch(
            client.app.url_path_for('update_booking_defaults', booking_contract=booking_contract),
            json=V2ModifyBookingDefaultEngagement(
                booking_contract=booking_contract,
                dc_engagement_id_default=dc_engagement_id_default).dict()
        )
        assert response.status_code == status_code

        if expected_error:
            assert expected_error == response.json().get("detail")
            return
        
        parsed = parse_obj_as(V2ClaimedBookingContractsModel, response.json())
        
        assert parsed.booking_contract == booking_contract
        assert parsed.dc_engagement_id_default == dc_engagement_id_default
