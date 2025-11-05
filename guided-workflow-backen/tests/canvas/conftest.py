import getpass
import uuid

import pytest

from fastapi import Request
from starlette.authentication import AuthCredentials

from api.v2 import PrefectFlowService, PrefectV3FlowService



class MockPrefectClient:
    def __init__(self):
        ...

    @staticmethod
    def create_flow_run(*args, **kwargs):
        print("Creating flow run", args, kwargs)
        return str(uuid.uuid4())


class MockS3Client:
    def __init__(self):
        ...

    @staticmethod
    def put_object(*args, **kwargs):
        print("Putting object", args, kwargs)
        return True


@pytest.fixture()
def default_overrides(mocker):
    from api.dependencies.aws import get_s3_client
    from api.dependencies.database import get_db_url
    from api.dependencies import login_required, DataCanvasUser
    from api.dependencies.prefect import get_prefect_client, get_prefect_v3_client, get_prefect_flow_service, get_prefect_v3_flow_service
    
    
    def _put_object(bucket, key, data):
        print(f"Putting object in {bucket} with key {key}")
        
    username = f"{getpass.getuser()}@cisco.com"
    

    

    def _decode_bearer(request: Request):
        user = DataCanvasUser(username=username, email=username, scopes={"dc_admin"})
        cred = AuthCredentials(scopes=list(user.scopes))
        request.scope["user"] = user
        request.scope["auth"] = cred
        return user

    def _get_prefect_service():
        # return MockPrefectClient()
        return mocker.MagicMock(spec=PrefectFlowService)
    
    def _get_prefect_v3_service():
        return mocker.MagicMock(spec=PrefectV3FlowService)

    def _get_s3_client():
        return mocker.MagicMock(spec=MockS3Client)

    return {
        login_required: _decode_bearer,
        get_prefect_flow_service: _get_prefect_service,
        get_prefect_v3_flow_service: _get_prefect_v3_service,
        get_s3_client: _get_s3_client,
    }


@pytest.fixture()
def test_app(default_overrides):
    from api.main import app

    for override, func in default_overrides.items():
        app.dependency_overrides[override] = func
    app.debug = True
    yield app


@pytest.fixture()
def test_client(test_app):
    from fastapi.testclient import TestClient

    with TestClient(test_app) as client:
        yield client
