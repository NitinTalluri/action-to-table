import json
import logging
from typing import (
    TYPE_CHECKING,
    Literal,
    NamedTuple,
    Optional,
    TypedDict,
    Union,
)

from fastapi.encoders import jsonable_encoder

from api.v2.models import (
    TextMessageCreate,
)

from .. import S3Mixin, ServiceException, SessionMixin

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from prefect import Client
    from sqlmodel import Session

    from api.settings import AppSettings
    from api.v2 import ExternalServiceTracker
    from api.v2.models.workflows.collector_file import (
        TCollectorRowModel,
        V2CollectorFileUpload,
    )
    from api.v2.models.workflows.customer_file import (
        TCustomerRowModel,
        V2CustomerFileUpload,
    )
    from api.v2.orm import V2User


logger = logging.getLogger("api")


class ServiceLevelFlowRow(TypedDict):
    instance_id: Optional[int]
    serial_number: Optional[str]
    expected_service_level: str


class FlowRunResult(NamedTuple):
    external_job_id: str
    external_run_id: str
    job_parameters: dict
    request_id: Optional[int]
    notification_id: Optional[int]


class PrefectFlowService(SessionMixin, S3Mixin):
    def __init__(
        self,
        prefect_client: "Client",
        s3_client: "S3Client",
        settings: "AppSettings",
        session: "Session",
    ):
        SessionMixin.__init__(self, session)
        S3Mixin.__init__(self, s3_client)
        self.prefect_client = prefect_client
        self.settings = settings

    def _create_evidence_flow(
        self,
        dc_engagement_id: int,
        payload: Union[
            "V2CustomerFileUpload",
            "V2CollectorFileUpload",
        ],
        data: Union[
            "TCollectorRowModel",
            "TCustomerRowModel",
        ],
        requested_by: str,
        tracker: "ExternalServiceTracker",
        flow_type: Literal["customer", "collector"],
    ):
        prefect_settings = self.settings.prefect_settings
        version_group_id = (
            prefect_settings.evidence_customer_version_group_id
            if flow_type == "customer"
            else prefect_settings.evidence_collector_version_group_id
        )
        flow_labels = (
            prefect_settings.evidence_customer_flow_labels
            if flow_type == "customer"
            else prefect_settings.evidence_collector_flow_labels
        )
        run_config_ = (
            prefect_settings.evidence_customer_run_config
            if flow_type == "customer"
            else prefect_settings.evidence_collector_run_config
        )
        run_config = run_config_.to_object() if run_config_ else None

        prefect_parameters = {
            "dc_engagement_id": dc_engagement_id,
            "env": str(self.settings.env),
            "requested_by": requested_by,
        }

        db_background, db_notification = tracker.create_job(
            dc_engagement_id=dc_engagement_id,
            parameters=prefect_parameters,
            db_session=self.session,
            external_job_id=version_group_id,
        )

        request_id: int = db_background.request_id
        notification_id: int = db_notification.notification_id
        prefect_parameters.update(
            {
                "request_id": request_id,
                "notification_id": notification_id,
            }
        )

        log_prefix = f"[{flow_type.capitalize()} File {request_id=}, {requested_by=}] "
        bucket = prefect_settings.json_requests_bucket
        key = "/".join(
            (
                str(self.settings.env),
                f"{flow_type}_file",
                f"{request_id}.json",
            )
        )
        request_json_loc = f"s3://{bucket}/{key}"
        prefect_parameters.update(
            {
                "request_json_loc": request_json_loc,
            }
        )

        logger.info(
            "%s - Uploading to S3: request_json_loc=%s", log_prefix, request_json_loc
        )

        # Merge payload and data into a single JSON object

        json_payload = {
            **payload.dict(exclude={"schema_type"}),
            "rows": [row.dict() for row in data],
        }

        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(
                    jsonable_encoder(json_payload), separators=(",", ":")
                ).encode("utf-8"),
            )
        except Exception as e:
            logger.exception("%s - Error uploading to S3", log_prefix)
            tracker.handle_job_error(
                self.session,
                db_notification,
                message=TextMessageCreate(type="text", data="Error uploading to S3"),
            )
            raise ServiceException("Error uploading to S3", 500) from e

        logger.info("%s - Uploaded JSON to S3, submitting Prefect job", log_prefix)

        try:
            external_run_id = self.prefect_client.create_flow_run(
                version_group_id=version_group_id,
                parameters=prefect_parameters,
                labels=flow_labels,
                run_config=run_config,
            )
        except Exception as e:
            logger.exception("%s - Error submitting Prefect job", log_prefix)
            tracker.handle_job_error(
                self.session,
                db_notification,
                message=TextMessageCreate(
                    type="text", data="Error submitting Prefect job"
                ),
            )
            raise ServiceException("Error submitting Prefect job", 500) from e

        data_msgs = [
            TextMessageCreate(
                data=f"{flow_type.capitalize()} File Job Submitted: run_id"
                f"='{external_run_id}'",
                type="text",
            )
        ]

        stmt = tracker.make_message_append_statement(
            notification_id,
            data_msgs,
        )
        self.session.exec(stmt)
        self.session.commit()
        db_background.external_run_id = external_run_id
        db_background.parameters = json.dumps(prefect_parameters, separators=(",", ":"))
        self.session.add(db_background)
        self.session.commit()

        return FlowRunResult(
            version_group_id,
            external_run_id,
            prefect_parameters,
            request_id,
            notification_id,
        )

    def create_evidence_collector_flow(
        self,
        dc_engagement_id: int,
        payload: "V2CollectorFileUpload",
        data: "TCollectorRowModel",
        requested_by: str,
        tracker: "ExternalServiceTracker",
    ):
        return self._create_evidence_flow(
            dc_engagement_id=dc_engagement_id,
            payload=payload,
            data=data,
            requested_by=requested_by,
            tracker=tracker,
            flow_type="collector",
        )

    def create_service_level_flow(
        self,
        dc_engagement_id: int,
        requested_by: str,
        run_type: Literal["serial_number", "instance_id"],
        payload: list[ServiceLevelFlowRow],
        tracker: "ExternalServiceTracker",
    ) -> FlowRunResult:
        prefect_settings = self.settings.prefect_settings
        version_group_id = prefect_settings.service_level_version_group_id
        flow_labels = prefect_settings.service_level_flow_labels
        run_config = (
            prefect_settings.service_level_run_config.to_object()
            if prefect_settings.service_level_run_config
            else None
        )

        payload_contents = {"dc_engagement_id": dc_engagement_id, "rows": payload}

        db_background, db_notification = tracker.create_job(
            dc_engagement_id=dc_engagement_id,
            parameters={},
            db_session=self.session,
            external_job_id=version_group_id,
            workflow_data=payload_contents,
        )

        request_id = db_background.request_id
        notification_id = db_notification.notification_id

        log_prefix = f"[Service Level {request_id=}, {requested_by=}] "

        bucket = prefect_settings.json_requests_bucket

        key = "/".join(
            (
                str(self.settings.env),
                "service_level",
                f"{request_id}.json",
            )
        )

        logger.info("%s - Uploading to S3: bucket=%s, key=%s", log_prefix, bucket, key)

        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(payload_contents, separators=(",", ":")).encode(
                    "utf-8"
                ),
            )
        except Exception as e:
            logger.exception("%s - Error uploading to S3", log_prefix)
            tracker.handle_job_error(
                self.session,
                db_notification,
                message=TextMessageCreate(type="text", data="Error uploading to S3"),
            )
            raise ServiceException("Error uploading to S3", 500) from e

        logger.info("%s - Uploaded JSON to S3, submitting Prefect job", log_prefix)

        job_params = {
            "dc_engagement_id": dc_engagement_id,
            "env": str(self.settings.env),
            "notification_id": notification_id,
            "request_id": request_id,
            "request_json_loc": f"s3://{bucket}/{key}",
            "requested_by": requested_by,
            "run_type": run_type,
        }
        try:
            external_run_id = self.prefect_client.create_flow_run(
                version_group_id=version_group_id,
                parameters=job_params,
                labels=flow_labels,
                run_config=run_config,
            )
        except Exception as e:
            logger.exception("%s - Error submitting Prefect job", log_prefix)
            tracker.handle_job_error(
                self.session,
                db_notification,
                message=TextMessageCreate(
                    type="text", data="Error submitting Prefect job"
                ),
            )
            raise ServiceException("Error submitting Prefect job", 500) from e

        data_msgs = [
            TextMessageCreate(
                data=f"Service Level Availability Job Submitted run_id='"
                f"{external_run_id}'",
                type="text",
            )
        ]

        stmt = tracker.make_message_append_statement(
            notification_id,
            data_msgs,
        )
        self.session.exec(stmt)
        self.session.commit()
        db_background.external_run_id = external_run_id
        db_background.parameters = json.dumps(job_params, separators=(",", ":"))
        self.session.add(db_background)
        self.session.commit()

        return FlowRunResult(
            version_group_id, external_run_id, job_params, request_id, notification_id
        )

    def create_host_name_site_moves_flow(
        self,
        dc_engagement_id: int,
        tracker: "ExternalServiceTracker",
        db_user: "V2User",
    ):
        flow_settings = self.settings.prefect_settings.host_name_site_moves_settings
        job_params = {
            "dc_engagement_id": dc_engagement_id,
            "requested_by": db_user.cisco_cco_id,
        }
        prefect_params = {
            "env": str(self.settings.env),
            "request_json": {
                "engagement_id": dc_engagement_id,
            },
            "requested_by": db_user.cisco_cco_id,
            "dc_engagement_id": dc_engagement_id,
        }

        db_background, db_notification = tracker.create_job(
            dc_engagement_id=dc_engagement_id,
            parameters=prefect_params,
            db_session=self.session,
            external_job_id=flow_settings["version_group_id"],
            workflow_data={},
            messages=[
                TextMessageCreate(
                    type="text",
                    data="Host Name Site Moves Requested",
                )
            ],
        )

        request_id = db_background.request_id
        notification_id = db_notification.notification_id
        prefect_params.update(
            {
                "request_id": request_id,
                "notification_id": notification_id,
            }
        )

        try:
            run_id = self.prefect_client.create_flow_run(
                parameters=prefect_params,
                **flow_settings,
            )
            logger.info(
                "Submitted Host Name Site Moves Job request_id=%s db_user.cisco_cco_id=%s run_id=%s",
                request_id,
                db_user.cisco_cco_id,
                run_id,
            )
        except Exception as e:
            logger.exception(
                "Error submitting Host Name Site Moves Job request_id=%s db_user.cisco_cco_id=%s",
                request_id,
                db_user.cisco_cco_id,
            )
            tracker.handle_job_error(
                db_session=self.session,
                db_notification=db_notification,
                message=TextMessageCreate(
                    type="text", data="Error submitting Prefect job"
                ),
                exception=e,
            )
            raise ServiceException("Error submitting Prefect job", 500) from e

        db_background.external_run_id = run_id
        self.session.add(db_background)
        self.session.commit()

        return FlowRunResult(
            flow_settings["version_group_id"],
            run_id,
            job_params,
            request_id,
            notification_id,
        )
