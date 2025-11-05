from . import Model


class AdminSDPQueryAllResponse(Model):
    deliverable_id: int
    deliverable_desc: str
    task_id: int
    task_desc: str
    task_hours: float
    task_frequency: int
    task_anchor_date_id: int
    task_anchor_date_name: str
    task_cycle_iterator_id: int
    task_cycle_iterator_name: str
    sub_task_id: int
    subtask_desc: str
    subtask_hours: float
    subtask_frequency: int
    subtask_cycle_days: int
