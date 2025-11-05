import datetime
from datetime import date

from pydantic.v1 import Field

from . import Model, TrueFalse


class UserSDPCompletionDeliverableRow(Model):
    """
    Represents a deliverable that has been completed by a user. This model is used to translate from the database to the API.
    """

    sub_task_id: int
    booking_contract: int
    dc_user_id: int
    cycle_iterator: int
    completion_type_id: int = Field(
        default=1, description="References table DC_SDP_TYP_TASK_COMPLETION_REASON"
    )
    dc_engagement_id: int
    due_date: date
    created_by: str | None
    create_dtm: datetime.datetime
    is_deleted: TrueFalse
    note: str


class UserSDPCompletionDeliverableResponse(Model):
    sub_task_id: int
    booking_contract: int
    dc_user_id: int
    cycle_iterator: int
    completion_type_id: int = Field(
        default=1, description="References table DC_SDP_TYP_TASK_COMPLETION_REASON"
    )
    dc_engagement_id: int
    due_date: date
    created_by: str | None
    create_dtm: datetime.datetime
    updated_by: str | None
    update_dtm: datetime.datetime | None
    is_completed: bool
    note: str

    class Config:
        schema_extra = {
            "examples": [
                {
                    "sub_task_id": 61,
                    "booking_contract": 123456,
                    "dc_user_id": 4,
                    "cycle_iterator": 12,
                    "completion_type_id": 1,
                    "dc_engagement_id": 727,
                    "due_date": "2022-01-15",
                    "created_by": "someuser@cisco.com",
                    "create_dtm": "2022-01-01T00:00:00",
                    "updated_by": None,
                    "update_dtm": None,
                }
            ]
        }


class UserSDPCompletionDeliverablePayload(Model):
    """
    Represents a deliverables completion submitted by a user.
    The is_completed field is used to indicate if the deliverable is completed or not.
    """

    sub_task_id: int
    booking_contract: int
    cycle_iterator: int
    completion_type_id: int = Field(
        description="References table DC_SDP_TYP_TASK_COMPLETION_REASON. This field must be set even if the deliverable is being reverted to incomplete."
    )
    dc_engagement_id: int
    due_date: date = Field(description="Due date of the deliverable being completed")
    is_completed: bool
    note: str = Field("")

    class Config:
        schema_extra = {
            "examples": [
                {
                    "sub_task_id": 61,
                    "booking_contract": 123456,
                    "cycle_iterator": 12,
                    "completion_type_id": 1,
                    "dc_engagement_id": 727,
                    "due_date": "2022-01-15",
                    "is_completed": True,
                    "note": "Completion Comment",
                }
            ]
        }


__all__ = [
    "UserSDPCompletionDeliverablePayload",
    "UserSDPCompletionDeliverableResponse",
    "UserSDPCompletionDeliverableRow",
]
