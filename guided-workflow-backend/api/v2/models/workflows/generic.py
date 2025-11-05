from typing import Literal, Optional

from pydantic.v1 import Field

from .. import Model


class V2GenericResponse(Model):
    message: str
    success: bool


class V2GenericJobResponse(Model):
    request_id: int = Field(
        ..., title="Request ID assigned to this job. Generated from the database."
    )
    notification_id: Optional[int] = Field(
        ...,
        title="Notification ID assigned to this job. Generated from the database.",
    )
    external_job_id: Optional[str] = Field(
        None,
        title="External Identifier for the Workflow Job, e.g. Prefect Flow Group ID",
    )
    external_run_id: Optional[str] = Field(
        None, title="External Identifier for the Workflow Run, e.g. Prefect Flow Run ID"
    )
    message: str = Field("", title="Message")
    success: Literal[True] = Field(default=True, title="Success Flag")


class V2GenericJobErrorResponse(Model):
    request_id: Optional[int] = Field(
        None, title="Request ID assigned to this job. Generated from the database."
    )
    notification_id: Optional[int] = Field(
        None, title="Notification ID assigned to this job. Generated from the database."
    )
    external_job_id: Optional[str] = Field(
        None,
        title="External Identifier for the Workflow Job, e.g. Prefect Flow Group ID",
    )
    external_run_id: Optional[str] = Field(
        None, title="External Identifier for the Workflow Run, e.g. Prefect Flow Run ID"
    )
    message: str = Field("", title="Message")
    success: Literal[False] = Field(False, title="Success Flag")
