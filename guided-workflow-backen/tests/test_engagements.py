from contextlib import nullcontext as does_not_raise

from pydantic import parse_obj_as

from api.v2.models import V2EngagementRead


def test_get_engagements(test_client):
    """Does the server respond to a GET request to /api/v2/engagements with a list of all Engagements in the form of EngagementHeaders"""
    response = test_client.get(test_client.app.url_path_for("get_users_engagements"))
    assert response.status_code == 200
    data = response.json()
    with does_not_raise():
        data = parse_obj_as(list[V2EngagementRead], data)
    assert isinstance(data, list)
