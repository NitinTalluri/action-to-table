from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic.v1 import Field

from . import Model, TrueFalse


class V2RecordMetaData(Model):
    created_by: Optional[str] = Field(None, example="exampleuser@example.org")
    create_dtm: Optional[datetime] = None
    update_dtm: Optional[datetime] = None
    updated_by: Optional[str] = None
    is_deleted: Optional[TrueFalse] = None
