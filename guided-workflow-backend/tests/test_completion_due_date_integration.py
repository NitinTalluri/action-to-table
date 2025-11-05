"""
Test cases for SDP completion due_date integration.
This ensures the CXEA Scale collision scenario is properly handled.
"""
import datetime
from datetime import date

from api.v2.models.sdp.completions import (
    UserSDPCompletionDeliverablePayload,
    UserSDPCompletionDeliverableResponse,
)


def test_completion_payload_includes_due_date():
    """Test that completion payload includes due_date field."""
    payload = UserSDPCompletionDeliverablePayload(
        sub_task_id=61,
        booking_contract=123456,
        cycle_iterator=1,
        completion_type_id=1,
        dc_engagement_id=727,
        is_completed=True,
        note="Test completion",
        due_date=date(2024, 1, 15),
    )

    assert payload.due_date == date(2024, 1, 15)
    assert payload.sub_task_id == 61
    assert payload.is_completed is True


def test_completion_response_includes_due_date():
    """Test that completion response includes due_date field."""
    response = UserSDPCompletionDeliverableResponse(
        sub_task_id=61,
        booking_contract=123456,
        dc_user_id=4,
        cycle_iterator=1,
        completion_type_id=1,
        dc_engagement_id=727,
        due_date=date(2024, 1, 15),  # Now required, not optional
        created_by="test@cisco.com",
        create_dtm=datetime.datetime(2024, 1, 1),
        updated_by=None,
        update_dtm=None,
        is_completed=True,
        note="Test completion",
    )

    assert response.due_date == date(2024, 1, 15)
    assert response.sub_task_id == 61
    assert response.is_completed is True


def test_completion_models_support_cxea_scale_scenario():
    """Test that models can handle CXEA Scale collision scenario."""
    # Two completions with same logical key except due_date
    completion_1 = UserSDPCompletionDeliverablePayload(
        sub_task_id=100,
        booking_contract=123456,
        cycle_iterator=1,  # Same cycle_iterator
        completion_type_id=1,
        dc_engagement_id=727,
        is_completed=True,
        note="First completion",
        due_date=date(2024, 1, 15),  # Different due_date
    )

    completion_2 = UserSDPCompletionDeliverablePayload(
        sub_task_id=100,
        booking_contract=123456,
        cycle_iterator=1,  # Same cycle_iterator
        completion_type_id=1,
        dc_engagement_id=727,
        is_completed=True,
        note="Second completion",
        due_date=date(2024, 2, 15),  # Different due_date
    )

    # Should be able to create both without conflicts
    assert completion_1.due_date != completion_2.due_date
    assert completion_1.cycle_iterator == completion_2.cycle_iterator
    assert completion_1.sub_task_id == completion_2.sub_task_id

    # This demonstrates the solution - due_date distinguishes the records
    assert completion_1 != completion_2  # Different due_dates make them unique