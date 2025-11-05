from typing import Optional

from pydantic.v1 import Field, conlist, validator

from api.v2.models.validators import parse_json_data

from . import Model
from .validators import empty_to_unknown, empty_to_unknown_one


class AdminSDPSubTask(Model):
    sub_task_id: int
    subtask_desc: str
    subtask_desc_long: Optional[str]
    subtask_doc_link: str
    task_ids: conlist(int, unique_items=True)
    sold_as_service_type_ids: conlist(int, unique_items=True)
    pricing_type_ids: conlist(int, unique_items=True)
    buying_program_type_ids: conlist(int, unique_items=True)
    hours: float = 0.0
    frequency: int = 0
    cycle_days: int = 0

    _process_json = validator(
        "task_ids",
        "sold_as_service_type_ids",
        "pricing_type_ids",
        "buying_program_type_ids",
        pre=True,
        allow_reuse=True,
    )(parse_json_data)

    _validate_unknowns = validator("task_ids", allow_reuse=True)(empty_to_unknown)
    _validate_unknowns_one = validator(
        "sold_as_service_type_ids",
        "pricing_type_ids",
        "buying_program_type_ids",
        allow_reuse=True,
    )(empty_to_unknown_one)


class AdminSDPSubTaskCreate(Model):
    subtask_desc: str
    subtask_desc_long: Optional[str]
    subtask_doc_link: str
    task_ids: conlist(int, unique_items=True)
    sold_as_service_type_ids: conlist(int, unique_items=True)
    pricing_type_ids: conlist(int, unique_items=True)
    buying_program_type_ids: conlist(int, unique_items=True)
    hours: float = Field(
        0.0, ge=0.0, description="Number of hours to complete the subtask"
    )
    frequency: int = Field(
        0, ge=0, description="Number of times the subtask is repeated"
    )
    cycle_days: int = Field(
        0, ge=-365, le=365, description="Number of days in the cycle"
    )

    _validate_unknowns = validator("task_ids", allow_reuse=True)(empty_to_unknown)
    _validate_unknowns_one = validator(
        "sold_as_service_type_ids",
        "pricing_type_ids",
        "buying_program_type_ids",
        allow_reuse=True,
    )(empty_to_unknown_one)

    class Config:
        schema_extra = {
            "examples": [
                {
                    "subtask_desc": "Example subtask",
                    "subtask_desc_long": "A longer description of the subtask",
                    "subtask_doc_link": "https://example.com",
                    "task_ids": [],
                    "sold_as_service_type_ids": [],
                    "pricing_type_ids": [],
                    "buying_program_type_ids": [],
                    "hours": 1.0,
                    "frequency": 2,
                    "cycle_days": -30,
                }
            ]
        }


class AdminSDPSubTaskEdit(Model):
    sub_task_id: int
    subtask_desc: str
    subtask_desc_long: Optional[str]
    subtask_doc_link: str
    task_ids: conlist(int, unique_items=True)
    sold_as_service_type_ids: conlist(int, unique_items=True)
    pricing_type_ids: conlist(int, unique_items=True)
    buying_program_type_ids: conlist(int, unique_items=True)
    hours: float = Field(
        0.0, ge=0.0, description="Number of hours to complete the subtask"
    )
    frequency: int = Field(
        0, ge=0, description="Number of times the subtask is repeated"
    )
    cycle_days: int = Field(
        0, ge=-365, le=365, description="Number of days in the cycle"
    )

    _validate_unknowns = validator("task_ids", allow_reuse=True)(empty_to_unknown)
    _validate_unknowns_one = validator(
        "sold_as_service_type_ids",
        "pricing_type_ids",
        "buying_program_type_ids",
        allow_reuse=True,
    )(empty_to_unknown_one)

    class Config:
        schema_extra = {
            "examples": [
                {
                    "sub_task_id": 1,
                    "subtask_desc": "Example subtask",
                    "subtask_desc_long": "A longer description of the subtask",
                    "subtask_doc_link": "https://example.com",
                    "task_ids": [],
                    "sold_as_service_type_ids": [],
                    "pricing_type_ids": [3, 5],
                    "buying_program_type_ids": [],
                    "hours": 1.0,
                    "frequency": 1,
                    "cycle_days": 30,
                }
            ]
        }
