import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TypedDict, Union
from zoneinfo import ZoneInfo

import boto3
from pydantic.v1 import (
    BaseSettings,
    Field,
    SecretStr,
    constr,
    root_validator,
    validator,
)

from api.prefect_settings import RunConfigSetting

if TYPE_CHECKING:
    from prefect.run_configs import DockerRun, KubernetesRun
    from pydantic.env_settings import EnvSettingsSource

    TUUID = str
    TFlowLabels = list[str]
    TFlowConfig = DockerRun | KubernetesRun | None


class FlowSettings(TypedDict):
    version_group_id: str
    labels: list[str]
    run_config: Union["DockerRun", "KubernetesRun", None]


logger = logging.getLogger("api")


class Environment(str, Enum):
    dev = "dev"
    prod = "prod"
    test = "test"

    def __str__(self) -> str:
        return str.__str__(self)


class TagStoredProcSettings(BaseSettings):
    class Config:
        case_sensitive = False
        use_enum_values = True
        env_prefix = "PROC_"

    proc_schema: constr(to_lower=True) = Field(default=None, env="SCHEMA")
    tag_proc: constr(to_lower=True) = Field(default="tag_instances_11", env="TAG_NAME")
    tag_proc_v2: str = Field(default="tag_instances_v2", env="TAG_NAME_V2", lower=True)
    untag_proc: constr(to_lower=True) = Field(
        default="tag_instances_11", env="UNTAG_NAME"
    )
    bulk_tag_proc: constr(to_lower=True) = Field(
        default="bulk_tagging_v2", env="BULK_TAG_NAME"
    )


class TsTagRequestsStorage(BaseSettings):
    class Config:
        use_enum_values = True
        env_file = Path(__file__).parent.parent / ".env"

    bucket: str = Field(default="dsci.snowflake.storage", env="TS_TAG_REQUESTS_BUCKET")
    key: str = Field(default="thought_spot_tag_requests", env="TS_TAG_REQUESTS_KEY")
    env: Environment = Field(default=Environment.prod, env="RUN_ENV")

    @root_validator()
    def add_env(cls, values):
        """Append env to key"""
        key = values.get("key")
        if not key:
            raise ValueError("key is required")
        env = values.get("env")
        if not env:
            raise ValueError("env is required")
        values["key"] = f"{values['key']}/{env!s}"
        return values


class S3StagedFileUri(TypedDict):
    bucket: str
    key: str
    s3_uri: str
    snowflake_uri: str


class JsonStageFileStore(BaseSettings):
    class Config:
        use_enum_values = True
        env_file = Path(__file__).parent.parent / ".env"

    bucket: str = Field(
        default="dsci.snowflake.storage", env="JSON_STAGE__FILE_STORE_BUCKET"
    )
    key_prefix: str = Field(
        default="thought_spot_tag_requests",
        env="JSON_STAGE__FILE_STORE_KEY_PREFIX",
        description="The stage is defined to have a path of s3://<bucket>/<key_prefix>",
    )
    env: Environment = Field(default=Environment.prod, env="RUN_ENV")
    stage_name: str = Field(
        default="CPS_DSCI_STG.MY_CSV_STAGE", env="JSON_STAGE__STAGE_NAME"
    )
    stage_url: str = Field(
        default="s3://dsci.snowflake.storage/thought_spot_tag_requests",
        env="JSON_STAGE__STAGE_URL",
    )

    def make_staged_s3_uri(self, workflow: str, file_name: str) -> S3StagedFileUri:
        """
        Create the actual S3 URI for the file where
        s3://<self.bucket>/<self.key_prefix>/json/<self.env>/<workflow>/<file_name>
        And Snowflake would reference if as.
        @<self.stage_name>/json/<self.env>/<workflow>/<file_name>
        """
        bucket = self.bucket
        sf_key = f"json/{self.env!s}/{workflow}/{file_name}"
        snowflake_uri = f"@{self.stage_name}/{sf_key}"
        key = f"{self.key_prefix}/{sf_key}"
        s3_uri = f"s3://{bucket}/{key}"

        return S3StagedFileUri(
            bucket=bucket, key=key, s3_uri=s3_uri, snowflake_uri=snowflake_uri
        )


