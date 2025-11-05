import json
import os

import pytest
from contextlib import nullcontext as does_not_raise
from pydantic import BaseSettings, Field

from api.prefect_settings import RunConfigSetting
from api.settings import AppSettings


@pytest.fixture()
def json_settings_env(monkeypatch):
    kubernetes_run = dict(
        name="KubernetesRun",
        parameters=dict(
            memory_request="1024Mi",
            memory_limit="2048Mi",
        ),
    )
    dumped = json.dumps(kubernetes_run, separators=(",", ":"))
    with monkeypatch.context() as m:
        monkeypatch.setenv("KUBERNETES_RUN", dumped)
        yield



@pytest.fixture()
def environ_fixture(request):
    if not request.param:
        yield None, None
        return
    key, value = request.param
    if isinstance(value, dict):
        os.environ[key] = json.dumps(value)
    else:
        os.environ[key] = value
    yield key, value
    os.environ.pop(key)


@pytest.fixture()
def settings_fixture():
    class RunSettings(BaseSettings):
        kubernetes_run: RunConfigSetting = Field(
            env="KUBERNETES_RUN", default=dict(name="KubernetesRun", parameters=dict())
        )
        kubernetes_run_dict: RunConfigSetting = Field(
            default=dict(name="KubernetesRun", parameters=dict())
        )

    class Settings(BaseSettings):
        class Config:
            use_enum_values = True

        run_settings: RunSettings = None

        def __init__(self):
            super().__init__()
            self.run_settings = RunSettings()

    yield Settings


def test_settings_from_env(json_settings_env, settings_fixture):
    settings = settings_fixture()
    assert settings.run_settings.kubernetes_run.name == "KubernetesRun"
    params = settings.run_settings.kubernetes_run.parameters
    assert params["memory_request"] == "1024Mi"
    assert params["memory_limit"] == "2048Mi"


def test_prefect_settings_run_config():
    """Given either defaults or an .env file - test that the .to_object() method returns the correct object"""
    settings = AppSettings()
    prefect_settings = settings.prefect_settings
    run_configs = (k for k in dir(prefect_settings) if k.endswith("_RUN_CONFIG"))
    for k in run_configs:
        with does_not_raise():
            obj = getattr(prefect_settings, k).to_object()
