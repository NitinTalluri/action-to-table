from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from api.dependencies import get_settings
from api.dependencies.prefect import get_prefect_v3_client, get_prefect_v3_deployments
from api.v2 import ExternalServiceTracker
from api.v2.models import (
    UiEnum,
    V2CanvasPredefinedFileNames,
    V3CanvasCreate,
    CanvasType, V3CanvasRebuild,
)
from api.v2.models.canvas import V2CanvasPredefinedFiles
from api.v2.services.external.prefect_v3_flow_service import (
    PrefectV3FlowService,
    deployment_tags,
)


@pytest.fixture()
def mock_app_settings():
    settings = get_settings()
    return settings


# Fixture to mock HTTPX Client
@pytest.fixture
def prefect_httpx_client(mock_app_settings):
    client = get_prefect_v3_client(settings=mock_app_settings)
    assert client.headers.get("Authorization") != "Bearer None", "Bearer token not set"
    return client


@pytest_asyncio.fixture()
async def mock_tracker(mocker):
    mock = mocker.MagicMock(autospec=ExternalServiceTracker)
    mock.ui_enum = UiEnum.canvas_actions.value
    mock.default_subject = "test_canvas"
    mock.default_message = None
    mocker.patch("api.v2.ExternalServiceTracker.__init__", return_value=None)
    
    
    return mock
    

async def test_mock_tracker(mock_tracker):
    tracker =  mock_tracker()
    
    # user_attrs = {"user_id": 123, "cisco_cco_id": "testuser@cisco.com"}
    # mock_db_user = mocker.MagicMock(**user_attrs)
    #
    # notification_attrs = {
    #     "dc_engagement_id": 123,
    #     "notification_id": 123,
    # }
    # mock_notification = mocker.MagicMock(**notification_attrs)
    #
    # attrs = {
    #     "ui_enum": UiEnum.canvas_actions.value,
    #     "default_subject": "test_canvas",
    #     "create_job.return_value": (MagicMock(), mock_notification),
    # }
    #
    # mock = mocker.MagicMock(**attrs)

    return mock_tracker


@pytest.fixture()
def mock_user(mocker):
    mock = mocker.MagicMock()
    mock.user_id = 123
    mock.cisco_cco_id = "test_user@cisco.com"
    return mock


@pytest.fixture()
def canvas_payload_factory():
    def _canvas_payload_factory():
        model= V3CanvasCreate(
            canvas_name="test_canvas",
            dc_engagement_id=123,
            files=[
                V2CanvasPredefinedFiles(name=V2CanvasPredefinedFileNames.baseline_tags)
            ],
            tag_ids=[123],
            current_snapshot_name=None,
            historical_snapshot_name="test_snapshot",
            customer_request_ids=[123],
            collector_request_ids=[123],
            canvas_type=CanvasType.unified_view_canvas,
        )
        model._engagement_links = None
        return model

    return _canvas_payload_factory


@pytest.fixture()
def canvas_rebuild_payload_factory():
    def _canvas_rebuild_payload_factory():
        model = V3CanvasRebuild(
            canvas_name="test_canvas",
            dc_engagement_id=123,
            files=[
                V2CanvasPredefinedFiles(name=V2CanvasPredefinedFileNames.baseline_tags)
            ],
            tag_ids=[123],
            current_snapshot_name=None,
            historical_snapshot_name="test_snapshot",
            customer_request_ids=[123],
            collector_request_ids=[123],
            canvas_type=CanvasType.unified_view_canvas,
            canvas_id=123,
        )
        model._engagement_links = None
        return model
    

    return _canvas_rebuild_payload_factory


@pytest.fixture()
def mock_canvas_readable(mocker):
    with mocker.patch(
        "api.v2.services.external.prefect_v3_flow_service.canvas_readable",
        return_value={},
    ) as mock:
        yield mock


@pytest.fixture()
def mock_session(mocker):
    mock = mocker.MagicMock()
    return mock


@pytest.fixture()
def mock_s3_client(mocker):
    mock = mocker.MagicMock()
    return mock


@pytest.fixture()
def prefect_deployments(mock_app_settings, prefect_httpx_client):
    return get_prefect_v3_deployments(prefect_httpx_client, mock_app_settings)


def test_fetching_prefect_deployments(mock_app_settings, prefect_httpx_client):
    "Test that we can fetch deployments from Prefect V3 API"
    deployments = get_prefect_v3_deployments(
        client=prefect_httpx_client, settings=mock_app_settings
    )
    assert deployments is not None
    assert isinstance(deployments, list)
    for item in deployments:
        assert hasattr(item, "tags")
        print(item)


