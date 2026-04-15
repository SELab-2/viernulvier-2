import importlib
import sys

import pytest

REQUIRED_BASE_ENV = {
    "SECRET_KEY": "test-secret-key",
    "PUBLIC_API_KEY": "public-test-key",
    "INTERNAL_API_KEY": "internal-test-key",
}


def _fresh_import(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


@pytest.fixture(autouse=True)
def _set_required_base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in REQUIRED_BASE_ENV.items():
        monkeypatch.setenv(key, value)


def test_dev_settings_parse_hosts_cors_and_disable_throttles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOWED_HOSTS", " localhost, ,api.local ")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173, ,https://app.example.com ")

    dev = _fresh_import("config.settings.dev")

    assert dev.DEBUG is True
    assert dev.ALLOWED_HOSTS == ["localhost", "api.local"]
    assert dev.CORS_ALLOWED_ORIGINS == ["http://localhost:5173", "https://app.example.com"]
    assert dev.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] == []
    assert dev.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] == {}
    assert "rest_framework.renderers.BrowsableAPIRenderer" in dev.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]
    assert "x-api-key" in dev.CORS_ALLOW_HEADERS


def test_prod_settings_require_allowed_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)

    with pytest.raises(KeyError, match="ALLOWED_HOSTS"):
        _fresh_import("config.settings.prod")


def test_prod_settings_enable_security_and_build_csrf_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOWED_HOSTS", "api.example.com, www.example.com ")

    prod = _fresh_import("config.settings.prod")

    assert prod.DEBUG is False
    assert prod.ALLOWED_HOSTS == ["api.example.com", "www.example.com"]
    assert prod.SECURE_SSL_REDIRECT is True
    assert prod.SECURE_HSTS_SECONDS == 31_536_000
    assert prod.CSRF_TRUSTED_ORIGINS == ["https://api.example.com", "https://www.example.com"]
    assert prod.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] == {
        "public_min": "40/minute",
        "public_hour": "800/hour",
        "anon": "10/minute",
    }


def test_staging_settings_require_allowed_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)

    with pytest.raises(KeyError, match="ALLOWED_HOSTS"):
        _fresh_import("config.settings.staging")


def test_staging_settings_use_short_hsts_and_prod_like_throttling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOWED_HOSTS", "staging.example.com")

    staging = _fresh_import("config.settings.staging")

    assert staging.DEBUG is False
    assert staging.ALLOWED_HOSTS == ["staging.example.com"]
    assert staging.SECURE_SSL_REDIRECT is True
    assert staging.SECURE_HSTS_SECONDS == 300
    assert staging.CSRF_TRUSTED_ORIGINS == ["https://staging.example.com"]
    assert staging.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] == {
        "public_min": "40/minute",
        "public_hour": "800/hour",
        "anon": "10/minute",
    }
