import datetime
from typing import Optional

from pydantic.v1 import Field, root_validator

from api.v2.models import Model

from . import TToolNameLiteral
from .base import SchemaModelBase


class MacdHeaderResponseRow(Model):
    request_id: int
    dc_engagement_id: int
    dc_user_id: int
    sign_off_identity_id: int | None
    row_count: int
    approved_by: str | None
    effective_date: datetime.date | None
    tool_name: str
    tool_action: str
    notes: str | None
    created_by: str
    create_dtm: datetime.date
    update_dtm: datetime.date | None
    updated_by: str | None


class MacdSubmissionPayload(SchemaModelBase):
    dc_engagement_id: int
    sign_off_identity_id: Optional[int] = Field(
        description="References 'dc_typ_sign_off_identity'"
    )
    approved_by: Optional[str]
    effective_date: datetime.date
    notes: Optional[str]

    @root_validator
    def validate_fields(cls, values):
        """
        Validates fields for non-historical tool_name:
        sign_off_identity_id, approved_by and effective_date must be present.
        """

        tool_name = values.get("tool_name")

        if tool_name != "historical":
            missing_fields = []

            if values.get("sign_off_identity_id") is None:
                missing_fields.append("sign_off_identity_id")
            if values.get("approved_by") is None:
                missing_fields.append("approved_by")
            if values.get("effective_date") is None:
                missing_fields.append("effective_date")

            if missing_fields:
                raise ValueError(
                    f"The following fields are required when tool_name is not 'historical': "
                    f"{', '.join(missing_fields)}"
                )
        return values
