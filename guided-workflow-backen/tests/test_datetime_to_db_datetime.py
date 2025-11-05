from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil import parser


def get_zone(offset):
    match offset:
        case 0:
            return ZoneInfo("UTC")
        case -7:
            return ZoneInfo("America/Los_Angeles")
        case -4:
            return ZoneInfo("America/New_York")
        case _:
            raise ValueError("Invalid timezone offset")


sys_tz = datetime.now().astimezone().tzinfo
system_utc_offset = sys_tz.utcoffset(datetime.now())

testdata_ = [
    (
        ZoneInfo("UTC"),  # Database timezone is UTC
        "2020-01-01T00:00:00Z",  # Given isoformat datetime is UTC
        datetime(
            2020, 1, 1, 0, 0, 0
        ).isoformat(),  # Should be stored as naive datetime and equal to the given datetime
    ),
    (
        ZoneInfo("America/Los_Angeles"),  # Database timezone is America/Los_Angeles
        "2020-01-01T00:00:00Z",  # Given isoformat datetime is UTC
        datetime(
            2019, 12, 31, 16, 0, 0
        ).isoformat(),  # Should be stored as naive datetime and equal to the given datetime
    ),
]


def pytest_generate_tests(metafunc):
    if "test_data" in metafunc.fixturenames:
        params = []
        for offset, given, expected in testdata_:
            params.append((offset, given, expected))
        metafunc.parametrize("test_data", params)


def test_datetime_to_db_datetime(test_data):
    """

    Parameters
    ----------
    test_data

    Returns
    -------

    """

    from api.v2.routers.workflows.notifications import datetime_to_db_datetime

    zone, given, expected = test_data

    class FakeSettings:
        db_timezone = zone

    expected = parser.parse(expected)

    result = datetime_to_db_datetime(FakeSettings(), parser.parse(given))
    assert result == expected