DEFAULT_KUBERNETES_JOB_TEMPLATE = {
    "apiVersion": "batch/v1",
    "kind": "Job",
    "spec": {
        "ttlSecondsAfterFinished": 300,  # Auto cleanup Job
        "template": {"spec": {"containers": [{"name": "flow"}]}},
    },
}

# If labeled with "runon" or "thought-spot" then we're running in Cisco internal
DEFAULT_CAE_KUBERNETES = {
    "name": "KubernetesRun",
    "parameters": {
        "memory_request": "1024Mi",
        "memory_limit": "2048Mi",
        "cpu_request": "1000m",
        "cpu_limit": "2000m",
        "service_account_name": "builder",
        "job_template": DEFAULT_KUBERNETES_JOB_TEMPLATE,
    },
}


class AwsSecretsSettingsSource:
    """Use AWS Secrets Manager as Custom Source"""

    def __init__(
        self,
        env_settings: "EnvSettingsSource",
        aws_region: str = "us-east-1",
    ):
        self.client = boto3.client(
            service_name="secretsmanager",
            region_name=aws_region,
        )
        # We'd like to get environment the typical way but we can't as this
        # is a custom source and run in classmethod

        self.env = env_settings._read_env_files(True).get("RUN_ENV", "prod")

    def __call__(self, settings: BaseSettings) -> dict[str, Any]:
        secrets: dict[str, Any] = {}
        if self.client is None:
            return secrets

        def get_secret_value(secret_name: str):
            return self.client.get_secret_value(SecretId=secret_name)["SecretString"]

        for field in settings.__fields__.values():
            secret_name = field.field_info.extra.get("secret_name")
            if not secret_name:
                continue
            secret_name = secret_name.format(env=self.env)
            secret_key = field.field_info.extra.get("secret_key")

            try:
                secret_val = get_secret_value(secret_name)
                if (field.is_complex() or "{" in secret_val) and secret_key:
                    secrets[field.name] = json.loads(secret_val)[secret_key]
                else:
                    secrets[field.name] = secret_val
            except Exception:
                logger.warning("Failed to retrieve secret %s", secret_name)
                continue

        return secrets


