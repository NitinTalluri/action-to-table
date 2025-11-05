import contextlib
import datetime
import gzip
import json
import logging
import uuid
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    Optional,
    Union,
)
from zoneinfo import ZoneInfo

import httpx
from fastapi.encoders import jsonable_encoder
from pydantic.v1 import Field
from sqlalchemy import text
from toolz import excepts
from typing_extensions import Concatenate, ParamSpec, TypeVar, cast

from api.v2.models import (
    DeploymentItem,
    ExtCreateCanvasPayload,
    ExtRefreshCanvasViewPayload,
    Model,
    ParametersMessageCreate,
    TagsetTagModel,
    TEnv,
    TextMessageCreate,
    V2ConfigTagStrategy,
    V2CustomerFileUpload,
    V2GenericJobResponse,
    V2TagHistoryReportUpload,
    V2WriteTags,
    V3CanvasRebuild,
)
from api.v2.models.external import (
    CanvasEventType,
    DeleteCanvasEventPayload,
    DiscoverLiveboardsEventPayload,
    EngagementEventType,
    EventStage,
    ExtAcatDiscoveryPayload,
    ExtBulkTaggingPayload,
    ExtCreateTagHistoryPayload,
    ExtEvidenceCollectorPayload,
    ExtEvidenceCustomerPayload,
    ExtHostNameRelinkPayload,
    ExtRebuildCanvasPayload,
    ExtTaggingPayload,
    ExtThoughtSpotTaggingPayload,
    ManageLiveboardsEventPayload,
    RefreshEngagementEventPayload,
    ShareEngagementEventPayload,
    TEventPayload,
    TEventType,
    ThoughtSpotLiveboardEventType,
)
from api.v2.models.workflows.macd import MacdAuditSchemaType
from api.v2.orm import V2Canvas
from api.v2.services import canvas_readable

from ...models.external.flows import (
    get_macd_ext_audit_cls,
)
from ...models.stored_proc import V2S3StagedFile
from .. import (
    S3Mixin,
    ServiceException,
    SessionMixin,
)

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from sqlmodel import Session

    from api.settings import AppSettings, Environment
    from api.v2.models import (
        V2BulkInstanceTaggingPayload,
        V3CanvasCreate,
    )
    from api.v2.models.workflows.collector_file import V2CollectorFileUpload
    from api.v2.models.workflows.macd import MacdAuditPayload
    from api.v2.orm import V2Notification, V2User

    from ...models.workflows.lookups import UploadType
    from .. import (
        ExternalServiceTracker,
    )

logger = logging.getLogger("api")

P = ParamSpec("P")

R = TypeVar("R")
SVC = TypeVar("SVC", bound="PrefectV3FlowService")

# Should be a key in the PrefectV3Settings model
TPrefectV3SettingKey = Literal["canvas_deployment_id"]


def deployment_tags(
    tags: set[str],
) -> Callable[[Callable[[Concatenate[SVC, P]], R]], Callable[P, R]]:
    """
    Decorator to inject the deployment ID that is retrieved from the Prefect API
    using tags to filter the deployments by tags.

    This avoids the need to pass the deployment ID to the method.

    Example:
        @deployment_tags({"create_canvas"}) # Matches deployments with the tag "create_canvas" + "settings.env"
    """
    P1 = ParamSpec("P1")

    def decorator(
        method: Callable[[Concatenate[SVC, P1]], R],
    ) -> Callable[P1, R]:
        @wraps(method)
        def wrapper(self: "PrefectV3FlowService", **kwargs: P.kwargs) -> R:
            full_tags = {str(self.settings.env), *tags}
            # We collect all the matched deployments and choose the best match
            matched_deployments = (
                (deployment, len(deployment.tags.intersection(full_tags)))
                for deployment in self.deployments
                if tags.issubset(deployment.tags)
            )
            try:
                best_match = max(matched_deployments, key=lambda x: x[1])
            except ValueError as e:
                msg = f"Deployment not found with tags: {tags}"
                logger.error(msg)
                raise ServiceException(msg, 500) from e

            deployment_id = best_match[0].id
            kwargs["deployment_id"] = deployment_id
            return method(self, **kwargs)

        return wrapper

    return decorator


def name_flow(base: str, requestor: "V2User", *args, **kwargs) -> str:
    """
    Generate a name for a flow run

    Args are joined with hyphens and lowercased. The result is truncated to 255 characters.
    Kwargs are used with key=value format.
    """
    cco = requestor.cisco_cco_id.split("@")[0]
    tokens = [
        base.lower(),
        cco.lower(),
        *args,
        *[f"{k}={v}" for k, v in kwargs.items()],
    ]
    return "-".join(str(t) for t in tokens)[:255]


