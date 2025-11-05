import pytest
from contextlib import nullcontext as does_not_raise

from pydantic import ValidationError

from api.v2.models import V2TagInstancesParams, V2WriteTags


@pytest.fixture
def expected_ddl_action(action, config_strategy):
    if action != "set":
        return ValueError("action must be set")
    if config_strategy is None:
        return "set"
    elif config_strategy == "config-null":
        return "set-config-null"
    elif config_strategy == "config-all":
        return "set-config-all"
    elif config_strategy == "null":
        return "set-null"
    else:
        return ValidationError


@pytest.mark.parametrize("action", ["set"])
@pytest.mark.parametrize("user_id", ["user@cisco.com"])
@pytest.mark.parametrize("engagement_id", [0])
@pytest.mark.parametrize("instance_ids", [[1]])
@pytest.mark.parametrize("comment", [""])
@pytest.mark.parametrize(
    "config_strategy",
    [
        "config-null",
        "config-all",
        "null",
        None,
    ],
)
@pytest.mark.parametrize("tag_id", [0])
def test_tag_strategy_ddl(
    action,
    user_id,
    engagement_id,
    instance_ids,
    comment,
    config_strategy,
    tag_id,
    expected_ddl_action,
):

    model = V2TagInstancesParams.parse_obj(
        {
            "action": action,
            "userId": user_id,
            "engagementId": engagement_id,
            "instance": instance_ids,
            "comment": comment,
            "config_strategy": config_strategy,
            "tagId": tag_id,
        }
    )

    ddl_action = model.ddl_action
    assert ddl_action == expected_ddl_action


@pytest.fixture()
def payload_maker(request):
    strategy = request.param
    # return V2WriteTags(
    #     tag_ids=[1],
    #     instance_ids=[1],
    #     engagement_id=1,
    #     config_strategy=strategy,
    #     comment="",
    # ).dict(), strategy
    base = {
        "tag_ids": [1],
        "instance_ids": [1],
        "engagement_id": 1,
        "config_strategy": strategy,
        "comment": "",
    }
    if strategy == "explicit-null":
        base.pop("config_strategy")
    return base, strategy
    
    
    
@pytest.mark.parametrize(
    "payload_maker",
    [
        "null",
        None,
        "explicit-null",
    ],
    indirect=True,
)
def test_ddl_action_route_parsing(
    payload_maker,
    test_client,
    monkeypatch,
):
    # Does pydantic parse "null" as None?
    app = test_client.app
    
    
    route = app.url_path_for("submit_instance_tagging")
    payload, strategy = payload_maker
    response = test_client.post(route, json=payload)
    assert response.status_code != 422
    
    
def test_conf(patch_user_login):
    print(patch_user_login)
    assert 0