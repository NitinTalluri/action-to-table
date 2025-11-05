import logging
from typing import Literal, Optional, TypedDict

from pydantic.v1 import Field, root_validator

from .. import Model, V2ConfigTagStrategy, V2TagAction

logger = logging.getLogger("api")


def make_ddl_action(cls, values):
    strategy = values.get("config_strategy")
    match strategy:
        case None:
            ddl_action = "set"
        case V2ConfigTagStrategy.null | "null":
            ddl_action = "set-null"
        case V2ConfigTagStrategy.config_null | "config-null":
            ddl_action = "set-config-null"
        case V2ConfigTagStrategy.config_all | "config-all":
            ddl_action = "set-config-all"
        case _:
            logger.error("Invalid config strategy: %s, returning 'set'", strategy)
            ddl_action = "set"
    values["ddl_action"] = ddl_action
    return values


class V2SerialTaggingPayload(Model):
    tag_ids: list[int] = Field(..., title="Tag IDs")
    engagement_id: int = Field(..., title="Engagement ID")
    comment: Optional[str] = Field("", title="Comment")
    action: Literal[V2TagAction.set] = Field(
        exclude=True, default=V2TagAction.set, const=True
    )
    config_strategy: Optional[V2ConfigTagStrategy] = Field(
        exclude=True,
        description="Tag Selected Instance Ids : 'null', "
        "'Tag & Overwrite the Full Config:'config-all', "
        "'Tag Nulls on The Full Config': '', 'Tag Instances Where Config is Null': 'config-null'",
    )
    ddl_action: Optional[str] = None

    _make_ddl_action = root_validator(pre=True, allow_reuse=True)(make_ddl_action)

    class Config:
        schema_extra = {
            "examples": [
                {
                    "tag_ids": [123456, 123459],
                    "engagement_id": 94,
                    "comment": "Tagging Serial Numbers",
                    "config_strategy": "null",
                },
            ]
        }


class V2BulkRowData(TypedDict):
    id: int | str  # instance_id or serial_number
    tagsets: dict[int, str]


class V2BulkInstanceTaggingPayload(Model):
    id_type: Literal["instance_id", "serial_number"] = Field(
        "instance_id", title="ID Type"
    )
    engagement_id: int = Field(..., title="Engagement ID", example=94)
    comment: str = Field(default="", title="Comment")
    action: Literal[V2TagAction.set] = Field(
        exclude=True, default=V2TagAction.set, const=True
    )
    config_strategy: Optional[V2ConfigTagStrategy] = Field(
        exclude=True,
        description="Tag Selected Instance Ids : 'null', "
        "'Tag & Overwrite the Full Config:'config-all', "
        "'Tag Nulls on The Full Config': '', 'Tag Instances Where Config is Null': 'config-null'",
    )
    ddl_action: Optional[str] = None

    class Config:
        schema_extra = {
            "examples": [
                {
                    "id_type": "instance_id",
                    "engagement_id": 94,
                    "comment": "Tagging Serial Numbers",
                    "config_strategy": "config-null",
                },
            ]
        }


class V2BulkInstanceTaggingParams(Model):
    engagement_id: int = Field(..., title="Engagement ID")
    comment: str = Field("", title="Comment")
    cisco_cco_id: str = Field(..., title="Cisco CCO ID")
    id_type: Literal["instance_id", "serial_number"] = Field(..., title="ID Type")
    config_strategy: Optional[V2ConfigTagStrategy] = Field(..., title="Config Strategy")
    action: Literal[V2TagAction.set] = Field(
        exclude=True, default=V2TagAction.set, const=True
    )
    snowflake_uri: str = Field(
        description="The FQN of a Snowflake Stage and File Path",
        example="@CPS_DSCI_STG.MY_CSV_STAGE/json/dev/bulk_instance_tagging/json_blob.json.gz",
    )
    ddl_action: str = None
    notification_id: Optional[int] = None

    @classmethod
    def from_payload(
        cls,
        payload: V2BulkInstanceTaggingPayload,
        cisco_cco_id: str,
        snowflake_uri: str,
    ):
        engagement_id = payload.engagement_id
        id_type = payload.id_type
        strategy = payload.config_strategy
        comment = payload.comment

        match strategy:
            case None:
                ddl_action = "set"
            case V2ConfigTagStrategy.null | "null":
                ddl_action = "set-null"
            case V2ConfigTagStrategy.config_null | "config-null":
                ddl_action = "set-config-null"
            case V2ConfigTagStrategy.config_all | "config-all":
                ddl_action = "set-config-all"
            case _:
                logger.error("Invalid config strategy: %s, returning 'set'", strategy)
                ddl_action = "set"

        return cls(
            engagement_id=engagement_id,
            cisco_cco_id=cisco_cco_id,
            id_type=id_type,
            comment=comment,
            ddl_action=ddl_action,
            config_strategy=payload.config_strategy,
            snowflake_uri=snowflake_uri,
        )
