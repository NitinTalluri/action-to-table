from collections import Counter

import pytest
from fastapi.testclient import TestClient
from pydantic import parse_obj_as
from starlette.authentication import AuthCredentials
from starlette.requests import Request


class TestUnclaimedBookingsAsManager:
    @pytest.fixture
    def test_app(self):
        from api.dependencies import DataCanvasUser
        from api.dependencies.security.auth import decode_bearer
        from api.main import app

        def decode_bearer_override(r: Request):
            user = DataCanvasUser(
                username="manager",
                email="manager",
                scopes={"dc_manager"},
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


    def test_manager_gated_endpoint(self, client):
        # If manager is logged in, they should be able to access the endpoint

        response = client.get(client.app.url_path_for("get_unclaimed_bookings"))
        assert response.status_code < 400

    def test_get_unclaimed_bookings(self, client):
        # Test that get unclaimed bookings returns a list of V2BookingContractsModel
        from api.v2.models import V2BookingContractsModel
        response = client.get(client.app.url_path_for("get_unclaimed_bookings"))
        assert response.status_code == 200
        data = parse_obj_as(list[V2BookingContractsModel], response.json())
        
    def test_get_unclaimed_bookings_includes_default_engagament_id(self, client):
        # Test that get unclaimed bookings returns a list of V2BookingContractsModel each with a dc_engagement_id_default
        from api.v2.models import V2BookingContractsModel
        response = client.get(client.app.url_path_for("get_unclaimed_bookings"))
        assert response.status_code == 200
        data = parse_obj_as(list[V2BookingContractsModel], response.json())
        
        # Sanity check
        default_counts = Counter([row.dc_engagement_id_default for row in data])
        print(default_counts.most_common(10))
        
        