class PrefectSettings(BaseSettings):
    class Config:
        use_enum_values = True
        env_file = Path(__file__).parent.parent / ".env"

    auth_token: str = Field(env="PREFECT_AUTH_TOKEN")
    request_timeout: int = Field(default=60, env="PREFECT_REQUEST_TIMEOUT")
    json_requests_bucket: str = Field(
        default="dc-json-requests", env="PREFECT_JSON_REQUESTS_BUCKET"
    )
    extract_ts_version_group_id: str = Field(
        env="PREFECT_EXTRACT_TS_VERSION_GROUP_ID",
        default="bd98c2ec-9c25-4e8c-a23c-f9c894e48143",
    )
    extract_ts_flow_labels: list[str] = Field(
        env="PREFECT_EXTRACT_TS_FLOW_LABELS", default=["dev"]
    )
    extract_ts_run_config: Optional[RunConfigSetting] = Field(
        env="PREFECT_EXTRACT_TS_RUN_CONFIG", default=None
    )

    serial_tagging_version_group_id: str = Field(
        env="PREFECT_SERIAL_TAGGING_VERSION_GROUP_ID",
        default="fe5f3579-2207-4c2d-ad3a-71e8cd29feca",
    )
    serial_tagging_flow_labels: list[str] = Field(
        env="PREFECT_SERIAL_TAGGING_FLOW_LABELS",
        default=["dev"],
    )
    serial_tagging_run_config: RunConfigSetting = Field(
        env="PREFECT_SERIAL_TAGGING_RUN_CONFIG",
        default={
            "name": "KubernetesRun",
            "parameters": {"labels": ["dev"]},
        },
    )

    site_report_version_group_id: str = Field(
        env="PREFECT_SITE_REPORT_VERSION_GROUP_ID",
        default="a8a9fcb3-fe0a-4b4d-973c-42057e6e80a4",
    )
    site_report_flow_labels: list[str] = Field(
        env="PREFECT_SITE_REPORT_FLOW_LABELS",
        default=["thought-spot", "ds-server-docker"],
    )
    site_report_run_config: Optional[RunConfigSetting] = Field(
        env="PREFECT_SITE_REPORT_RUN_CONFIG",
        default=DEFAULT_CAE_KUBERNETES,
    )
    snif_report_version_group_id: str = Field(
        env="PREFECT_SNIF_REPORT_VERSION_GROUP_ID",
        default="2dbd75b8-a24e-402e-b749-59fbc5604433",
    )
    snif_report_flow_labels: list[str] = Field(
        env="PREFECT_SNIF_REPORT_FLOW_LABELS",
        default=["thought-spot", "ds-server-docker"],
    )
    snif_report_run_config: RunConfigSetting = Field(
        env="PREFECT_SNIF_REPORT_RUN_CONFIG",
        default=DEFAULT_CAE_KUBERNETES,
    )
    evidence_collector_version_group_id: str = Field(
        env="PREFECT_EVIDENCE_COLLECTOR_VERSION_GROUP_ID",
        default="da7746d2-fe0a-49a2-bd88-978c2570eb92",
    )
    evidence_collector_flow_labels: list[str] = Field(
        env="PREFECT_EVIDENCE_COLLECTOR_FLOW_LABELS", default=["dev"]
    )
    evidence_collector_run_config: Optional[RunConfigSetting] = Field(
        env="PREFECT_EVIDENCE_COLLECTOR_RUN_CONFIG", default=None
    )

    generic_upload_version_group_id: str = Field(
        env="PREFECT_GENERIC_UPLOAD_VERSION_GROUP_ID",
        default="a4517ca1-c059-4dbc-8b54-dde23b60c70d",
    )
    generic_upload_flow_labels: list[str] = Field(
        env="PREFECT_GENERIC_UPLOAD_FLOW_LABELS", default=["dev"]
    )
    generic_upload_run_config: RunConfigSetting = Field(
        env="PREFECT_GENERIC_UPLOAD_RUN_CONFIG",
        default={"name": "KubernetesRun", "parameters": {"memory_request": "6G"}},
    )
    host_name_site_moves_version_group_id: str = Field(
        env="PREFECT_HOST_NAME_SITE_MOVES_VERSION_GROUP_ID",
        default="388f523c-f473-47e6-bd89-340a3a08cbb1",
    )
    host_name_site_moves_flow_labels: list[str] = Field(
        env="PREFECT_HOST_NAME_SITE_MOVES_FLOW_LABELS", default=["dev"]
    )
    host_name_site_moves_run_config: RunConfigSetting = Field(
        env="PREFECT_HOST_NAME_SITE_MOVES_RUN_CONFIG",
        default={"name": "KubernetesRun", "parameters": {"memory_request": "6G"}},
    )
    service_level_version_group_id: str = Field(
        env="PREFECT_SERVICE_LEVEL_VERSION_GROUP_ID",
        default="3c413e28-1fd8-4f70-8032-00acd6feb077",
    )
    service_level_flow_labels: list[str] = Field(
        env="PREFECT_SERVICE_LEVEL_FLOW_LABELS",
        default=["dev"],
    )
    service_level_run_config: RunConfigSetting = Field(
        env="PREFECT_SERVICE_LEVEL_RUN_CONFIG",
        default={"name": "KubernetesRun", "parameters": {"memory_request": "6G"}},
    )

    @staticmethod
    def config_to_object(
        setting: Optional["RunConfigSetting"],
    ) -> "TFlowConfig":
        if setting is None:
            return None
        try:
            return setting.to_object()
        except Exception as e:
            logger.error("Error converting run config setting to object: %s", e)
            return None

    @property
    def extract_ts_settings(self) -> "FlowSettings":
        return {
            "version_group_id": self.extract_ts_version_group_id,
            "labels": self.extract_ts_flow_labels,
            "run_config": self.config_to_object(self.extract_ts_run_config),
        }

    @property
    def serial_tagging_settings(self) -> "FlowSettings":
        return {
            "version_group_id": self.serial_tagging_version_group_id,
            "labels": self.serial_tagging_flow_labels,
            "run_config": self.config_to_object(self.serial_tagging_run_config),
        }

    @property
    def site_report_settings(self) -> "FlowSettings":
        return {
            "version_group_id": self.site_report_version_group_id,
            "labels": self.site_report_flow_labels,
            "run_config": self.config_to_object(self.site_report_run_config),
        }

    @property
    def snif_report_settings(self) -> "FlowSettings":
        return {
            "version_group_id": self.snif_report_version_group_id,
            "labels": self.snif_report_flow_labels,
            "run_config": self.config_to_object(self.snif_report_run_config),
        }

    @property
    def evidence_customer_settings(self) -> "FlowSettings":
        return {
            "version_group_id": self.evidence_customer_version_group_id,
            "labels": self.evidence_customer_flow_labels,
            "run_config": self.config_to_object(self.evidence_customer_run_config),
        }

    @property
    def evidence_collector_settings(self) -> "FlowSettings":
        return {
            "version_group_id": self.evidence_collector_version_group_id,
            "labels": self.evidence_collector_flow_labels,
            "run_config": self.config_to_object(self.evidence_collector_run_config),
        }

    @property
    def generic_upload_settings(self) -> "FlowSettings":
        return {
            "version_group_id": self.generic_upload_version_group_id,
            "labels": self.generic_upload_flow_labels,
            "run_config": self.config_to_object(self.generic_upload_run_config),
        }

    @property
    def host_name_site_moves_settings(self) -> "FlowSettings":
        return {
            "version_group_id": self.host_name_site_moves_version_group_id,
            "labels": self.host_name_site_moves_flow_labels,
            "run_config": self.config_to_object(self.host_name_site_moves_run_config),
        }

    @property
    def service_level_settings(self) -> "FlowSettings":
        return {
            "version_group_id": self.service_level_version_group_id,
            "labels": self.service_level_flow_labels,
            "run_config": self.config_to_object(self.service_level_run_config),
        }


