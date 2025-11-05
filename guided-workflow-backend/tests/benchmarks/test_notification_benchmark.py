import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime  # Added for datetime handling
from collections import namedtuple

import pytest
from sqlmodel import Session

from api.dependencies import GetSessionDep
from api.v2.models import (
    TaskNotification,
    safe_parse_orm_collection,
    safe_parse_collection,
)
from api.v2.queries.notifications import query_engagement_notifications


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSONEncoder that converts datetime objects to ISO format.
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class CustomJSONDecoder(json.JSONDecoder):
    """
    Custom JSONDecoder that parses ISO format strings back to datetime objects.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        for key, value in obj.items():
            if isinstance(value, str):
                try:
                    obj[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
        return obj


@pytest.fixture(
    params=[
        {"dc_engagement_id": 20285, "dc_user_id": 423},
    ]
)
def notification_rows(request, db_session: GetSessionDep) -> list[dict[str, Any]]:
    """
    Fixture that returns database rows for notifications.

    If a cached JSON file exists, it will parse and return the data.
    Otherwise, it will execute the query, cache the results, and return the data.

    This fixture is parametrized with dc_engagement_id and dc_user_id.
    These parameters are used when naming the cache file.
    """
    # Get parameters from request
    dc_engagement_id = request.param["dc_engagement_id"]
    dc_user_id = request.param["dc_user_id"]

    use_orm = "orm" in request.node.name

    # Define the path to the cache file with parameters in the filename
    cache_dir = Path(__file__).parent / "benchmark_cache"
    cache_dir.mkdir(exist_ok=True)
    cache_file = (
        cache_dir / f"notification_rows_eng_{dc_engagement_id}_user_{dc_user_id}.json"
    )

    # If cache file exists, load the data
    if cache_file.exists():
        with open(cache_file, "r") as f:
            rows = json.load(f, cls=CustomJSONDecoder)
    else:
        # Execute the query
        query = query_engagement_notifications(dc_engagement_id=dc_engagement_id)
        rows = [dict(r) for r in db_session.exec(query).mappings().all()]

        # Cache the results
        with open(cache_file, "w") as f:
            json.dump(rows, f, cls=CustomJSONEncoder)

    if not use_orm:
        return rows

    # Get the field names from the TaskNotification model
    field_names = list(TaskNotification.__fields__.keys())
    mock_tuple = namedtuple("TaskNotification", field_names)
    # Convert each dictionary to a named tuple
    orm_rows = [mock_tuple(**row) for row in rows]
    return orm_rows


def test_benchmark_safe_parse_orm_collection(notification_rows, benchmark):
    """
    Benchmark the performance of safe_parse_orm_collection.
    """

    def parse_with_orm_collection():
        return safe_parse_orm_collection(list[TaskNotification], notification_rows)

    # Run the benchmark
    result = benchmark(parse_with_orm_collection)

    # Verify the result is not empty (if we have data)
    if notification_rows:
        assert result
        assert isinstance(result, list)
        assert all(isinstance(item, TaskNotification) for item in result)


def test_benchmark_safe_parse_collection(notification_rows, benchmark):
    """
    Benchmark the performance of safe_parse_collection.
    """

    def parse_with_collection():
        return safe_parse_collection(list[TaskNotification], notification_rows)

    # Run the benchmark
    result = benchmark(parse_with_collection)

    # Verify the result is not empty (if we have data)
    if notification_rows:
        assert result
        assert isinstance(result, list)
        assert all(isinstance(item, TaskNotification) for item in result)


def test_benchmark_task_notification(notification_rows, benchmark):
    """
    Benchmark the performance of TaskNotification model.
    """

    def parse_row(rows):
        return [TaskNotification.parse_obj(row) for row in rows]

    # Run the benchmark
    result = benchmark(parse_row, notification_rows)

    # Verify the result is not empty (if we have data)
    if notification_rows:
        assert result
        assert isinstance(result, list)
        assert all(isinstance(item, TaskNotification) for item in result)
