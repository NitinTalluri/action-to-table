from pydantic.v1 import conlist, validator

from ... import parse_json_data
from . import Model
from .validators import empty_to_unknown


class AdminSDPDeliverable(Model):
    deliverable_id: int
    deliverable_desc: str
    deliverable_doc_link: str
    task_ids: conlist(int, unique_items=True)

    _process_json = validator("task_ids", pre=True, allow_reuse=True)(parse_json_data)

    _validate_unknowns = validator("task_ids", allow_reuse=True)(empty_to_unknown)


class AdminSDPDeliverableCreate(Model):
    deliverable_desc: str
    deliverable_doc_link: str
    task_ids: conlist(int, unique_items=True)

    _validate_unknowns = validator("task_ids", allow_reuse=True)(empty_to_unknown)


class AdminSDPDeliverableEdit(Model):
    deliverable_id: int
    deliverable_desc: str
    deliverable_doc_link: str
    task_ids: conlist(int, unique_items=True)

    _validate_unknowns = validator("task_ids", pre=True, allow_reuse=True)(
        empty_to_unknown
    )
