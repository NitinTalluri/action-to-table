import logging
from typing import TYPE_CHECKING, TypedDict, Union

from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from api.v2.models.stored_proc import (
    V2MACDUploadParams,
    V2ProcedureNames,
    V2S3StagedFile,
    V2SEAUploadParams,
)
from api.v2.orm import MacdHdrTable
from api.v2.services import (
    ExternalServiceTracker,
    S3Mixin,
    ServiceException,
)

from . import EngineCompatMsgMixin, EngineCompatSPMixin, MsgPartials

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from sqlalchemy.engine import Engine

    from api.settings import AppSettings
    from api.v2.models import V2SEAUploadPayload
    from api.v2.models.workflows.macd import MacdSubmissionPayload

logger = logging.getLogger("api")


class DcUserDict(TypedDict):
    cisco_cco_id: str
    dc_user_id: int


UploadSpParams = Union[V2SEAUploadParams, V2MACDUploadParams]


class UploadSPService(
    S3Mixin, EngineCompatMsgMixin, EngineCompatSPMixin[UploadSpParams]
):
    """
    A Generic service that is suited for background tasks that:
    - Has a multi-part form with a file upload
    - The file contents need to be uploaded to S3
    - The file contents need to be processed by a Snowflake stored procedure that expects a 'normalized' file uri
    """

    def __init__(
        self,
        engine: "Engine",
        settings: "AppSettings",
        s3_client: "S3Client",
        tracker: "ExternalServiceTracker",
        dc_engagement_id: int,
        dc_user_id: int,
        cisco_cco_id: str,
        request_id: int,
        notification_id: int,
        workflow_name: str,
        sp_name: V2ProcedureNames,
    ):
        S3Mixin.__init__(self, s3_client=s3_client)
        EngineCompatMsgMixin.__init__(self, engine=engine)
        EngineCompatSPMixin.__init__(self, engine=engine)
        self.settings = settings
        self.tracker = tracker
        # noinspection PyTypeChecker
        self.session_maker = sessionmaker(bind=self.engine, class_=Session)
        self.dc_engagement_id = dc_engagement_id
        self.dc_user_id = dc_user_id
        self.request_id = request_id
        self.notification_id = notification_id
        self.workflow_name = workflow_name
        self.cisco_cco_id = cisco_cco_id
        self.sp_name = str(sp_name)

    def setup_messaging(
        self, params: UploadSpParams, message: str, subject: str
    ) -> MsgPartials:
        from api.v2.models import TextMessageCreate

        with self.session_maker() as session:
            self.tracker.create_job(
                dc_engagement_id=self.dc_engagement_id,
                parameters=params.dict(),
                db_session=session,
                external_job_id=str(self.sp_name),
                workflow_data=None,
                user_id=self.dc_user_id,
                messages=[TextMessageCreate(data=message, type="text")],
                subject=subject,
                request_id=self.request_id,
                notification_id=self.notification_id,
            )

        log_msg, exit_error, exit_success = self.make_msg_partial(
            notification_id=self.notification_id,
            ext_tracker=self.tracker,
            cisco_cco_id=params.cisco_cco_id,
        )

        return log_msg, exit_error, exit_success

    @property
    def s3_staged_file(self) -> V2S3StagedFile:
        """
        Creates a staged S3 URI for the given workflow name, cisco_cco_id, and request_id.
        """
        return V2S3StagedFile.parse_obj(
            self.settings.json_stage_file_store.make_staged_s3_uri(
                workflow=self.workflow_name,
                file_name=f"{self.cisco_cco_id.split('@')[0]}_{self.request_id}.json.gz",
            )
        )

    def upload_sea_data(self, params: UploadSpParams, file_content: bytes):
        """
        Uploads SEA data to S3, then calls Snowflake Stored Procedure to process the data.
        """

        s3_staged_file = self.s3_staged_file
        logger.info("Uploading SEA file to S3: %s", s3_staged_file.s3_uri)
        self.upload_to_s3(
            bucket=s3_staged_file.bucket,
            key=s3_staged_file.key,
            body=file_content,
        )
        logger.info("Uploaded SEA file to S3: %s", s3_staged_file.s3_uri)

        log_msg, exit_error, exit_success = self.setup_messaging(
            params=params,
            message="SEA File Upload Received, Processing",
            subject="SEA File Upload",
        )
        try:
            proc_result = self.run_stored_procedure(
                params=params,
                proc_name=V2ProcedureNames.load_sea_data,
                logged_user=params.cisco_cco_id,
            )
            logger.info(
                "SEA Upload stored procedure completed successfully %s", proc_result
            )
            exit_success(msg="SEA Upload completed successfully")

        except ServiceException as e:
            logger.exception("Failed to run SEA Upload stored procedure")
            exit_error(msg=f"Failed to run SEA Upload stored procedure: {e.msg}")
            return
        except Exception as e:
            logger.exception("Failed to run SEA Upload stored procedure")
            exit_error(msg=f"Failed to run SEA Upload stored procedure: {e}")
            return

    def upload_macd_data(self, params: V2MACDUploadParams, file_content: bytes):
        s3_staged_file = params.staged_file
        logger.info("Uploading MACD file to S3: %s", s3_staged_file.s3_uri)

        self.upload_to_s3(
            bucket=s3_staged_file.bucket,
            key=s3_staged_file.key,
            body=file_content,
        )
        logger.info("Uploaded MACD file to S3: %s", s3_staged_file.s3_uri)

        log_msg, exit_error, exit_success = self.setup_messaging(
            params=params,
            message="MACD File Upload Received, Processing",
            subject=f"{params.tool_name.upper()} - {params.tool_action.title()} File Upload",
        )
        try:
            proc_result = self.run_stored_procedure(
                params=params,
                proc_name=V2ProcedureNames.load_macd_data,
                logged_user=params.cisco_cco_id,
            )
            logger.info(
                "MACD Upload stored procedure completed successfully %s", proc_result
            )
            exit_success(msg="MACD Upload completed successfully")
        except ServiceException as e:
            logger.exception("Failed to run MACD Upload stored procedure")
            exit_error(msg=f"Failed to run MACD Upload stored procedure: {e.msg}")
            return
        except Exception as e:
            logger.exception("Failed to run MACD Upload stored procedure")
            exit_error(msg=f"Failed to run MACD Upload stored procedure: {e}")
            return


