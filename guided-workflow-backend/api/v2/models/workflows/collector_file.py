import datetime
from typing import Literal

from pydantic.v1 import Field

from .. import Model


class V2CollectorFileUpload(Model):
    file_name_id: int = Field(description="The Id of the User Defined Type")
    effective_date: datetime.date = Field(description="Effective Date")
    source: str | None = Field(None, description="Source")
    note: str | None = Field(None, description="Notes")
    dc_engagement_id: int = Field(description="Engagement ID")