@pytest.mark.parametrize("tags", [{"create_canvas"}, {"rebuild_canvas"}])
def test_deployment_tags(prefect_deployments, mocker, tags):
    # Test that our decorator will find the correct deployment given the tags
    mock_service = mocker.MagicMock()
    mock_instance = mock_service.return_value
    mock_instance.deployments = prefect_deployments
    mock_instance.env = mocker.MagicMock(side_effect=lambda: "dev")

    def _run_some_deployment(self, deployment_id, **kwargs):
        return deployment_id, kwargs

    mock_instance.run_some_deployment = lambda: deployment_tags(tags)(
        _run_some_deployment
    )

    result_ = mock_instance.run_some_deployment()
    other_kwargs = {"param1": "value1", "param2": "value2"}
    result = result_(mock_instance, **other_kwargs)
    assert result[0] is not None
    assert isinstance(result[0], str)
    assert result[1] == other_kwargs

    print(tags, result)

class TestPrefectV3Deployments:
    @pytest.fixture()
    def client(self, mocker):
        return mocker.MagicMock()
    @pytest.fixture()
    def s3_client(self, mocker):
        return mocker.MagicMock()
    @pytest.fixture()
    def settings(self, mocker):
        return mocker.MagicMock()
    @pytest.fixture()
    def session(self, mocker):
        return mocker.MagicMock()
    @pytest.fixture()
    def deployments(self, mocker):
        return mocker.MagicMock()
    @pytest.fixture()
    def flow_service(self, client, s3_client, settings, session, deployments, mocker):
        
        reply = MagicMock()
        reply.id = 1
        reply.name = "test"
        
        def return_reply(*args, **kwargs):
            return reply
        
        service = PrefectV3FlowService(
            client=client,
            s3_client=s3_client,
            settings=settings,
            session=session,
            deployments=deployments,
        )
    
        
        for flow in {"create_canvas_flow", "rebuild_canvas_flow"}:
            mock = mocker.MagicMock(side_effect=return_reply)
            setattr(service, flow, mock)
            
            
        
        
        
       
        return service
        
    @pytest.fixture()
    def user(self, mocker):
        return mocker.MagicMock()
    @pytest.fixture()
    def tracker(self, mocker):
        mock_tracker = mocker.MagicMock(autospec=ExternalServiceTracker)
        mock_tracker.create_job.return_value = (MagicMock(), MagicMock())
        return mock_tracker
        
    def test_create_canvas_flow(self, flow_service, user, tracker, canvas_payload_factory):
        
        with flow_service as service:
            payload = canvas_payload_factory()
            _ = service.create_canvas_flow(
                canvas_id=123, payload=payload, requestor=user, tracker=tracker
            )
            
        flow_service.create_canvas_flow.assert_called_once()
    
    def test_rebuild_canvas_flow(
        self, flow_service, user, tracker, canvas_rebuild_payload_factory
        ):
        with flow_service as service:
            payload = canvas_rebuild_payload_factory()
            _ = service.rebuild_canvas_flow(
                canvas_id=123, payload=payload, requestor=user, tracker=tracker
            )
        
        
        flow_service.rebuild_canvas_flow.assert_called_once()
        
    
def test_create_flow_run_from_deployment(
    canvas_payload_factory,
    mocker,
):
    """
    Integration test that tests that we can create a flow run for creating a canvas
    We aren't actually creating a flow run, but we are testing that the method is called
    """
    
    def return_values(*args, **kwargs):
        return mocker.MagicMock()
    
    httpx_client = MagicMock()
    s3_client = MagicMock()
    settings = MagicMock()
    session = MagicMock()
    deployments = MagicMock()
    service = PrefectV3FlowService(
        client=httpx_client,
        s3_client=s3_client,
        settings=settings,
        session=session,
        deployments=deployments,
    )
    
    func_mock = mocker.MagicMock(side_effect=return_values)
    
    service.create_flow_run_from_deployment = func_mock
    
    # Unwrap the decorated method to inject a fake deployment id and avoid getting an exception
    unwrapped = service.create_canvas_flow.__wrapped__
    
    def inject_deployment_id(*args, **kwargs):
        return unwrapped(service, deployment_id="123", *args, **kwargs)
    
    service.create_canvas_flow = inject_deployment_id
    
    
    mock_user = MagicMock()
    mock_tracker = MagicMock()
    mock_tracker.create_job.return_value = MagicMock(), MagicMock()
    service.create_flow_run_from_deployment = mocker.Mock(side_effect=return_values)

    with service as flow_service:
        payload = canvas_payload_factory()
        _ = flow_service.create_canvas_flow(
            canvas_id=123, payload=payload, requestor=mock_user, tracker=mock_tracker
        )
    
    assert func_mock.called_once()


def test_emit_canvas_deleted_event(
    mock_app_settings,
    prefect_httpx_client,
    mock_session,
    mock_s3_client,
    mock_user,
    canvas_payload_factory,
):
    """
    Integration test that tests that we can emit a canvas deleted event
    """

    service = PrefectV3FlowService(
        client=prefect_httpx_client,
        s3_client=mock_s3_client,
        settings=mock_app_settings,
        session=mock_session,
        deployments=[],
    )

    with service as flow_service:
        payload = canvas_payload_factory()
        reply = flow_service.emit_canvas_deleted(
            canvas_id=123,
            dc_user_id=423,
            dc_engagement_id=payload.dc_engagement_id,
            notification_id=123,
            request_id=None,
        )
