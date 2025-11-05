import datetime
import json
from enum import Enum
from typing import Any, Literal, Optional

from pydantic.v1 import Field, conint, constr, root_validator, validator

from . import Model, V2ConfigTagStrategy


class V2TagAction(str, Enum):
    set = "set"
    unset = "unset"
    extract = "extract"

    def __str__(self) -> str:
        return str.__str__(self)


class V2LinkAction(str, Enum):
    link = "link"
    unlink = "unlink"

    def __str__(self) -> str:
        return str.__str__(self)


class V2ProcedureNames(str, Enum):
    link_sdp = "link_sdp"
    link_sdp_subtask_enablements = "link_sdp_sub_task_to_enablements"
    create_super_customer = "create_super_customer"
    update_super_customer = "update_super_customer"
    delete_super_customer = "delete_super_customer"
    load_sea_data = "load_sea_data"
    load_macd_data = "load_macd_data"

    def __str__(self) -> str:
        return str.__str__(self)


class V2TaggingStoredProcedureParams(Model):
    action: V2TagAction = Field(exclude=True)
    config_strategy: Optional[V2ConfigTagStrategy]
    user_id: constr(regex=r"[a-z\d_-]+@cisco.com") = Field(default=None, alias="userId")
    engagement_id: conint(ge=0) = Field(default=None, alias="engagementId")
    comment: str = Field(default="", title="Comment")
    instance_ids: list[conint(ge=0)] = Field(default=None, alias="instance")

    @validator("instance_ids", pre=True)
    def validate_instance_ids(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class V2TagInstancesParams(V2TaggingStoredProcedureParams):
    tag_id: conint(ge=0) = Field(default=None, alias="tagId")
    ddl_action: str = None
    action: Literal[V2TagAction.set] = Field(exclude=True, default=V2TagAction.set)
    config_strategy: Optional[V2ConfigTagStrategy] = Field(
        exclude=True,
        description="Tag Selected Instance Ids : 'null', "
        "'Tag & Overwrite the Full Config:'config-all', "
        "'Tag Nulls on The Full Config': '', 'Tag Instances Where Config is Null': 'config-null'",
    )
    instance_ids: list[conint(ge=0)] = Field(default=None, alias="instance")

    @root_validator(pre=True)
    def make_ddl_action(cls, values):
        action, strategy = values.get("action"), values.get("config_strategy")
        match (action, strategy):
            case (None, _):
                raise ValueError("action is required")
            case (x, _) if x != V2TagAction.set:
                raise ValueError(f"action must be {V2TagAction.set}")
            case (_, None):
                values["ddl_action"] = "set"
                return values
            case (_, V2ConfigTagStrategy.config_null):
                values["ddl_action"] = "set-config-null"
                return values
            case (_, V2ConfigTagStrategy.config_all):
                values["ddl_action"] = "set-config-all"
                return values
            case (_, V2ConfigTagStrategy.null):
                values["ddl_action"] = "set-null"
                return values
            case _:
                raise ValueError(f"Invalid config strategy {strategy}")

    def get_config_strategy_description(self):
        strategy = self.config_strategy
        match strategy:
            case None:
                return "Tag Selected Instance Ids"
            case V2ConfigTagStrategy.config_all:
                return "Tag & Overwrite the Full Config"
            case V2ConfigTagStrategy.config_null:
                return "Tag Nulls on The Full Config"
            case V2ConfigTagStrategy.null:
                return "Tag Instances Where Config is Null"
            case _:
                return "Default"


class V2UntagInstancesParams(V2TaggingStoredProcedureParams):
    action: V2TagAction = Field(default=V2TagAction.unset)
    config_strategy: Literal[None] = None
    tag_id: None = Field(default=None, alias="tagId")
    tagset_id: conint(ge=0) = Field(default=None, alias="tagsetId")
    ddl_action: str = "unset"
    instance_ids: list[conint(ge=0)] = Field(default=None, alias="instance")


class V2TaggingInstances(V2TaggingStoredProcedureParams):
    action: V2TagAction = Field(default=V2TagAction.set, alias="ddl_action")
    tag_id: conint(ge=0) = Field(default=None, alias="tagId")
    tagset_id: conint(ge=0) = Field(default=None, alias="tagsetId")
    instance_ids: list[conint(ge=0)] = Field(default=None, alias="instance")


class V2SPParamsBase(Model):
    logged_user: str = Field(..., description="The logged in user's email address")


class V2LinkSDPParams(V2SPParamsBase):
    action: V2LinkAction
    task_id: int
    sub_task_id: int


class V2LinkSDPSubtaskEnablementsParams(V2SPParamsBase):
    sub_task_id: int
    sold_as_service_type_ids: list[int]
    pricing_type_ids: list[int]
    buying_program_type_ids: list[int]


class V2CreateSuperCustomerParams(V2SPParamsBase):
    """Parameters for the create_super_customer stored procedure"""

    super_customer_name: str
    dc_engagement_ids: set[int] = Field(default_factory=set)


class V2UpdateSuperCustomerParams(V2SPParamsBase):
    """Parameters for the update_super_customer stored procedure"""

    super_customer_id: int
    super_customer_name: str
    dc_engagement_ids: set[int]


class V2DeleteSuperCustomerParams(V2SPParamsBase):
    """Parameters for the delete_super_customer stored procedure"""

    super_customer_id: int


class V2S3StagedFile(Model):
    bucket: str = Field(description="S3 bucket name")
    key: str = Field(description="S3 object key")
    s3_uri: str = Field(description="S3 URI of the file")
    snowflake_uri: str = Field(description="Snowflake flavored URI of S3")


class V2SEAUploadParams(Model):
    dc_engagement_id: int = Field(alias="engagement_id")
    request_id: int
    dc_user_id: int
    cisco_cco_id: str
    notification_id: int
    staged_file: V2S3StagedFile = Field(
        description="Staged file in S3 for SEA upload",
    )
    snowflake_uri: str = Field(
        description="Snowflake flavored URI of S3. Will be automatically generated from the staged_file"
        "during root validation"
    )

    @root_validator(pre=True)
    def extract_snowflake_uri(cls, values):
        staged_file = values.get("staged_file")
        if staged_file:
            values["snowflake_uri"] = staged_file.snowflake_uri
        return values


class V2MACDUploadParams(Model):
    approved_by: Optional[str]
    cisco_cco_id: str
    dc_engagement_id: int = Field(alias="engagement_id")
    dc_user_id: int
    sign_off_identity_id: Optional[str]
    effective_date: datetime.date = Field()
    notes: Optional[str]
    notification_id: int
    request_id: int
    tool_action: str
    tool_name: str
    staged_file: V2S3StagedFile = Field(
        description="Staged file in S3 for MACD upload",
    )
    snowflake_uri: str = Field(
        description="Snowflake flavored URI of S3. Will be automatically generated from the staged_file"
        "during root validation"
    )

    @root_validator(pre=True)
    def extract_snowflake_uri(cls, values):
        staged_file = values.get("staged_file")
        if staged_file:
            values["snowflake_uri"] = staged_file.snowflake_uri
        return values


class V2StoredProcedureResult(Model):
    success: bool = False
    message: str = Field(default="")
    code: int = Field(default=200)
    logs: list[str] | None = None
