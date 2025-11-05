from typing import Optional

from pydantic.v1 import Field, conlist, validator

from api.v2.models.validators import parse_json_data

from . import Model
from .validators import empty_to_unknown, enforce_default_zero


class AdminSDPTask(Model):
    task_id: int
    task_desc: str
    task_desc_long: Optional[str]
    task_doc_link: str
    sub_task_ids: conlist(int, unique_items=True)
    deliverable_ids: conlist(int, unique_items=True)
    hours: float = 0.0
    frequency: int = 0
    anchor_date_id: int
    cycle_iterator_id: int
    due_date_offset: int = 0

    _process_json = validator(
        "sub_task_ids", "deliverable_ids", pre=True, allow_reuse=True
    )(parse_json_data)
    _validate_unknowns = validator("sub_task_ids", "deliverable_ids", allow_reuse=True)(
        empty_to_unknown
    )


class AdminSDPTaskCreate(Model):
    task_desc: str
    task_desc_long: Optional[str]
    task_doc_link: str
    sub_task_ids: conlist(int, unique_items=True)
    deliverable_ids: conlist(int, unique_items=True)
    hours: float = Field(
        0.0, ge=0.0, description="Number of hours to complete the task"
    )
    frequency: int = Field(0, ge=0, description="Number of times the task is repeated")
    anchor_date_id: int
    cycle_iterator_id: int
    due_date_offset: int | None = Field(
        0, description="Only applicable for 'direct' type cycle_iterators"
    )

    _validate_unknowns = validator("sub_task_ids", "deliverable_ids", allow_reuse=True)(
        empty_to_unknown
    )
    _validate_due_date_offset = validator("due_date_offset", allow_reuse=True)(
        enforce_default_zero
    )


class AdminSDPTaskEdit(Model):
    task_id: int
    task_desc: str
    task_desc_long: Optional[str]
    task_doc_link: str
    sub_task_ids: conlist(int, unique_items=True)
    deliverable_ids: conlist(int, unique_items=True)
    hours: float = Field(
        0.0, ge=0.0, description="Number of hours to complete the task"
    )
    frequency: int = Field(0, ge=0, description="Number of times the task is repeated")
    anchor_date_id: int
    cycle_iterator_id: int
    due_date_offset: int | None = Field(
        0, description="Only applicable for 'direct' type cycle_iterators"
    )

    _validate_unknowns = validator(
        "sub_task_ids", "deliverable_ids", pre=True, allow_reuse=True
    )(empty_to_unknown)

    _validate_due_date_offset = validator("due_date_offset", allow_reuse=True)(
        enforce_default_zero
    )
