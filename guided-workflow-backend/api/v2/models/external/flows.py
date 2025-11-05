import datetime
from typing import Annotated, Literal

from pydantic.v1 import Field

from .. import TagsetTagModel, V2ConfigTagStrategy
from ..canvas import V2CanvasPredefinedFiles
from ..stored_proc import V2S3StagedFile
from ..workflows.macd import MacdAuditSchemaType
from . import Model


class ExtCreateCanvasPayload(Model):
    """
    Expected model payload for creating a canvas
    """

    request_id: int
    dc_user_id: int
    notification_id: int
    canvas_id: int
    dc_engagement_id: int
    extensions: list[V2CanvasPredefinedFiles]
    tag_ids: list[int]
    current_snapshot_name: str | None = Field(
        ...,
        description="The name of the snapshot to treat as the current snapshot."
        " If historical_snapshot_name is not None, this field defaults to the latest snapshot found.",
    )
    historical_snapshot_name: str | None = Field(
        ...,
        description="The name of the snapshot to treat as the historical snapshot."
        " If this field is not None, current_snapshot_name must not be None.",
    )
    customer_request_ids: list[int]
    collector_request_ids: list[int]


class ExtRebuildCanvasPayload(ExtCreateCanvasPayload):
    """
    Expected model payload for rebuilding a canvas
    """

    rebuild: bool = True


class ExtRefreshCanvasViewPayload(Model):
    """
    Expected model payload for refreshing a canvas view
    """

    canvas_id: int
    dc_user_id: int
    request_id: int
    notification_id: int
    dc_engagement_id: int


class ExtAcatDiscoveryPayload(Model):
    """
    Expected model payload for acat discovery
    """

    dc_engagement_id: int
    dc_user_id: int
    notification_id: int
    request_id: int
    requested_by: str


class ExtMacdAuditPayloadBase(Model):
    dc_engagement_id: int
    dc_user_id: int
    notification_id: int
    request_id: int
    requested_by: str
    period_start_date: datetime.date
    period_end_date: datetime.date


class ExtMacdAuditInstancePayload(ExtMacdAuditPayloadBase):
    """
    Expected model payload for Macd Audit Workflow
    """

    schema_type: Literal[MacdAuditSchemaType.instance_id] = (
        MacdAuditSchemaType.instance_id
    )
    file_uri: str


class ExtMacdAuditSerialPayload(ExtMacdAuditPayloadBase):
    """
    Expected model payload for Macd Audit Workflow
    """

    schema_type: Literal[MacdAuditSchemaType.serial_number] = (
        MacdAuditSchemaType.serial_number
    )
    file_uri: str


class ExtMacdAuditSkipPayload(ExtMacdAuditPayloadBase):
    """
    Expected model payload for Macd Audit Workflow when no file is provided
    """

    schema_type: Literal[MacdAuditSchemaType.skip] = MacdAuditSchemaType.skip
    file_uri: Literal[None] = None


ExtMacdAuditPayload = Annotated[
    ExtMacdAuditInstancePayload | ExtMacdAuditSerialPayload | ExtMacdAuditSkipPayload,
    Field(discriminator="schema_type"),
]


def get_macd_ext_audit_cls(
    schema_type: MacdAuditSchemaType,
) -> type[
    ExtMacdAuditSkipPayload | ExtMacdAuditSerialPayload | ExtMacdAuditInstancePayload
]:
    """
    Returns the appropriate MacdAuditPayload class based on the schema type.
    """
    if schema_type == MacdAuditSchemaType.instance_id:
        cls = ExtMacdAuditInstancePayload
    elif schema_type == MacdAuditSchemaType.serial_number:
        cls = ExtMacdAuditSerialPayload
    elif schema_type == MacdAuditSchemaType.skip:
        cls = ExtMacdAuditSkipPayload
    else:
        raise ValueError(f"Unknown schema type: {schema_type}")
    cls.update_forward_refs()
    return cls


class ExtCreateTagHistoryPayload(Model):
    """
    Expected model payload for creating tag history report
    """

    dc_engagement_id: int
    notification_id: int
    request_id: int
    requested_by: str
    id_type: Literal["instance_id", "serial_number"]
    snowflake_uri: V2S3StagedFile
    from_date: datetime.date
    tagset_ids: list[int]


class ExtHostNameRelinkPayload(Model):
    """
    Expected model payload for hostname relink
    """

    dc_engagement_id: int
    dc_user_id: int
    notification_id: int
    request_id: int
    requested_by: str


class ExtTaggingPayload(Model):
    """
    Expected model payload for instance tagging or serial number tagging
    """

    request_id: int
    dc_user_id: int
    notification_id: int
    tagset_tag_ids: list[TagsetTagModel]
    dc_engagement_id: int
    comment: str
    cisco_cco_id: str
    snowflake_uri: V2S3StagedFile
    action: Literal["set"] = "set"
    config_strategy: V2ConfigTagStrategy | None = None


class ExtBulkTaggingPayload(Model):
    """
    Expected model payload for bulk instance tagging
    """

    request_id: int
    dc_user_id: int
    notification_id: int
    dc_engagement_id: int
    comment: str
    cisco_cco_id: str
    snowflake_uri: V2S3StagedFile
    action: Literal["set"] = "set"
    config_strategy: V2ConfigTagStrategy | None = None
    id_type: Literal["instance_id", "serial_number"]


class ExtEvidenceCustomerPayload(Model):
    request_id: int
    notification_id: int
    dc_engagement_id: int
    cisco_cco_id: str
    snowflake_uri: V2S3StagedFile
    file_name_id: int
    source: str
    effective_date: datetime.date
    schema_type: Literal["instance_id", "serial_number"]
    note: str | None = ""


class ExtEvidenceCollectorPayload(Model):
    request_id: int
    notification_id: int
    dc_engagement_id: int
    cisco_cco_id: str
    snowflake_uri: V2S3StagedFile
    file_name_id: int
    source: str
    effective_date: datetime.date
    schema_type: Literal["instance_id", "serial_number"]
    note: str | None = ""


class ExtThoughtSpotTaggingPayload(Model):
    request_id: int
    notification_id: int
    dc_engagement_id: int
    cisco_cco_id: str
    dc_user_id: int
    thoughtspot_ids: list[int]
    config_strategy: V2ConfigTagStrategy | None = None
