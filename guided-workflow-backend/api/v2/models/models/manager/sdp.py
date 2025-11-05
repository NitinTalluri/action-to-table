from pydantic import Field

from api.v2.models.contracts import V2BookingEngagementAssignment

from . import Model


class V2RebuildSDPForBookingPayload(Model):
    booking_contract: int = Field(..., description="The booking contract id")
    sub_task_ids: list[int] = Field(
        ...,
        description="List of sub task ids to rebuild SDP for",
        min_items=1,
        unique_items=True,
    )
    assignments: list["V2BookingEngagementAssignment"] = Field(
        ...,
        description="List of assignments to be made for the sub tasks. HW/SW assignments are added automatically",
    )


class V2GetSDPForBooking(Model):
    booking_contract: int = Field(..., description="The booking contract id")
    deliverable_id: int = Field(..., description="The deliverable id")
    deliverable_desc: str = Field(..., description="The deliverable description")
    task_id: int = Field(..., description="The task id")
    task_desc: str = Field(..., description="The task description")
    sub_task_id: int = Field(..., description="The sub task id")
    subtask_desc: str = Field(..., description="The subtask description")
    task_anchor_date_id: int = Field(..., description="The task anchor date id")
    task_cycle_iterator_name: str = Field(
        ..., description="The task cycle iterator name"
    )
    task_anchor_date_name: str = Field(..., description="The task anchor date name")
    task_cycle_iterator_id: int = Field(..., description="The task cycle iterator id")
    due_date_offset: int = Field(..., description="The due date offset in days")
    cycle_days: int = Field(..., description="The cycle days in the task")
    sdp_assigned_user_ids: list[int] = Field(
        ...,
        description="List of DC user ids with subtasks already assigned.",
        unique_items=True,
    )