class PrefectV3Settings(BaseSettings):
    class Config:
        case_sensitive = False
        use_enum_values = True
        env_file = Path(__file__).parent.parent / ".env"
        aws_region = "us-east-1"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            """For fields that define at least `secret_name`, use AWS Secrets Manager as a source"""
            aws_secrets_source = AwsSecretsSettingsSource(env_settings, cls.aws_region)
            return (
                init_settings,
                aws_secrets_source,
                env_settings,
                file_secret_settings,
            )

    api_key: str = Field(
        default=None,
        env="PREFECT_V3_API_KEY",
        secret_name="{env}/prefect/v3/worker/api_key",
        secret_key="API_KEY",
    )
    api_version: str = Field(default="0.8.4", env="PREFECT_V3_API_VERSION")
    api_url: str = Field(default="https://api.prefect.cloud", env="PREFECT_V3_API_URL")
    account_id: str = Field(
        default="421a2ff7-ff12-46b7-9d43-8f012c9bb18a", env="PREFECT_V3_ACCOUNT_ID"
    )
    workspace_id: str = Field(
        default="70c6c7e5-7706-4c2d-a3be-7cd81a5ce5c4", env="PREFECT_V3_WORKSPACE_ID"
    )


DEFAULT_DB_SESSION_PARAMETERS = {
    "abort_detached_query": True,
    "statement_timeout_in_seconds": 1800,
    "client_session_keep_alive": False,
}


