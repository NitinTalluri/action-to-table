from datetime import datetime
from typing import Any, Optional, Union

from pydantic.v1 import Field

from api.v2.models import V2SupportStatus

from . import Model

TSupportEvidence = Union[dict[str, Any], list[dict[str, Any]], list[Any]]


class SupportCaseCreatePayload(Model):
    comments: str
    subject: str
    path: str
    support_evidence: Optional[TSupportEvidence] = None

    class Config:
        schema_extra = {
            "examples": [
                {
                    "comments": "I get an error when I try to delete an engagement",
                    "subject": "Error Deleting Engagement",
                    "path": "/api/v2/engagements",
                    "support_evidence": {
                        "canvas_id": 123,
                    },
                }
            ]
        }


class SupportCaseModel(SupportCaseCreatePayload):
    case_id: int
    user_id: int
    status: V2SupportStatus
    create_dtm: datetime
    update_dtm: Optional[datetime]
    resolved_dtm: Optional[datetime]
    agent_comments: Optional[str]
    agent_id: Optional[int]
    root_cause_id: Optional[int]


class SupportCaseAgentModel(SupportCaseModel):
    dc_theater: Optional[str] = Field(
        ..., description="The theater of the user who submitted the case"
    )


class SupportCaseAgentUpdatePayload(Model):
    """All fields are optional"""

    is_resolved: Optional[bool] = None
    agent_comments: Optional[str] = None
    agent_id: Optional[int] = None
    root_cause_id: Optional[int] = None


class SupportCaseUserClosedPayload(Model):
    comments: Optional[str] = None
