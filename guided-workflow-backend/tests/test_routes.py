import re

import pytest


@pytest.fixture
def test_app():
    from api.main import app

    return app


def test_overlapping_routes(test_app):
    seen_routes = set()
    generic_path_pattern = re.compile(r"\{[^}]*\}")  # Regex to find path parameters
    overlaps = []

    for route in test_app.routes:
        route_path = route.path
        route_name = route.name
        route_methods = route.methods

        generic_path = generic_path_pattern.sub("{param}", route_path)
        keys = [(method, generic_path) for method in route_methods]
        for k in keys:
            if k in seen_routes:
                overlaps.append((route_path, route_name, k[0]))
            seen_routes.add(k)

    assert not overlaps, f"Overlapping routes found: {overlaps}"
