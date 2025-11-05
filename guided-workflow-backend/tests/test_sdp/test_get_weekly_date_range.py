import datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from api.v2.queries.sdp.time_tracking import _get_weekly_date_range


@st.composite
def date_ranges(draw):
    reference_date = draw(
        st.dates(
            min_value=datetime.date(1900, 1, 1), max_value=datetime.date(2100, 12, 31)
        )
    )
    n_weeks = draw(st.integers(min_value=1, max_value=1000))
    return reference_date, n_weeks


@settings(max_examples=1000)
@given(
    date_ranges(),
)
def test_get_weekly_date_range(params):
    reference_date, n_weeks = params
    start_date, end_date = _get_weekly_date_range(
        reference_date=reference_date, n_weeks=n_weeks
    )

    # Check that start_date is before end_date
    assert start_date < end_date, "Start date should be before end date"

    # Check that start_date falls on a Monday (isoweekday() == 1)
    assert start_date.isoweekday() == 1, "Start date should be a Monday"

    # Check that end_date falls on a Sunday (isoweekday() == 7)
    assert end_date.isoweekday() == 7, "End date should be a Sunday"

    # Check that the difference is exactly (n_weeks * 7) - 1 days
    delta_days = (end_date - start_date).days
    expected_diff = (n_weeks * 7 * 2) - 1 + 7
    assert delta_days == expected_diff, (
        f"Difference should be {expected_diff} days, but got {delta_days}"
    )