def process_sea_upload(
    payload: "V2SEAUploadPayload",
    file_content: bytes,
    engine: "Engine",
    settings: "AppSettings",
    s3_client: "S3Client",
    tracker: ExternalServiceTracker,
    request_id: int,
    notification_id: int,
    user: DcUserDict,
):
    service = UploadSPService(
        engine=engine,
        settings=settings,
        s3_client=s3_client,
        tracker=tracker,
        dc_engagement_id=payload.dc_engagement_id,
        dc_user_id=user["dc_user_id"],
        request_id=request_id,
        notification_id=notification_id,
        workflow_name="sea_upload",
        sp_name=V2ProcedureNames.load_sea_data,
        cisco_cco_id=user["cisco_cco_id"],
    )

    s3_staged_file = service.s3_staged_file
    params = V2SEAUploadParams(
        engagement_id=payload.dc_engagement_id,
        request_id=request_id,
        dc_user_id=user["dc_user_id"],
        cisco_cco_id=user["cisco_cco_id"],
        notification_id=notification_id,
        staged_file=s3_staged_file,
    )

    return service.upload_sea_data(
        params=params,
        file_content=file_content,
    )


def process_macd_upload(
    payload: "MacdSubmissionPayload",
    file_content: bytes,
    engine: "Engine",
    settings: "AppSettings",
    s3_client: "S3Client",
    tracker: ExternalServiceTracker,
    request_id: int,
    notification_id: int,
    user: DcUserDict,
):
    is_historical = payload.tool_name == "historical"
    workflow_prefix = "macd_historical_upload" if is_historical else "macd_upload"

    service = UploadSPService(
        engine=engine,
        settings=settings,
        s3_client=s3_client,
        tracker=tracker,
        dc_engagement_id=payload.dc_engagement_id,
        dc_user_id=user["dc_user_id"],
        request_id=request_id,
        notification_id=notification_id,
        workflow_name=f"{workflow_prefix}/{payload.tool_name}/{payload.tool_action}",
        sp_name=V2ProcedureNames.load_macd_data,
        cisco_cco_id=user["cisco_cco_id"],
    )

    s3_staged_file = service.s3_staged_file

    stmt = insert(MacdHdrTable).values(
        request_id=request_id,
        dc_engagement_id=payload.dc_engagement_id,
        dc_user_id=user["dc_user_id"],
        sign_off_identity_id=payload.sign_off_identity_id,
        staged_file_uri=s3_staged_file.s3_uri,
        snowflake_file_uri=s3_staged_file.snowflake_uri,
        row_count=0,
        approved_by=payload.approved_by,
        effective_date=payload.effective_date,
        tool_name=payload.tool_name,
        tool_action=payload.tool_action,
        notes=payload.notes,
        created_by=user["cisco_cco_id"],
    )
    with engine.begin() as conn:
        conn.execute(stmt)

    sp_params = V2MACDUploadParams(
        approved_by=payload.approved_by,
        engagement_id=payload.dc_engagement_id,
        dc_user_id=user["dc_user_id"],
        sign_off_identity_id=payload.sign_off_identity_id,
        effective_date=payload.effective_date,
        notes=payload.notes,
        notification_id=notification_id,
        request_id=request_id,
        tool_action=payload.tool_action,
        tool_name=payload.tool_name,
        staged_file=s3_staged_file,
        cisco_cco_id=user["cisco_cco_id"],
    )

    return service.upload_macd_data(params=sp_params, file_content=file_content)
