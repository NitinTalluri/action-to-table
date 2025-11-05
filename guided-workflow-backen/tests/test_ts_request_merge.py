import pytest

from api.v2.models import V2TagAction, V2ThoughtSpotTaskListWrite
from api.v2.orm.thought_spot import ThoughtSportInstanceRequestDict

IDS = {}

def get_id(name):
    global IDS
    if name not in IDS:
        IDS[name] = 0
    IDS[name] += 1
    return IDS[name]

def get_thoughtspot_id():
    return get_id("thoughtspot_id")

def get_dc_engagement_id():
    return get_id("dc_engagement_id")

def get_user_id():
    return get_id("user_id")


def make_db_task(**kwargs) -> ThoughtSportInstanceRequestDict:
    
    ts_id = kwargs.get("thoughtspot_id", get_thoughtspot_id())
    dc_id = kwargs.get("dc_engagement_id", get_dc_engagement_id())
    user_id = kwargs.get("user_id", get_user_id())
    
    return {
        "thoughtspot_id": ts_id,
        "dc_engagement_id": dc_id,
        "user_id": user_id,
        "tag_ids": [1],
        "tagset_ids": [1],
        "comment": "",
        "user_action": str(V2TagAction.set),
        "canvas_id": 1,
        "count_instances": 1,
        "file_location": "",
    }

def make_ts_task(config_strategy, **kwargs):
    ts_id = kwargs.get("thoughtspot_id", get_thoughtspot_id())
    
    return {
        "thoughtspot_id": ts_id,
        "config_strategy": config_strategy,
    }
    
def assert_merged(left, right, result):
    seen_left = {task["thoughtspot_id"] for task in left}
    seen_right = {task.thoughtspot_id for task in right.requests}
    seen_result = {task["thoughtspot_id"] for task in result}
    
    assert seen_left == seen_result
    assert seen_right == seen_result
    
    id_by_left = {task["thoughtspot_id"]: task for task in left}
    id_by_right = {task.thoughtspot_id: task.dict() for task in right.requests}
    
    for task in result:
        # Ensure they were merged correctly by thoughtspot_id
        assert task['config_strategy'] == id_by_right[task['thoughtspot_id']]['config_strategy']
        
# Follow convention that left ids are the same as right ids
# Follow convention that id #4 is missing from both
# Unordered
left_db_tasks = [
    make_db_task(thoughtspot_id=2, dc_engagement_id=1, user_id=1),
    make_db_task(thoughtspot_id=1, dc_engagement_id=1, user_id=1),
    make_db_task(thoughtspot_id=3, dc_engagement_id=1, user_id=1),
    make_db_task(thoughtspot_id=6, dc_engagement_id=1, user_id=1),
    make_db_task(thoughtspot_id=5, dc_engagement_id=1, user_id=1),
]

right_ts_tasks_raw = [
    make_ts_task("config-null", thoughtspot_id=6),
    make_ts_task("config-all", thoughtspot_id=2),
    make_ts_task("null", thoughtspot_id=3),
    make_ts_task(None, thoughtspot_id=1),
    make_ts_task(None, thoughtspot_id=5),
]

right_ts_tasks = V2ThoughtSpotTaskListWrite.parse_obj({"requests": right_ts_tasks_raw})



@pytest.mark.parametrize("left, right", [
    (left_db_tasks, right_ts_tasks),
])
def test_merge_tasks(left, right):
    from api.v2.routers.thought_spot_tag import merge_tasks
    result = merge_tasks(
        left, right, {task.thoughtspot_id for task in right_ts_tasks.requests}
        )
    assert_merged(left_db_tasks, right_ts_tasks, result)

