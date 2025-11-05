import pytest


# noinspection PyTestParametrized
@pytest.mark.parametrize("override_decode_bearer", [{"dc_support"}], indirect=True)
@pytest.mark.parametrize(
    "route",
    [
        "get_deleted_canvas",
        "get_deleted_engagements",
        "get_deleted_engagement_tags_v2",
        "get_deleted_tagsets_v2",
    ],
)
def test_support_user_access(test_client, route):
    app = test_client.app
    matched_route = next((r for r in app.routes if r.name == route), None)
    matched_route_method = list(matched_route.methods)[0].lower()
    assert matched_route is not None
    uri = app.url_path_for(route)
    caller = getattr(test_client, matched_route_method)
    response = caller(uri)
    assert response.status_code not in {401, 403}


def test_open_support_case(test_client):
    app = test_client.app
    uri = app.url_path_for("create_support_case")
    from api.v2.models import SupportCaseCreatePayload

    payload = SupportCaseCreatePayload(
        subject="Test Case",
        comments="This is a test case",
        path="/test/path",
    )
    response = test_client.post(uri, json=payload.dict())

    assert response.status_code == 200

    data = response.json()

    assert data["subject"] == payload.subject
    assert data["comments"] == payload.comments
    assert data["path"] == payload.path
    assert "case_id" in data
