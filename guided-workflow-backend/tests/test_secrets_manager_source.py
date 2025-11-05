import pytest

from api.dependencies import get_settings

@pytest.mark.parametrize(
    "env", ["dev", "prod"]
)
def test_secrets_manager_source(env, monkeypatch):
    # Test that our custom secrets manager source is working
    monkeypatch.setenv("RUN_ENV", env)
    settings = get_settings()
    assert settings.prefect_v3_settings.api_key is not None
    
    
    
    