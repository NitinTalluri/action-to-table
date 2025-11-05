import pytest


@pytest.mark.parametrize("test_app", [{}], indirect=True)
def test_healthcheck_get(test_app):
    """
    Does the server respond to an unauthenticated GET request to /healthcheck with a JSON response of {"status": "ok"}
    """
    from fastapi.testclient import TestClient

    with TestClient(test_app) as noauth_client:
        response = noauth_client.get(test_app.url_path_for("healthcheck"))
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