class CreateFlowRunResponse(Model):
    deployment_id: str = Field(
        ..., description="UUID of the deployment that the flow is associated with."
    )
    flow_id: str = Field(..., description="UUID of the flow being run.")
    id: str = Field(..., description="UUID of the flow run.")
    name: str = Field(
        ...,
        description="Name of the flow run. Either automatically generated or user provided.",
    )
    parameters: Optional[dict]
    work_pool_id: Optional[str]
    work_pool_name: Optional[str]
    labels: Optional[dict[str, str]] = Field(
        {},
        description="Labels associated with the flow run. The flow's name may be accessed via labels['prefect.flow.name']",
    )


class PrefectV3APIMixin:
    """Mixin class that implements the main Prefect API endpoints"""

    def __init__(
        self,
        client: httpx.Client,
        account_id: str,
        workspace_id: str,
        env: Union["TEnv", "Environment"],
    ):
        self.account_id = account_id
        self.workspace_id = workspace_id
        self.client = client
        self.env = cast("TEnv", str(env))

    @property
    def api_url(self) -> str:
        return f"/api/accounts/{self.account_id}/workspaces/{self.workspace_id}"

    def _emit_api_event(
        self, event: str, resource: dict[str, str], payload: dict[str, Any] | None
    ) -> None:
        endpoint = f"{self.api_url}/events"
        UTC = ZoneInfo("UTC")
        event_payload = [
            {
                "occurred": datetime.datetime.now(UTC).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "event": event,
                "resource": resource,
                "id": str(uuid.uuid4()),
                "payload": payload,
            }
        ]

        response = self.client.post(endpoint, json=event_payload)
        response.raise_for_status()
        return

    def _create_flow_run_from_deployment(
        self,
        deployment_id: str,
        parameters: dict,
        name: str | None = None,
        tags: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> CreateFlowRunResponse:
        """

        Parameters
        ----------
        deployment_id : str (UUID) - Deployment ID of the flow to run
        parameters : dict - Parameters to pass to the flow
        name : str, optional - Name of the flow run. If None, Prefect will generate a name.
        tags : list[str], optional - Tags to associate with the flow run
        idempotency_key: str, optional - Idempotency key to ensure that the flow run is only created once

        Returns
        -------
        CreateFlowRunResponse: Response from Prefect API

        """

        endpoint = f"{self.api_url}/deployments/{deployment_id}/create_flow_run"
        prefect_payload = {
            "name": name,
            "parameters": {
                "payload": parameters,
                "env": str(self.env),
            },
            "enforce_parameter_schema": True,
            "tags": tags or [],
            "idempotency_key": idempotency_key,
            "state": {
                "message": f"Run from DC API via {self.__class__.__name__}",
                "state_details": {},
                "type": "SCHEDULED",
            },
        }
        if name is None:
            prefect_payload.pop("name")
        response = self.client.post(endpoint, json=prefect_payload)
        response.raise_for_status()
        return CreateFlowRunResponse.parse_obj(response.json())


class PrefectV3FlowService(SessionMixin, S3Mixin, PrefectV3APIMixin):
    deployments: list["DeploymentItem"]

    def __init__(
        self,
        client: httpx.Client,
        s3_client: "S3Client",
        settings: "AppSettings",
        session: "Session",
        deployments: list["DeploymentItem"],
    ):
        SessionMixin.__init__(self, session)
        S3Mixin.__init__(self, s3_client)
        PrefectV3APIMixin.__init__(
            self,
            client,
            account_id=settings.prefect_v3_settings.account_id,
            workspace_id=settings.prefect_v3_settings.workspace_id,
            env=settings.env,
        )
        self.settings = settings
        self.deployments = deployments

    def _get_s3_staged_file_uri(
        self, workflow_name: str, cisco_cco_id: str, request_id: int
    ) -> "V2S3StagedFile":
        return V2S3StagedFile.parse_obj(
            self.settings.json_stage_file_store.make_staged_s3_uri(
                workflow=workflow_name,
                file_name=f"{cisco_cco_id.split('@')[0]}_{request_id}.json.gz",
            )
        )

    def _emit_event(self, event: TEventType, payload: TEventPayload) -> None:
        event_name = f"{event!s}.{EventStage.requested!s}"

        match payload:
            case ShareEngagementEventPayload() | RefreshEngagementEventPayload():
                resource = {
                    "prefect.resource.id": f"datacanvas.{payload.env}.engagement.{payload.dc_engagement_id}",
                    "prefect.resource.name": f"Data Canvas {payload.env.title()}",
                }
            case (
                DeleteCanvasEventPayload()
                | ManageLiveboardsEventPayload()
                | DiscoverLiveboardsEventPayload()
            ):
                resource = {
                    "prefect.resource.id": f"datacanvas.{payload.env}.canvas.{payload.canvas_id}",
                    "prefect.resource.name": f"Data Canvas {payload.env.title()}",
                }
            case _:
                msg = f"Unhandled event payload {payload=}"
                raise ServiceException(msg, 500)

        logger.debug(
            "Emitting event %s with payload %s and resource %s",
            event_name,
            payload,
            resource,
        )
        try:
            return self._emit_api_event(event_name, resource, payload.dict())
        except httpx.HTTPStatusError as e:
            msg = f"Error emitting event {event_name}"
            logger.exception(msg)
            raise ServiceException(msg, 500) from e
        except Exception as e:
            msg = f"Unhandled exception emitting event {event_name}"
            logger.exception(msg)
            raise ServiceException(msg, 500) from e

    def emit_engagement_shared(
        self,
        dc_engagement_id: int,
        dc_user_id: int,
        notification_id: int,
        request_id: int,
        shared_with_dc_user_id: int,
    ):
        """
        Emits an event that an engagement was shared. The event should be handled by a flow
        where all engagement canvases are shared via ThoughtSpot
        """

        payload = ShareEngagementEventPayload(
            env=self.env,
            dc_user_id=dc_user_id,
            dc_engagement_id=dc_engagement_id,
            notification_id=notification_id,
            request_id=request_id,
            shared_with_dc_user_id=shared_with_dc_user_id,
        )

        return self._emit_event(EngagementEventType.engagement_share, payload)

    def emit_tagset_created(
        self,
        dc_engagement_id: int,
        dc_user_id: int,
        notification_id: int,
        request_id: int,
    ):
        payload = RefreshEngagementEventPayload(
            env=self.env,
            dc_user_id=dc_user_id,
            dc_engagement_id=dc_engagement_id,
            notification_id=notification_id,
            request_id=request_id,
        )

        return self._emit_event(EngagementEventType.engagement_view_refresh, payload)

    def emit_canvas_deleted(
        self,
        canvas_id: int,
        dc_user_id: int,
        dc_engagement_id: int,
        notification_id: int,
        request_id: int | None,
    ) -> None:
        """
        Emits an event that a canvas was deleted. The event should be handled by a flow
        in the Prefect Cloud Automations.
        """
        payload = DeleteCanvasEventPayload(
            env=self.env,
            canvas_id=canvas_id,
            dc_user_id=dc_user_id,
            dc_engagement_id=dc_engagement_id,
            notification_id=notification_id,
            request_id=request_id,
        )
        return self._emit_event(CanvasEventType.canvas_delete, payload)

    def emit_liveboard_management_requested(
        self,
        canvas_id: int,
        dc_user_id: int,
        dc_engagement_id: int,
        notification_id: int,
        request_id: int,
    ):
        """
        Emits an event that a liveboard management request was made. The request is stored in the database. The flow
        will retrieve the details and process the request.
        """
        payload = ManageLiveboardsEventPayload(
            env=self.env,
            canvas_id=canvas_id,
            dc_user_id=dc_user_id,
            dc_engagement_id=dc_engagement_id,
            notification_id=notification_id,
            request_id=request_id,
        )
        return self._emit_event(
            ThoughtSpotLiveboardEventType.manage_liveboards, payload
        )

    def emit_liveboard_discovery_requested(
        self,
        canvas_id: int,
        dc_user_id: int,
        dc_engagement_id: int,
        notification_id: int,
        request_id: int,
    ):
        """
        Emits an event that a liveboard discovery request was made. The flow will run dc-canvas-service SyncService
        """
        payload = DiscoverLiveboardsEventPayload(
            env=self.env,
            canvas_id=canvas_id,
            dc_user_id=dc_user_id,
            dc_engagement_id=dc_engagement_id,
            notification_id=notification_id,
            request_id=request_id,
        )
        return self._emit_event(
            ThoughtSpotLiveboardEventType.discover_liveboards, payload
        )

    def create_flow_run_from_deployment(
        self,
        deployment_id: str,
        parameters: dict,
        tracker: "ExternalServiceTracker",
        db_notification: "V2Notification",
        name: str | None = None,
        tags: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> CreateFlowRunResponse:
        try:
            response = self._create_flow_run_from_deployment(
                deployment_id=deployment_id,
                parameters=jsonable_encoder(parameters),
                name=name,
                tags=tags,
                idempotency_key=idempotency_key,
            )
        except httpx.HTTPStatusError as e:
            msg = f"Error creating flow run from deployment {deployment_id}"
            with contextlib.suppress(Exception):
                msg = f"{msg} : {e.response.content.decode()}"
            logger.exception(msg)
            tracker.handle_job_error(
                self.session,
                db_notification,
                message=TextMessageCreate(type="text", data=msg),
            )
            raise ServiceException(msg, 500) from e
        except Exception as e:
            msg = (
                f"Unhandled exception creating flow run from deployment {deployment_id}"
            )
            logger.exception(msg)
            tracker.handle_job_error(
                self.session,
                db_notification,
                message=TextMessageCreate(type="text", data=msg),
            )
            raise ServiceException(msg, 500) from e
        return response

    @deployment_tags({"rebuild_canvas"})
    def rebuild_canvas_flow(
        self,
        deployment_id: str,
        canvas_id: int,
        payload: "V3CanvasRebuild",
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2Canvas":
        db_background, db_notification = tracker.create_job(
            dc_engagement_id=payload.dc_engagement_id,
            parameters=payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data={**payload.dict(), "canvas_id": canvas_id, "rebuild": True},
            user_id=requestor.user_id,
            canvas_id=canvas_id,
            messages=[
                ParametersMessageCreate(
                    form_data={
                        **payload.dict(),
                        "canvas_id": canvas_id,
                        "_engagement_links": payload._engagement_links,
                    },
                    data={
                        **canvas_readable(model=payload, session=self.session),
                        "Canvas Id": canvas_id,
                    },
                    type="parameters",
                ),
            ],
        )

        request_id = db_background.request_id
        notification_id = db_notification.notification_id

        ext_payload = ExtRebuildCanvasPayload(
            request_id=request_id,
            dc_user_id=requestor.user_id,
            notification_id=notification_id,
            canvas_id=canvas_id,
            dc_engagement_id=payload.dc_engagement_id,
            extensions=payload.files,
            tag_ids=payload.tag_ids,
            current_snapshot_name=payload.current_snapshot_name,
            historical_snapshot_name=payload.historical_snapshot_name,
            customer_request_ids=payload.customer_request_ids,
            collector_request_ids=payload.collector_request_ids,
        )

        # Associate the notification with the canvas
        stmt = text(
            """
            UPDATE DC_CANVAS_HDR
            SET
                NOTIFICATION_ID = :notification_id
                WHERE
                    CANVAS_ID = :canvas_id
            """
        ).bindparams(notification_id=notification_id, canvas_id=canvas_id)

        self.session.execute(stmt)
        self.session.commit()

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "rebuild-canvas",
                requestor,
                canvas=canvas_id,
                request=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to rebuild canvas #{canvas_id} has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return self.session.get(V2Canvas, (canvas_id, payload.dc_engagement_id))

    @deployment_tags({"create_canvas"})
    def create_canvas_flow(
        self,
        deployment_id: str,
        canvas_id: int,
        payload: "V3CanvasCreate",
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2Canvas":
        db_background, db_notification = tracker.create_job(
            dc_engagement_id=payload.dc_engagement_id,
            parameters=payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data={**payload.dict(), "canvas_id": canvas_id},
            user_id=requestor.user_id,
            canvas_id=canvas_id,
            messages=[
                ParametersMessageCreate(
                    form_data={
                        **payload.dict(),
                        "canvas_id": canvas_id,
                        "_engagement_links": payload._engagement_links,
                        "_engagement_evidence_uploads": payload._engagement_evidence_uploads,
                    },
                    data={
                        **canvas_readable(model=payload, session=self.session),
                        "Canvas Id": canvas_id,
                    },
                    type="parameters",
                ),
            ],
        )

        request_id = db_background.request_id
        notification_id = db_notification.notification_id

        ext_payload = ExtCreateCanvasPayload(
            request_id=request_id,
            dc_user_id=requestor.user_id,
            notification_id=notification_id,
            canvas_id=canvas_id,
            dc_engagement_id=payload.dc_engagement_id,
            extensions=payload.files,
            tag_ids=payload.tag_ids,
            current_snapshot_name=payload.current_snapshot_name,
            historical_snapshot_name=payload.historical_snapshot_name,
            customer_request_ids=payload.customer_request_ids,
            collector_request_ids=payload.collector_request_ids,
        )

        # Associate the notification with the canvas
        stmt = text(
            """
            UPDATE DC_CANVAS_HDR
            SET
                NOTIFICATION_ID = :notification_id
                WHERE
                    CANVAS_ID = :canvas_id
            """
        ).bindparams(notification_id=notification_id, canvas_id=canvas_id)

        self.session.execute(stmt)
        self.session.commit()

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "create-canvas",
                requestor,
                canvas=canvas_id,
                request=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to create a canvas has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return self.session.get(V2Canvas, (canvas_id, payload.dc_engagement_id))

    @deployment_tags({"refresh_canvas_view"})
    def refresh_canvas_view_flow(
        self,
        deployment_id: str,
        canvas_id: int,
        requestor: "V2User",
        dc_engagement_id: int,
        tracker: "ExternalServiceTracker",
    ) -> "V2GenericJobResponse":
        request_id = tracker.get_next_request_id(self.session)
        notification_id = tracker.get_next_notification_id(self.session)

        ext_payload = ExtRefreshCanvasViewPayload(
            canvas_id=canvas_id,
            dc_user_id=requestor.user_id,
            request_id=request_id,
            dc_engagement_id=dc_engagement_id,
            notification_id=notification_id,
        )

        db_background, db_notification = tracker.create_job(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=dc_engagement_id,
            parameters=ext_payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data={},
            user_id=requestor.user_id,
            canvas_id=canvas_id,
            messages=[
                ParametersMessageCreate(
                    form_data={"canvas_id": canvas_id},
                    data={"Canvas Id": canvas_id},
                    type="parameters",
                ),
            ],
        )

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "refresh-canvas",
                requestor,
                canvas=canvas_id,
                request=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to refresh a canvas view has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="Canvas view refresh job submitted",
        )

    @deployment_tags({"create_dc_acat_report"})
    def create_acat_discovery_flow(
        self,
        deployment_id: str,
        dc_engagement_id: int,
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2GenericJobResponse":
        """
        Creates a flow run for ACAT discovery.
        """
        db_background, db_notification = tracker.create_job(
            dc_engagement_id=dc_engagement_id,
            parameters={},
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data={},
            user_id=requestor.user_id,
        )

        request_id = db_background.request_id
        notification_id = db_notification.notification_id

        ext_payload = ExtAcatDiscoveryPayload(
            notification_id=notification_id,
            request_id=request_id,
            requested_by=requestor.cisco_cco_id,
            dc_user_id=requestor.user_id,
            dc_engagement_id=dc_engagement_id,
        )

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "acat-discovery",
                requestor,
                E=dc_engagement_id,
                R=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to create an ACAT discovery report has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(
            notification_id=notification_id, messages=data_msgs
        )
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="ACAT discovery job submitted",
        )

    @deployment_tags({"create_macd_audit"})
    def create_macd_audit_flow(
        self,
        deployment_id: str,
        dc_engagement_id: int,
        payload: "MacdAuditPayload",
        data: bytes,
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2GenericJobResponse":
        request_id = tracker.get_next_request_id(self.session)
        notification_id = tracker.get_next_notification_id(self.session)
        if payload.schema_type == MacdAuditSchemaType.skip:
            upload_uri = None
        else:
            upload_uri = self.settings.json_stage_file_store.make_staged_s3_uri(
                workflow="macd_audit",
                file_name=f"{request_id}_{dc_engagement_id}.json.gz",
            )
            logger.info("Uploading MACD Audit Request to S3: %s", upload_uri["s3_uri"])
            self.upload_to_s3(
                bucket=upload_uri["bucket"],
                key=upload_uri["key"],
                body=data,
            )

        db_background, db_notification = tracker.create_job(
            dc_engagement_id=dc_engagement_id,
            parameters=payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data=payload.dict(),
            user_id=requestor.user_id,
            canvas_id=None,
            messages=[
                TextMessageCreate(
                    type="text",
                    data="Processing MACD Audit request",
                )
            ],
            request_id=request_id,
            notification_id=notification_id,
        )

        payload_cls = get_macd_ext_audit_cls(schema_type=payload.schema_type)

        flow_payload = payload_cls(
            dc_engagement_id=dc_engagement_id,
            dc_user_id=requestor.user_id,
            notification_id=db_notification.notification_id,
            request_id=db_background.request_id,
            requested_by=requestor.cisco_cco_id,
            schema_type=payload.schema_type,
            period_start_date=payload.period_start_date,
            period_end_date=payload.period_end_date,
            file_uri=upload_uri["s3_uri"] if upload_uri else None,
        )

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=flow_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "macd-audit",
                requestor,
                E=dc_engagement_id,
                R=request_id,
            ),
        )
        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to create a MACD Audit has been submitted. Job Name: '{reply.name}',  Job ID: '{reply.id}'",
            )
        ]
        stmt = tracker.make_message_append_statement(
            notification_id=db_notification.notification_id, messages=data_msgs
        )
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=db_background.request_id,
            notification_id=db_notification.notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="MACD Audit job submitted",
        )

    @deployment_tags({"create_tag_history"})
    def create_tag_history_flow(
        self,
        deployment_id: str,
        payload: "V2TagHistoryReportUpload",
        data: bytes,
        tracker: "ExternalServiceTracker",
        requestor: "V2User",
    ) -> "V2GenericJobResponse":
        """
        Creates a flow run for TagHistory Report.
        """

        request_id, notification_id = (
            tracker.get_next_request_id(self.session),
            tracker.get_next_notification_id(self.session),
        )

        def format_stage_data(compressed_data: bytes, id_type: "UploadType") -> bytes:
            """
            We receive an array of gzip compressed items. These are either instance_ids or serial_numbers.
            We need to:
            1. Decompress
            2. Use payload.id_type to determine how to transform to object
            3. Apply to all items, so that we have an array of objects/dicts
            4. Recompress
            """

            def pack_item_as_instance_id(item: int):
                return {"instance_id": int(item)}

            def pack_item_as_serial_number(item: str):
                return {"serial_number": item}

            pack_func = (
                pack_item_as_instance_id
                if id_type.value == "instance_id"
                else pack_item_as_serial_number
            )

            pack_or_ignore = excepts(Exception, pack_func, lambda _: None)

            data = json.loads(gzip.decompress(compressed_data).decode("utf-8"))
            if not isinstance(data, list):
                raise ServiceException(
                    "Data must be a list of items",
                    400,
                )
            packed_with_nones = (pack_or_ignore(item) for item in data)
            packed_data = [d for d in packed_with_nones if d is not None]
            return gzip.compress(json.dumps(packed_data).encode("utf-8"))

        upload_uri = self._get_s3_staged_file_uri(
            workflow_name="tag_history",
            cisco_cco_id=requestor.cisco_cco_id,
            request_id=request_id,
        )
        repacked_data = format_stage_data(data, payload.id_type)

        ext_payload = ExtCreateTagHistoryPayload(
            dc_engagement_id=payload.dc_engagement_id,
            notification_id=notification_id,
            request_id=request_id,
            requested_by=requestor.cisco_cco_id,
            id_type=payload.id_type,
            snowflake_uri=upload_uri,
            from_date=payload.from_date,
            tagset_ids=payload.tagset_ids,
        )

        db_background, db_notification = tracker.create_job(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=payload.dc_engagement_id,
            parameters=ext_payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data=payload.dict(),
            user_id=requestor.user_id,
            subject=f"Tag History Report Request for Engagement #{payload.dc_engagement_id}",
            messages=[
                TextMessageCreate(
                    type="text",
                    data="Processing Tag History Report request",
                )
            ],
        )
        logger.info(
            "Uploading Tag History Report Request to S3: %s",
            upload_uri.s3_uri,
        )

        bucket, key = upload_uri.bucket, upload_uri.key
        self.upload_to_s3(
            bucket=bucket,
            key=key,
            body=repacked_data,
            ContentType="application/json",
            ContentEncoding="gzip",
        )

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "tag-history",
                requestor,
                E=payload.dc_engagement_id,
                R=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to create a tag history report has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="Create Tag History Report Request Submitted",
        )

    @deployment_tags({"create_dc_hostname_relink"})
    def create_host_name_relink_flow(
        self,
        deployment_id: str,
        dc_engagement_id: int,
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2GenericJobResponse":
        """
        Creates a flow run for HostName Relink.
        """

        db_background, db_notification = tracker.create_job(
            dc_engagement_id=dc_engagement_id,
            parameters={},
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data={},
            user_id=requestor.user_id,
        )

        request_id = db_background.request_id
        notification_id = db_notification.notification_id

        ext_payload = ExtHostNameRelinkPayload(
            notification_id=notification_id,
            request_id=request_id,
            requested_by=requestor.cisco_cco_id,
            dc_user_id=requestor.user_id,
            dc_engagement_id=dc_engagement_id,
        )

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "hostname-relink",
                requestor,
                E=dc_engagement_id,
                R=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to create a hostname relink has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(
            notification_id=notification_id, messages=data_msgs
        )
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="Create HostName Relink Report Request Submitted",
        )

    @deployment_tags({"bulk_tagging"})
    def create_bulk_tagging_flow(
        self,
        deployment_id: str,
        payload: "V2BulkInstanceTaggingPayload",
        data: bytes,
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2GenericJobResponse":
        """
        Creates a flow run for Bulk Tagging.
        """

        request_id, notification_id = (
            tracker.get_next_request_id(self.session),
            tracker.get_next_notification_id(self.session),
        )

        # Upload the data to S3
        upload_uri = self._get_s3_staged_file_uri(
            workflow_name="bulk_tagging",
            cisco_cco_id=requestor.cisco_cco_id,
            request_id=request_id,
        )

        ext_payload = ExtBulkTaggingPayload(
            request_id=request_id,
            dc_user_id=requestor.user_id,
            notification_id=notification_id,
            dc_engagement_id=payload.engagement_id,
            comment=payload.comment,
            cisco_cco_id=requestor.cisco_cco_id,
            snowflake_uri=upload_uri,
            action="set",
            config_strategy=payload.config_strategy,
            id_type=payload.id_type,
        )

        db_background, db_notification = tracker.create_job(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=payload.engagement_id,
            parameters=ext_payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data=payload.dict(),
            user_id=requestor.user_id,
            subject=f"Bulk Tagging Request for Engagement #{payload.engagement_id}",
            messages=[
                TextMessageCreate(
                    type="text",
                    data="Processing Bulk Tagging",
                )
            ],
        )

        logger.info("Uploading Bulk Tagging Request to S3: %s", upload_uri.s3_uri)
        bucket, key = upload_uri.bucket, upload_uri.key
        self.upload_to_s3(
            bucket=bucket,
            key=key,
            body=data,
            ContentType="application/json",
            ContentEncoding="gzip",
        )

        logger.info("Uploaded Bulk Tagging Request to S3: %s", upload_uri.s3_uri)

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "bulk-tagging",
                requestor,
                E=payload.engagement_id,
                R=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to bulk tag has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="Bulk Tagging Request Submitted",
        )

    @deployment_tags({"instance_tagging"})
    def create_instance_tagging_flow(
        self,
        deployment_id: str,
        payload: "V2WriteTags",
        data: bytes,
        tagset_tag_ids: list[TagsetTagModel],
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2GenericJobResponse":
        """
        Creates a flow run for Instance Tagging.
        """

        request_id, notification_id = (
            tracker.get_next_request_id(self.session),
            tracker.get_next_notification_id(self.session),
        )

        # Upload the data to S3
        upload_uri = self._get_s3_staged_file_uri(
            workflow_name="instance_tagging",
            cisco_cco_id=requestor.cisco_cco_id,
            request_id=request_id,
        )

        ext_payload = ExtTaggingPayload(
            request_id=request_id,
            dc_user_id=requestor.user_id,
            notification_id=notification_id,
            tagset_tag_ids=tagset_tag_ids,
            dc_engagement_id=payload.engagement_id,
            comment=payload.comment,
            cisco_cco_id=requestor.cisco_cco_id,
            snowflake_uri=upload_uri,
            action="set",
            config_strategy=payload.config_strategy,
        )

        db_background, db_notification = tracker.create_job(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=payload.engagement_id,
            parameters=ext_payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data=payload.dict(),
            user_id=requestor.user_id,
            subject=f"Instance Tagging Request for Engagement #{payload.engagement_id}, with {len(payload.tag_ids)}",
            messages=[
                TextMessageCreate(
                    type="text",
                    data="Processing Instance Tagging",
                )
            ],
        )

        logger.info("Uploading Instance Tagging Request to S3: %s", upload_uri.s3_uri)
        bucket, key = upload_uri.bucket, upload_uri.key
        self.upload_to_s3(
            bucket=bucket,
            key=key,
            body=data,
            ContentType="application/json",
            ContentEncoding="gzip",
        )

        logger.info("Uploaded Instance Tagging Request to S3: %s", upload_uri.s3_uri)

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "instance-tagging",
                requestor,
                E=payload.engagement_id,
                R=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to tag instances has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="Instance Tagging Request Submitted",
        )

    @deployment_tags({"serial_tagging"})
    def create_serial_tagging_flow(
        self,
        deployment_id: str,
        payload: "V2WriteTags",
        data: bytes,
        tagset_tag_ids: list[TagsetTagModel],
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2GenericJobResponse":
        """
        Creates a flow run for Serial Tagging.
        """
        request_id, notification_id = (
            tracker.get_next_request_id(self.session),
            tracker.get_next_notification_id(self.session),
        )

        # Upload the data to S3
        upload_uri = self._get_s3_staged_file_uri(
            workflow_name="serial_tagging",
            cisco_cco_id=requestor.cisco_cco_id,
            request_id=request_id,
        )
        ext_payload = ExtTaggingPayload(
            request_id=request_id,
            dc_user_id=requestor.user_id,
            notification_id=notification_id,
            tagset_tag_ids=tagset_tag_ids,
            dc_engagement_id=payload.engagement_id,
            comment=payload.comment,
            cisco_cco_id=requestor.cisco_cco_id,
            snowflake_uri=upload_uri,
            action="set",
            config_strategy=payload.config_strategy,
        )

        db_background, db_notification = tracker.create_job(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=payload.engagement_id,
            parameters=ext_payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data=payload.dict(),
            user_id=requestor.user_id,
            subject=f"Serial Tagging Request for Engagement #{payload.engagement_id}",
            messages=[
                TextMessageCreate(
                    type="text",
                    data="Processing Serial Tagging",
                )
            ],
        )

        logger.info("Uploading Serial Tagging Request to S3: %s", upload_uri.s3_uri)
        bucket, key = upload_uri.bucket, upload_uri.key
        self.upload_to_s3(
            bucket=bucket,
            key=key,
            body=data,
            ContentType="application/json",
            ContentEncoding="gzip",
        )

        logger.info("Uploaded Serial Tagging Request to S3: %s", upload_uri.s3_uri)

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "serial-tagging",
                requestor,
                E=payload.engagement_id,
                R=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to tag serials has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="Serial Tagging Request Submitted",
        )

    @deployment_tags({"create_evidence_customer"})
    def create_evidence_customer_flow(
        self,
        deployment_id: str,
        payload: "V2CustomerFileUpload",
        data: bytes,
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2GenericJobResponse":
        """
        Create a flow run for evidence upload, customer
        """
        request_id, notification_id = (
            tracker.get_next_request_id(self.session),
            tracker.get_next_notification_id(self.session),
        )

        upload_uri = self._get_s3_staged_file_uri(
            workflow_name="evidence_customer",
            cisco_cco_id=requestor.cisco_cco_id,
            request_id=request_id,
        )

        schema_type: Literal["instance_id", "serial_number"] = (
            "instance_id"
            if "instance_id" in payload.schema_type.value
            else "serial_number"
        )

        ext_payload = ExtEvidenceCustomerPayload(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=payload.dc_engagement_id,
            cisco_cco_id=requestor.cisco_cco_id,
            snowflake_uri=upload_uri,
            file_name_id=payload.file_name_id,
            source=payload.source,
            effective_date=payload.effective_date,
            schema_type=schema_type,
            note=payload.note or "",
        )

        db_background, db_notification = tracker.create_job(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=payload.dc_engagement_id,
            parameters=ext_payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data=payload.dict(),
            user_id=requestor.user_id,
            subject="Customer File Upload",
            messages=[
                TextMessageCreate(
                    type="text",
                    data="Processing Customer File Upload",
                )
            ],
        )

        logger.info("Uploading Customer File Upload to S3: %s", upload_uri.s3_uri)
        bucket, key = upload_uri.bucket, upload_uri.key
        self.upload_to_s3(
            bucket=bucket,
            key=key,
            body=data,
            ContentType="application/json",
            ContentEncoding="gzip",
        )

        logger.info("Uploaded Customer File Upload to S3: %s", upload_uri.s3_uri)
        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "evidence-customer",
                requestor,
                E=payload.dc_engagement_id,
                R=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your Customer File upload has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]

        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="Customer File Upload Request Submitted",
        )

    @deployment_tags({"create_evidence_collector"})
    def create_evidence_collector_flow(
        self,
        deployment_id: str,
        payload: "V2CollectorFileUpload",
        data: bytes,
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
    ) -> "V2GenericJobResponse":
        """
        Create a flow run for evidence upload, collector
        """
        request_id, notification_id = (
            tracker.get_next_request_id(self.session),
            tracker.get_next_notification_id(self.session),
        )

        upload_uri = self._get_s3_staged_file_uri(
            workflow_name="evidence_collector",
            cisco_cco_id=requestor.cisco_cco_id,
            request_id=request_id,
        )

        ext_payload = ExtEvidenceCollectorPayload(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=payload.dc_engagement_id,
            cisco_cco_id=requestor.cisco_cco_id,
            snowflake_uri=upload_uri,
            file_name_id=payload.file_name_id,
            source=payload.source or "",
            effective_date=payload.effective_date,
            schema_type="serial_number",
            note=payload.note or "",
        )

        db_background, db_notification = tracker.create_job(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=payload.dc_engagement_id,
            parameters=ext_payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data=payload.dict(),
            user_id=requestor.user_id,
            subject="Collector File Upload",
            messages=[
                TextMessageCreate(
                    type="text",
                    data="Processing Collector File Upload",
                )
            ],
        )

        logger.info("Uploading Collector File Upload to S3: %s", upload_uri.s3_uri)
        bucket, key = upload_uri.bucket, upload_uri.key
        self.upload_to_s3(
            bucket=bucket,
            key=key,
            body=data,
            ContentType="application/json",
            ContentEncoding="gzip",
        )

        logger.info("Uploaded Collector File Upload to S3: %s", upload_uri.s3_uri)
        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "evidence-collector",
                requestor,
                E=payload.dc_engagement_id,
                R=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your Collector File upload has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]

        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="Collector File Upload Request Submitted",
        )

    @deployment_tags({"thoughtspot_tagging"})
    def create_thoughtspot_tagging_flow(
        self,
        deployment_id: str,
        thoughtspot_ids: list[int],
        config_strategy: Union[V2ConfigTagStrategy, None],
        requestor: "V2User",
        tracker: "ExternalServiceTracker",
        dc_engagement_id: int,
    ) -> "V2GenericJobResponse":
        """
        Creates a flow run for ThoughtSpot Tagging.
        """
        request_id, notification_id = (
            tracker.get_next_request_id(self.session),
            tracker.get_next_notification_id(self.session),
        )

        ext_payload = ExtThoughtSpotTaggingPayload(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=dc_engagement_id,
            cisco_cco_id=requestor.cisco_cco_id,
            dc_user_id=requestor.user_id,
            thoughtspot_ids=thoughtspot_ids,
            config_strategy=config_strategy,
        )

        db_background, db_notification = tracker.create_job(
            request_id=request_id,
            notification_id=notification_id,
            dc_engagement_id=dc_engagement_id,
            parameters=ext_payload.dict(),
            db_session=self.session,
            external_job_id=deployment_id,
            workflow_data={
                "thoughtspot_ids": thoughtspot_ids,
                "config_strategy": config_strategy if config_strategy else None,
            },
            user_id=requestor.user_id,
            subject=f"ThoughtSpot Tagging Request for {len(thoughtspot_ids)} items",
            messages=[
                TextMessageCreate(
                    type="text",
                    data="Processing ThoughtSpot Tagging",
                )
            ],
        )

        reply = self.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters=ext_payload.dict(),
            tracker=tracker,
            db_notification=db_notification,
            name=name_flow(
                "thoughtspot-tagging",
                requestor,
                E=dc_engagement_id,
                R=request_id,
            ),
        )

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=f"Your request to tag ThoughtSpot items has been submitted. Job ID: '{reply.id}', Job Name: '{reply.name}'",
            )
        ]
        stmt = tracker.make_message_append_statement(notification_id, data_msgs)
        self.session.exec(stmt)
        self.session.commit()

        return V2GenericJobResponse(
            request_id=request_id,
            notification_id=notification_id,
            external_job_id=reply.flow_id,
            external_run_id=reply.id,
            message="ThoughtSpot Tagging Request Submitted",
        )


__all__ = ["CreateFlowRunResponse", "PrefectV3FlowService"]