class AppSettings(BaseSettings):
    class Config:
        case_sensitive = False
        use_enum_values = True
        env_file = Path(__file__).parent.parent / ".env"

    user_pool_id: str = Field(default=None, env="USER_POOL_ID")
    app_client_id: str = Field(default=None, env="APP_CLIENT_ID")
    aws_region: str = Field(default=None, env="REGION")
    role: str = Field(default=None, env="ROLE")
    env: Environment = Field(default=Environment.prod, env="RUN_ENV")
    db_schema: constr(to_lower=True) = Field(default=None, env="SCHEMA")
    db_string_secret: SecretStr = Field(default=None, env="DB_STRING_SECRET")
    db_timezone: ZoneInfo = Field(default="America/Los_Angeles", env="DB_TIMEZONE")
    db_url: Optional[SecretStr] = Field(
        default=None,
        env="DB_URL",
        description="Database URL Can be set directly for local development",
    )
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_pool_max_overflow: int = Field(default=40, env="DB_POOL_MAX_OVERFLOW")
    db_pool_pre_ping: bool = Field(default=False, env="DB_POOL_PRE_PING")
    db_session_parameters: dict = Field(
        default_factory=lambda: DEFAULT_DB_SESSION_PARAMETERS,
        env="DB_SESSION_PARAMETERS",
    )
    db_warehouse: str = Field(default="CPS_DSCI_ETL_EXT2_WH", env="WAREHOUSE")
    db_tagging_warehouse: str = Field(
        default="CPS_DSCI_ETL_EXT4_WH", env="TAGGING_WAREHOUSE"
    )
    ts_tag_requests_settings: TsTagRequestsStorage = None
    json_stage_file_store: JsonStageFileStore = None
    tag_proc_settings: TagStoredProcSettings = None
    prefect_settings: PrefectSettings = None
    prefect_v3_settings: PrefectV3Settings = None
    booking_extension_count_limit: int = 2
    booking_extension_days: int = 90
    announcement_dashboard_limit: int = 6
    docs_bucket: str = Field("dc.docs", env="DOCS_BUCKET")
    static_html_filename: str = Field("static_view.html", env="STATIC_HTML_FILENAME")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tag_proc_settings = TagStoredProcSettings(proc_schema=self.db_schema)
        self.ts_tag_requests_settings = TsTagRequestsStorage()
        self.json_stage_file_store = JsonStageFileStore()
        self.prefect_settings = PrefectSettings()
        self.prefect_v3_settings = PrefectV3Settings()

    @validator("db_timezone", pre=True, always=True)
    def validate_timezone(cls, v):
        match v:
            case str():
                return ZoneInfo(v)
            case ZoneInfo():
                return v
            case _:
                return ZoneInfo("America/Los_Angeles")

    def get_db_datetime_now(self):
        # Get naive datetime now in db timezone
        return datetime.now().astimezone(self.db_timezone).replace(tzinfo=None)

    @property
    def static_html_key(self) -> str:
        return f"{self.env!s}/{self.static_html_filename}"


class S3StageFile(TypedDict):
    """
    This appears redundant, but in snowflake, we would get
    s3://dsci.snowflake.storage/thought_spot_tag_requests/json/dev/some_file.json.gz

    With
    FROM @CPS_DSCI_STG.MY_CSV_STAGE/json/dev/json_blob.json
    (FILE_FORMAT => CPS_DSCI_BR.JSON_FILE_FORMAT)

    The `thought_spot_tag_requests` has to be removed from the stage
    """

    s3_bucket: str
    s3_key: str
    file_name: str
    sf_file_path: str
