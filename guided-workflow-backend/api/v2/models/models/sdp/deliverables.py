import datetime

from . import Model


class UserSDPEngagementDeliverable(Model):
    task_id: int
    task_desc: str | None
    sub_task_id: int
    subtask_desc: str
    deliverable_id: int
    deliverable_desc: str | None
    time_cycle: str
    cycle_days: int
    due_date_offset: int
    anchor_date: str
    anchor_date_id: int
    engagement_name: str | None
    dc_engagement_id: int
    booking_contract: int
    buying_program_name: str | None
    buying_program_type_id: int
    sold_as_service_name: str | None
    sold_as_service_type_id: int
    pricing_model_name: str | None
    pricing_model_type_id: int


class UserSDPActiveDeliverables(Model):
    booking_contract: int
    completed_by: str | None
    closed_date: datetime.date | None
    completion_type_id: int | None
    cycle: int
    dc_engagement_id: int
    deliverable_desc: str | None
    deliverable_id: int
    due_date: datetime.date | None
    engagement_name: str | None
    header_name: str
    is_closed: bool
    sort_date: datetime.date | None
    subtask_desc: str
    sub_task_id: int
    task_desc: str
    task_id: int
    task_status: str


class UserSDPActiveDeliverableHeader(Model):
    header_name: str
    booking_contract: int
    task_desc: str
    due_date: datetime.date
    cycle: int
    deliverable_id: int
    tasks: list[UserSDPActiveDeliverables]


class UserSDPScheduledDeliverables(Model):
    booking_contract: int
    cisco_cco_id: str
    dc_engagement_id: int
    deliverable_desc: str
    deliverable_id: int
    due_date: datetime.date
    engagement_name: str
    sort_date: datetime.date
    sub_task_id: int
    subtask_desc: str
    task_desc: str
    task_id: int


class UserSDPScheduledDeliverablesHeader(Model):
    header_name: str
    booking_contract: int
    task_desc: str
    due_date: datetime.date
    cycle: int
    deliverable_id: int
    tasks: list[UserSDPScheduledDeliverables]


class UserSDPClosedDeliverables(Model):
    booking_contract: int
    closed_date: datetime.date | None
    completed_by: str
    completion_type_id: int
    cycle: int
    dc_engagement_id: int
    deliverable_desc: str
    deliverable_id: int
    due_date: datetime.date
    engagement_name: str
    header_name: str
    is_closed: bool
    sort_date: datetime.date
    sub_task_id: int
    subtask_desc: str
    task_desc: str
    task_id: int
    task_status: str


class UserSDPClosedDeliverablesHeader(Model):
    header_name: str
    booking_contract: int
    task_desc: str
    due_date: datetime.date
    cycle: int
    deliverable_id: int
    tasks: list[UserSDPClosedDeliverables]


__all__ = [
    "UserSDPActiveDeliverableHeader",
    "UserSDPActiveDeliverables",
    "UserSDPClosedDeliverables",
    "UserSDPClosedDeliverablesHeader",
    "UserSDPEngagementDeliverable",
    "UserSDPScheduledDeliverables",
    "UserSDPScheduledDeliverablesHeader",
]
