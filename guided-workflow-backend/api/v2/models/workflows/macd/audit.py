import datetime
from typing import Annotated, Literal, Union

from pydantic.v1 import Field

from api.v2.models import Model, StrEnum


class MacdAuditSchemaType(StrEnum):
    instance_id = "instance_id"
    serial_number = "serial_number"
    skip = "skip"


class MacdAuditPayloadInstanceId(Model):
    schema_type: Literal[MacdAuditSchemaType.instance_id] = (
        MacdAuditSchemaType.instance_id
    )
    period_start_date: datetime.date = Field(
        description="The start date of the period for which the audit is being performed. Inclusive.",
    )
    period_end_date: datetime.date = Field(
        description="The end date of the period for which the audit is being performed. Inclusive.",
    )
    dc_engagement_id: int


class MacdAuditPayloadSerialNumber(Model):
    schema_type: Literal[MacdAuditSchemaType.serial_number] = (
        MacdAuditSchemaType.serial_number
    )
    period_start_date: datetime.date = Field(
        description="The start date of the period for which the audit is being performed. Inclusive.",
    )
    period_end_date: datetime.date = Field(
        description="The end date of the period for which the audit is being performed. Inclusive.",
    )
    dc_engagement_id: int


class MacdAuditNoPayload(Model):
    schema_type: Literal[MacdAuditSchemaType.skip] = MacdAuditSchemaType.skip
    period_start_date: datetime.date = Field(
        description="The start date of the period for which the audit is being performed. Inclusive.",
    )
    period_end_date: datetime.date = Field(
        description="The end date of the period for which the audit is being performed. Inclusive.",
    )
    dc_engagement_id: int


MacdAuditPayload = Annotated[
    MacdAuditPayloadSerialNumber | MacdAuditPayloadInstanceId | MacdAuditNoPayload,
    Field(discriminator="schema_type"),
]
