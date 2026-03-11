"""
Tests for Viernulvier scraper fetch, error handling, and persistence.
"""

from __future__ import annotations

import datetime
import logging
import sys
import types
from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import IntegrityError, connection, models
from django.test.utils import isolate_apps

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    FKCache,
    M2MConfig,
    ModelSyncConfig,
    RateLimitError,
    ScraperError,
    TranslationConfig,
    _build_defaults,
    _discover_extra_pages,
    _parse_field_value,
    _sync_all_translations,
    _sync_m2m,
    clean_string,
    clean_vendor_id,
    normalize_performer_type,
    normalize_url,
    sync_viernulvier,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_build_session(monkeypatch, response_sequence=None, *, raise_exc=None):
    """
    Replace _build_session so that session.get returns controlled responses.

    response_sequence: list of (status_code, data) tuples, consumed in order.
    If the list is exhausted the last entry is repeated (handles retry loops).
    raise_exc: if given, session.get raises this exception on every call.
    """
    if response_sequence is None:
        response_sequence = [(200, [])]

    call_index = [0]

    def _make_response(status, data):
        r = Mock()
        r.status_code = status
        r.ok = status < 400
        r.headers = Mock()
        r.headers.get = Mock(return_value=None)
        if isinstance(data, Exception):
            r.json.side_effect = data
        else:
            r.json.return_value = data
        return r

    def fake_build_session():
        session = Mock()

        def fake_get(url, params=None, headers=None, timeout=None):
            if raise_exc is not None:
                raise raise_exc
            idx = min(call_index[0], len(response_sequence) - 1)
            status, data = response_sequence[idx]
            call_index[0] += 1
            return _make_response(status, data)

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)
    monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)

    return call_index


def _make_ok_response(data, etag=None):
    r = Mock()
    r.status_code = 200
    r.ok = True
    r.headers = Mock()
    r.headers.get = Mock(return_value=etag)
    r.json.return_value = data
    return r


def _make_status_response(status, headers=None):
    r = Mock()
    r.status_code = status
    r.ok = status < 400
    r.headers = Mock()
    header_dict = headers or {}
    r.headers.get = lambda k, d=None: header_dict.get(k, d)
    return r


def _mock_session(monkeypatch, responses_fn):
    """responses_fn(url, call_count) -> Mock response or raise."""
    call_count = [0]
    monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)

    def fake_build_session():
        session = Mock()

        def fake_get(url, params=None, headers=None, timeout=None):
            call_count[0] += 1
            return responses_fn(url, call_count[0])

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)
    return call_count


@contextmanager
def _temp_viernulvier_model():
    """Create a temporary in-memory model for sync tests with automatic cleanup."""

    class ViernulvierItem(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        title = models.CharField(max_length=255, null=True, blank=True)
        description = models.TextField(null=True, blank=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(ViernulvierItem)
    try:
        yield ViernulvierItem
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(ViernulvierItem)


class _PassThroughConfig(ModelSyncConfig):
    """Minimal config that maps '@id' as the lookup key (default api_id_key)."""

    def __init__(self):
        super().__init__(lookup_field="id")


def _reload_module(monkeypatch, tqdm_available: bool):
    """
    Reload your module with tqdm either present or absent in sys.modules.
    """
    # Remove cached version so the try/except runs again
    monkeypatch.delitem(sys.modules, "apps.imports.management.commands.sync_viernulvier", raising=False)

    if tqdm_available:
        # Make sure a real or stub tqdm exists
        if "tqdm" not in sys.modules:
            stub = types.ModuleType("tqdm")
            stub.tqdm = _StubTqdm
            monkeypatch.setitem(sys.modules, "tqdm", stub)
    else:
        # Force ImportError by removing tqdm from sys.modules
        monkeypatch.delitem(sys.modules, "tqdm", raising=False)
        # Inject a broken finder so 'import tqdm' raises ImportError
        monkeypatch.setitem(sys.modules, "tqdm", None)  # None -> ImportError

    import apps.imports.management.commands.sync_viernulvier

    return apps.imports.management.commands.sync_viernulvier


class _StubTqdm:
    """Minimal tqdm stand-in that records calls."""

    instances: list = []

    def __init__(self, *, total, desc, unit, leave):
        self.total = total
        self.desc = desc
        self.unit = unit
        self.leave = leave
        _StubTqdm.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def update(self, n=1):
        pass

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Tqdm presence handling
# ---------------------------------------------------------------------------


class TestWithTqdm:
    def test_tqdm_is_not_none(self, monkeypatch):
        mod = _reload_module(monkeypatch, tqdm_available=True)
        assert mod._tqdm is not None

    def test_make_progress_bar_returns_object(self, monkeypatch):
        mod = _reload_module(monkeypatch, tqdm_available=True)
        bar = mod._make_progress_bar("test", 10)
        assert bar is not None

    def test_make_progress_bar_is_context_manager(self, monkeypatch):
        mod = _reload_module(monkeypatch, tqdm_available=True)
        bar = mod._make_progress_bar("ctx", 5)
        # Must not raise when used as a context manager
        with bar:
            pass


class TestWithoutTqdm:
    def test_tqdm_is_none_when_missing(self, monkeypatch):
        mod = _reload_module(monkeypatch, tqdm_available=False)
        assert mod._tqdm is None

    def test_make_progress_bar_returns_none(self, monkeypatch):
        mod = _reload_module(monkeypatch, tqdm_available=False)
        result = mod._make_progress_bar("fallback", 99)
        assert result is None

    def test_make_progress_bar_accepts_any_args_without_crash(self, monkeypatch):
        mod = _reload_module(monkeypatch, tqdm_available=False)
        # Should never raise regardless of inputs
        mod._make_progress_bar("", 0)
        mod._make_progress_bar("x" * 100, 10_000_000)


@pytest.mark.parametrize("tqdm_available", [True, False])
def test_make_progress_bar_signature(monkeypatch, tqdm_available):
    """_make_progress_bar(name, total) must always accept exactly these two args."""
    mod = _reload_module(monkeypatch, tqdm_available=tqdm_available)
    import inspect

    sig = inspect.signature(mod._make_progress_bar)
    params = list(sig.parameters)
    assert params == ["name", "total"]


# ---------------------------------------------------------------------------
# fetch_viernulvier - HTTP layer
# ---------------------------------------------------------------------------


def test_fetch_raises_on_http_error(monkeypatch):
    """5xx errors after all retries are exhausted raise ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(500, "")] * (viernulvier.MAX_RETRIES + 1))

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_non_json_response(monkeypatch):
    """A payload that is not a list or dict raises ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(200, "not a dict or list")])

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_when_api_key_missing(monkeypatch):
    """Missing VIERNULVIER_API_KEY raises ScraperError before any HTTP call."""
    monkeypatch.delenv("VIERNULVIER_API_KEY", raising=False)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_invalid_json(monkeypatch):
    """A response whose .json() raises ValueError is wrapped in ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(200, ValueError("invalid json"))])

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_timeout(monkeypatch):
    """Connection timeouts after MAX_RETRIES raise ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(
        monkeypatch,
        raise_exc=requests.Timeout(),
    )

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_generic_request_exception(monkeypatch):
    """Non-retryable RequestException is immediately wrapped in ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(
        monkeypatch,
        raise_exc=requests.RequestException("connection failed"),
    )

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_none_payload(monkeypatch):
    """A null JSON payload raises ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(200, None)])

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_absolute_endpoint(monkeypatch):
    """Absolute URLs passed as endpoint are rejected immediately."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    with pytest.raises(viernulvier.ScraperError, match="endpoint must be a relative path"):
        viernulvier.fetch_viernulvier(endpoint="https://evil.com/events")

    with pytest.raises(viernulvier.ScraperError, match="endpoint must be a relative path"):
        viernulvier.fetch_viernulvier(endpoint="http://example.com/api")


def test_fetch_raises_on_json_ld_error_context(monkeypatch):
    """JSON-LD error context payload raises ScraperError with status/detail."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    error_payload = {
        "@context": "/api/contexts/Error",
        "status": 403,
        "detail": "Forbidden: access denied",
    }
    _mock_build_session(monkeypatch, [(200, error_payload)])

    with pytest.raises(viernulvier.ScraperError, match="status=403.*detail=Forbidden: access denied"):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_allows_different_endpoint_paths(monkeypatch):
    """Relative paths other than /productions are accepted."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    captured_url = {}

    def fake_build_session():
        session = Mock()
        mock_response = Mock(status_code=200, ok=True)
        mock_response.json.return_value = []
        mock_response.headers = Mock()
        mock_response.headers.get.return_value = None

        def fake_get(url, params=None, headers=None, timeout=None):
            captured_url["url"] = url
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    result = viernulvier.fetch_viernulvier(endpoint="/venues")
    assert result == []
    assert "venues" in captured_url["url"]


def test_fetch_dict_without_context_or_member_returns_empty(monkeypatch):
    """A dict payload without @context or member key returns an empty list."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(200, {"foo": "bar"})])

    result = viernulvier.fetch_viernulvier(endpoint="/events")
    assert result == []


def test_fetch_extracts_member_collection(monkeypatch):
    """JSON-LD member collection is returned as a flat list."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    payload = {
        "@context": "https://example.com/context.jsonld",
        "member": [
            {"@id": "https://example.com/1", "title": "Event A"},
            {"@id": "https://example.com/2", "title": "Event B"},
        ],
    }
    _mock_build_session(monkeypatch, [(200, payload)])

    result = viernulvier.fetch_viernulvier(endpoint="/events")

    assert len(result) == 2
    assert result[0]["@id"] == "https://example.com/1"
    assert result[1]["title"] == "Event B"


def test_fetch_collects_single_item_dict_with_context(monkeypatch):
    """A single-item dict with @context but no 'member' key is returned as one-element list."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    single_item = {"@context": "ctx", "@id": "/api/v1/events/1"}
    _mock_build_session(monkeypatch, [(200, single_item)])

    result = viernulvier.fetch_viernulvier(endpoint="/events")

    assert result == [single_item]


# ---------------------------------------------------------------------------
# fetch_viernulvier - query parameter support
# ---------------------------------------------------------------------------


def test_fetch_accepts_query_params(monkeypatch):
    """Params dict is forwarded to the first HTTP request."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    captured = {}

    def fake_build_session():
        session = Mock()
        mock_response = Mock(status_code=200, ok=True)
        mock_response.json.return_value = {"member": []}
        mock_response.headers = Mock()
        mock_response.headers.get.return_value = None

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["params"] = params
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    viernulvier.fetch_viernulvier(endpoint="/events", params={"created_at[after]": "2024-01-01T00:00:00Z"})

    assert captured["params"] == {"created_at[after]": "2024-01-01T00:00:00Z"}


def test_fetch_params_applied_to_initial_request_only(monkeypatch):
    """Query params are passed on page 1 only; sequential 'next' pages have no params."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    request_count = [0]
    captured_params_list = []

    def fake_build_session():
        session = Mock()

        def fake_get(url, params=None, headers=None, timeout=None):
            request_count[0] += 1
            captured_params_list.append(params)
            mock_response = Mock(status_code=200, ok=True)
            mock_response.headers = Mock()
            mock_response.headers.get.return_value = None

            if request_count[0] == 1:
                mock_response.json.return_value = {
                    "@context": "https://example.com/context.jsonld",
                    "member": [{"@id": "https://example.com/1", "title": "A"}],
                    "view": {"next": "https://example.com/api/v1/events?page=2"},
                }
            else:
                mock_response.json.return_value = {
                    "@context": "https://example.com/context.jsonld",
                    "member": [{"@id": "https://example.com/2", "title": "B"}],
                }
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    result = viernulvier.fetch_viernulvier(endpoint="/events", params={"created_at[after]": "2024-01-01T00:00:00Z"})

    assert len(result) == 2
    assert captured_params_list[0] == {"created_at[after]": "2024-01-01T00:00:00Z"}
    assert captured_params_list[1] is None


def test_fetch_with_multiple_query_params(monkeypatch):
    """Multiple query parameters are all forwarded correctly."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    captured = {}

    def fake_build_session():
        session = Mock()
        mock_response = Mock(status_code=200, ok=True)
        mock_response.json.return_value = {"member": []}
        mock_response.headers = Mock()
        mock_response.headers.get.return_value = None

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["params"] = params
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    params = {
        "created_at[after]": "2024-01-01T00:00:00Z",
        "updated_at[before]": "2024-12-31T23:59:59Z",
    }
    viernulvier.fetch_viernulvier(endpoint="/events", params=params)

    assert captured["params"] == params


def test_fetch_without_params_sends_none(monkeypatch):
    """Calling fetch without params passes None to the HTTP layer."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    captured = {}

    def fake_build_session():
        session = Mock()
        mock_response = Mock(status_code=200, ok=True)
        mock_response.json.return_value = {"member": []}
        mock_response.headers = Mock()
        mock_response.headers.get.return_value = None

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["params"] = params
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    viernulvier.fetch_viernulvier(endpoint="/events")

    assert captured["params"] is None


def test_fetch_preserves_timestamp_format(monkeypatch):
    """ISO 8601 timestamp strings in params are not modified."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    captured = {}

    def fake_build_session():
        session = Mock()
        mock_response = Mock(status_code=200, ok=True)
        mock_response.json.return_value = {"member": []}
        mock_response.headers = Mock()
        mock_response.headers.get.return_value = None

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["params"] = params
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    iso_timestamp = "2024-12-25T10:30:45Z"
    viernulvier.fetch_viernulvier(endpoint="/events", params={"created_at[after]": iso_timestamp})

    assert captured["params"]["created_at[after]"] == iso_timestamp


# ---------------------------------------------------------------------------
# HTTP Retry edge cases
# ---------------------------------------------------------------------------


class TestHTTPRetryEdgeCases:
    def test_parse_retry_after_integer_header(self):
        from apps.imports.scrapers.viernulvier import _parse_retry_after

        r = Mock()
        r.headers = Mock()
        r.headers.get = Mock(return_value="30")
        assert _parse_retry_after(r) == 30

    def test_parse_retry_after_non_integer_returns_none(self):
        from apps.imports.scrapers.viernulvier import _parse_retry_after

        r = Mock()
        r.headers = Mock()
        r.headers.get = Mock(return_value="Wed, 21 Oct 2015 07:28:00 GMT")
        assert _parse_retry_after(r) is None

    def test_parse_retry_after_missing_returns_none(self):
        from apps.imports.scrapers.viernulvier import _parse_retry_after

        r = Mock()
        r.headers = Mock()
        r.headers.get = Mock(return_value=None)
        assert _parse_retry_after(r) is None

    def test_429_with_numeric_retry_after_uses_header_as_wait(self, monkeypatch):
        """HTTP 429 with numeric Retry-After uses that value as the sleep time."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        call_count = [0]

        def responses(url, n):
            call_count[0] = n
            if n == 1:
                r = _make_status_response(429, {"Retry-After": "45"})
                r.ok = False
                return r
            return _make_ok_response([])

        # _mock_session patches time.sleep to a no-op; overwrite it afterwards
        # so the capture lambda wins.
        _mock_session(monkeypatch, responses)
        sleep_args = []
        monkeypatch.setattr(viernulvier.time, "sleep", lambda t: sleep_args.append(t))

        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert result == []
        assert 45.0 in sleep_args

    def test_429_without_retry_after_uses_backoff(self, monkeypatch):
        """HTTP 429 with no Retry-After falls back to exponential backoff."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            if n == 1:
                r = _make_status_response(429, {})
                r.ok = False
                return r
            return _make_ok_response([])

        # Overwrite after _mock_session so our capture lambda wins.
        _mock_session(monkeypatch, responses)
        sleep_args = []
        monkeypatch.setattr(viernulvier.time, "sleep", lambda t: sleep_args.append(t))

        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert result == []
        assert sleep_args and sleep_args[0] != 45.0

    def test_429_all_retries_exhausted_raises_rate_limit_error(self, monkeypatch):
        """RateLimitError raised when all 429 retries exhausted."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)

        def responses(url, n):
            r = _make_status_response(429, {"Retry-After": "1"})
            r.ok = False
            return r

        _mock_session(monkeypatch, responses)
        with pytest.raises(RateLimitError) as exc_info:
            viernulvier.fetch_viernulvier(endpoint="/events")
        assert exc_info.value.retry_after == 1

    def test_429_without_retry_after_raises_with_none(self, monkeypatch):
        """RateLimitError.retry_after is None when Retry-After header is absent."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)

        def responses(url, n):
            r = _make_status_response(429, {})
            r.ok = False
            return r

        _mock_session(monkeypatch, responses)
        with pytest.raises(RateLimitError) as exc_info:
            viernulvier.fetch_viernulvier(endpoint="/events")
        assert exc_info.value.retry_after is None

    def test_5xx_retries_then_succeeds(self, monkeypatch):
        """5xx on attempt 1, success on attempt 2."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            if n == 1:
                r = _make_status_response(503, {})
                r.ok = False
                return r
            return _make_ok_response({"member": [{"@id": "1"}]})

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 1

    def test_connection_error_retries_then_succeeds(self, monkeypatch):
        """ConnectionError on attempt 1, success on attempt 2."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        call_count = [0]

        def responses(url, n):
            call_count[0] = n
            if n == 1:
                raise requests.ConnectionError("network down")
            return _make_ok_response([])

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert result == []
        assert call_count[0] == 2

    def test_connection_error_all_retries_exhausted(self, monkeypatch):
        """ScraperError raised after all ConnectionError retries exhausted."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            raise requests.ConnectionError("always down")

        _mock_session(monkeypatch, responses)
        with pytest.raises(ScraperError, match="Connection failed"):
            viernulvier.fetch_viernulvier(endpoint="/events")

    def test_timeout_retries_then_succeeds(self, monkeypatch):
        """Timeout on attempt 1, success on attempt 2."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            if n == 1:
                raise requests.Timeout()
            return _make_ok_response([])

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert result == []

    def test_304_not_modified_returns_empty_and_preserves_etag(self, monkeypatch):
        """304 returns empty list; cached ETag is preserved in etag_cache."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            return _make_status_response(304, {})

        _mock_session(monkeypatch, responses)
        etag_cache = {"https://www.viernulvier.gent/api/v1/events": "old-etag"}
        result = viernulvier.fetch_viernulvier(endpoint="/events", etag_cache=etag_cache)
        assert result == []
        assert etag_cache["https://www.viernulvier.gent/api/v1/events"] == "old-etag"

    def test_etag_from_response_stored_in_cache(self, monkeypatch):
        """ETag header in response is stored in etag_cache."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            return _make_ok_response({"member": []}, etag="new-etag-789")

        _mock_session(monkeypatch, responses)
        etag_cache = {}
        viernulvier.fetch_viernulvier(endpoint="/events", etag_cache=etag_cache)
        assert "new-etag-789" in etag_cache.values()

    def test_list_payload_returned_directly(self, monkeypatch):
        """A plain JSON list (not dict) is returned as-is."""
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            return _make_ok_response([{"@id": "1"}, {"@id": "2"}])

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 2


# ---------------------------------------------------------------------------
# RateLimitError
# ---------------------------------------------------------------------------


def test_rate_limit_error_with_retry_after():
    err = RateLimitError(retry_after=120)
    assert err.retry_after == 120
    assert "120" in str(err)


def test_rate_limit_error_without_retry_after():
    err = RateLimitError()
    assert err.retry_after is None
    assert "Rate limited" in str(err)


# ---------------------------------------------------------------------------
# _backoff_seconds
# ---------------------------------------------------------------------------


def test_backoff_seconds_capped_at_max():
    from apps.imports.scrapers.viernulvier import RETRY_BACKOFF_MAX, _backoff_seconds

    for attempt in range(10):
        val = _backoff_seconds(attempt)
        assert 0 < val <= RETRY_BACKOFF_MAX


def test_backoff_seconds_increases_with_attempt():
    from apps.imports.scrapers.viernulvier import _backoff_seconds

    avg_0 = sum(_backoff_seconds(0) for _ in range(20)) / 20
    avg_3 = sum(_backoff_seconds(3) for _ in range(20)) / 20
    assert avg_3 > avg_0


# ---------------------------------------------------------------------------
# _discover_extra_pages
# ---------------------------------------------------------------------------


class TestDiscoverExtraPages:
    def test_no_view_key_returns_empty(self):
        assert _discover_extra_pages({}) == []

    def test_empty_view_returns_empty(self):
        assert _discover_extra_pages({"view": {}}) == []

    def test_last_url_without_page_param_returns_empty(self):
        data = {"view": {"last": "https://example.com/api/events"}}
        assert _discover_extra_pages(data) == []

    def test_last_url_with_page_param_returns_pages_2_to_n(self):
        data = {"view": {"last": "https://www.viernulvier.gent/api/v1/events?page=4"}}
        pages = _discover_extra_pages(data)
        assert len(pages) == 3
        assert all("page=" in p for p in pages)
        assert "page=2" in pages[0]
        assert "page=4" in pages[2]

    def test_relative_last_url_becomes_absolute(self):
        data = {"view": {"last": "/api/v1/events?page=3"}}
        pages = _discover_extra_pages(data)
        assert all(p.startswith("http") for p in pages)

    def test_single_page_url_returns_empty(self):
        """If last=page=1, there are no extra pages."""
        data = {"view": {"last": "https://example.com/api/events?page=1"}}
        pages = _discover_extra_pages(data)
        assert pages == []


# ---------------------------------------------------------------------------
# Pagination - concurrent + sequential edge cases
# ---------------------------------------------------------------------------


class TestConcurrentPagination:
    def test_fetches_all_pages_concurrently(self, monkeypatch):
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            if "page=2" in url:
                return _make_ok_response({"member": [{"@id": "2"}]})
            if "page=3" in url:
                return _make_ok_response({"member": [{"@id": "3"}]})
            return _make_ok_response(
                {
                    "@context": "ctx",
                    "member": [{"@id": "1"}],
                    "totalItems": 3,
                    "view": {"last": "https://www.viernulvier.gent/api/v1/events?page=3"},
                }
            )

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 3

    def test_page_fetch_error_logged_and_other_pages_returned(self, monkeypatch, caplog):
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            if "page=2" in url:
                raise ScraperError("page 2 failed")
            return _make_ok_response(
                {
                    "@context": "ctx",
                    "member": [{"@id": "1"}],
                    "totalItems": 2,
                    "view": {"last": "https://www.viernulvier.gent/api/v1/events?page=2"},
                }
            )

        _mock_session(monkeypatch, responses)
        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert any(item["@id"] == "1" for item in result)
        assert any("Page fetch failed" in r.message for r in caplog.records)

    def test_304_on_concurrent_page_silently_skipped(self, monkeypatch):
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            if "page=2" in url:
                return _make_status_response(304, {})
            return _make_ok_response(
                {
                    "@context": "ctx",
                    "member": [{"@id": "1"}],
                    "totalItems": 2,
                    "view": {"last": "https://www.viernulvier.gent/api/v1/events?page=2"},
                }
            )

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 1


class TestSequentialFallback:
    def test_304_on_next_page_breaks_loop(self, monkeypatch):
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        call_count = [0]

        def responses(url, n):
            call_count[0] = n
            if n == 1:
                return _make_ok_response(
                    {
                        "@context": "ctx",
                        "member": [{"@id": "1"}],
                        "view": {"next": "https://www.viernulvier.gent/api/v1/events?page=2"},
                    }
                )
            return _make_status_response(304, {})

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 1

    def test_relative_next_url_made_absolute(self, monkeypatch):
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        captured_urls = []

        def responses(url, n):
            captured_urls.append(url)
            if n == 1:
                return _make_ok_response(
                    {
                        "@context": "ctx",
                        "member": [{"@id": "1"}],
                        "view": {"next": "/api/v1/events?page=2"},
                    }
                )
            return _make_ok_response({"member": [{"@id": "2"}]})

        _mock_session(monkeypatch, responses)
        viernulvier.fetch_viernulvier(endpoint="/events")
        assert captured_urls[1].startswith("http")

    def test_list_response_on_next_page_appended(self, monkeypatch):
        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        call_count = [0]

        def responses(url, n):
            call_count[0] = n
            if n == 1:
                return _make_ok_response(
                    {
                        "@context": "ctx",
                        "member": [{"@id": "1"}],
                        "view": {"next": "https://www.viernulvier.gent/api/v1/events?page=2"},
                    }
                )
            return _make_ok_response([{"@id": "2"}, {"@id": "3"}])

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 3


# ---------------------------------------------------------------------------
# sync_viernulvier - basic persistence
# ---------------------------------------------------------------------------


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_persists_items(monkeypatch):
    """Items returned by fetch are persisted to the database."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "A"},
                {"@id": "https://example.com/2", "title": "B"},
            ],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 2
        assert ViernulvierItem.objects.count() == 2


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_updates_existing_item(monkeypatch):
    """Existing records are updated, not duplicated."""
    with _temp_viernulvier_model() as ViernulvierItem:
        ViernulvierItem.objects.create(id="https://example.com/1", title="old")

        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [{"@id": "https://example.com/1", "title": "new"}],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert ViernulvierItem.objects.get(id="https://example.com/1").title == "new"


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_items_without_id(monkeypatch, caplog):
    """Items with no @id are skipped and a warning is logged."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [{"title": "no id"}],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Missing '@id' in item:" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_empty_string_id(monkeypatch, caplog):
    """An empty string @id is treated the same as missing."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [{"@id": "", "title": "A"}],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Missing '@id' in item:" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_duplicate_ids_in_batch(monkeypatch, caplog):
    """Duplicate @id values within the same batch are deduplicated."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "A"},
                {"@id": "https://example.com/1", "title": "B"},
            ],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert any("Duplicate item skipped:" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_handles_special_chars_and_nulls(monkeypatch):
    """Unicode chars are stored correctly; None values are stored as NULL."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {
                    "@id": "https://example.com/9",
                    "title": "Café 🎭",
                    "description": None,
                }
            ],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        obj = ViernulvierItem.objects.get(id="https://example.com/9")
        assert obj.title == "Café 🎭"
        assert obj.description is None


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_handles_large_payload(monkeypatch):
    """50-item batch is fully persisted."""
    with _temp_viernulvier_model() as ViernulvierItem:
        items = [{"@id": f"https://example.com/{i}", "title": f"T{i}"} for i in range(50)]
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: items,
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 50
        assert ViernulvierItem.objects.count() == 50


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_on_database_errors(monkeypatch, caplog):
    """One item failing with IntegrityError does not abort the rest of the batch."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "A"},
                {"@id": "https://example.com/2", "title": "B"},
            ],
        )

        call_count = [0]
        original = ViernulvierItem.objects.update_or_create

        def boom_once(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise IntegrityError("boom")
            return original(*args, **kwargs)

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", boom_once)
        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert any("Database error" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_all_items_fail_returns_zero(monkeypatch):
    """All items failing returns 0 saved."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "A"},
                {"@id": "https://example.com/2", "title": "B"},
            ],
        )

        def boom(*_args, **_kwargs):
            raise IntegrityError("boom")

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", boom)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_logs_finish_message_with_saved_and_error_count(monkeypatch, caplog):
    """Sync completion log contains saved= and errors= counts."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "A"},
                {"title": "no id"},
            ],
        )

        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        assert any(
            "Sync complete:" in r.message and "saved=1" in r.message and "errors=1" in r.message for r in caplog.records
        )


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_when_item_is_not_dict(monkeypatch, caplog):
    """Non-dict items in the fetch result are logged as errors and skipped."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                "not-a-dict",
                {"@id": "https://example.com/2", "title": "B"},
            ],
        )

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert any("Item is not a dict" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_passes_params_to_fetch(monkeypatch):
    """sync_viernulvier forwards query parameters to fetch_viernulvier."""
    with _temp_viernulvier_model() as ViernulvierItem:
        captured = {}

        def mock_fetch(endpoint=None, params=None, etag_cache=None):
            captured["endpoint"] = endpoint
            captured["params"] = params
            return [{"@id": "https://example.com/1", "title": "Item"}]

        monkeypatch.setattr(viernulvier, "fetch_viernulvier", mock_fetch)

        params = {"created_at[after]": "2024-01-01T00:00:00Z"}
        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events", params=params)

        assert captured["endpoint"] == "/events"
        assert captured["params"] == params


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_without_params_still_works(monkeypatch):
    """Backward compatibility: sync works when params is omitted."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "Item"},
            ],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1


# ---------------------------------------------------------------------------
# sync_viernulvier - dry_run / on_progress / item_filter / MAX_ERROR_MESSAGES
# ---------------------------------------------------------------------------


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_dry_run_does_not_write_to_db(monkeypatch):
    """dry_run=True fetches and parses but writes nothing."""
    with _temp_viernulvier_model() as M:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **_: [
                {"@id": "https://example.com/1", "title": "A"},
                {"@id": "https://example.com/2", "title": "B"},
            ],
        )
        count = sync_viernulvier(M, _PassThroughConfig(), endpoint="/e", dry_run=True)
        assert count == 2
        assert M.objects.count() == 0


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_on_progress_called_with_cumulative_counts(monkeypatch):
    """on_progress is called after each save with (saved, total)."""
    with _temp_viernulvier_model() as M:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **_: [{"@id": f"https://example.com/{i}", "title": str(i)} for i in range(3)],
        )
        calls = []
        sync_viernulvier(
            M,
            _PassThroughConfig(),
            endpoint="/e",
            on_progress=lambda saved, total: calls.append((saved, total)),
        )
        assert calls == [(1, 3), (2, 3), (3, 3)]


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_dry_run_on_progress_also_called(monkeypatch):
    """on_progress is also invoked in dry_run mode."""
    with _temp_viernulvier_model() as M:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **_: [{"@id": "https://example.com/1"}],
        )
        calls = []
        sync_viernulvier(
            M,
            _PassThroughConfig(),
            endpoint="/e",
            dry_run=True,
            on_progress=lambda s, t: calls.append((s, t)),
        )
        assert calls == [(1, 1)]


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_item_filter_excludes_items(monkeypatch):
    """item_filter returning False causes the item to be skipped."""
    with _temp_viernulvier_model() as M:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **_: [
                {"@id": "https://example.com/keep/1"},
                {"@id": "https://example.com/longterm/2"},
            ],
        )
        config = ModelSyncConfig(
            lookup_field="id",
            item_filter=lambda item: "longterm" not in item.get("@id", ""),
        )
        count = sync_viernulvier(M, config, endpoint="/e")
        assert count == 1
        assert M.objects.count() == 1


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_max_error_messages_capped(monkeypatch):
    """Error messages list is capped at MAX_ERROR_MESSAGES."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as M:
        n = viernulvier.MAX_ERROR_MESSAGES + 5
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **_: [{"title": f"no-id-{i}"} for i in range(n)],
        )
        sync_viernulvier(M, _PassThroughConfig(), endpoint="/e")
        log = ImportLog.objects.first()
        assert f"showing first {viernulvier.MAX_ERROR_MESSAGES} of" in log.error_message


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_etag_cache_passed_to_fetch(monkeypatch):
    """sync_viernulvier passes the same etag_cache object to fetch_viernulvier."""
    with _temp_viernulvier_model() as M:
        captured = {}
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint=None, params=None, etag_cache=None: captured.update({"etag_cache": etag_cache}) or [],
        )
        shared_cache = {"key": "val"}
        sync_viernulvier(M, _PassThroughConfig(), endpoint="/e", etag_cache=shared_cache)
        assert captured["etag_cache"] is shared_cache


# ---------------------------------------------------------------------------
# ImportLog integration
# ---------------------------------------------------------------------------


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_creates_import_log_on_success(monkeypatch):
    """Successful sync creates a SUCCESS ImportLog with correct counters."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
                {"@id": "https://example.com/2", "title": "Event B"},
            ],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 2
        assert ImportLog.objects.count() == 1
        log = ImportLog.objects.first()

        assert log.source == "viernulvier:/events"
        assert log.status == ImportLog.Status.SUCCESS
        assert log.records_total == 2
        assert log.records_imported == 2
        assert log.records_failed == 0
        assert log.started_at is not None
        assert log.finished_at is not None
        assert log.finished_at >= log.started_at
        assert log.error_message is None


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_creates_import_log_with_params_in_source(monkeypatch):
    """Params are included (sorted) in the ImportLog source field."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        params = {"created_at[after]": "2024-01-01T00:00:00Z", "page": "1"}
        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events", params=params)

        log = ImportLog.objects.first()
        assert "viernulvier:/events?" in log.source
        assert "created_at[after]=2024-01-01T00:00:00Z" in log.source
        assert "page=1" in log.source


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_creates_import_log_on_partial_success(monkeypatch):
    """Some items failing creates a PARTIAL_SUCCESS ImportLog."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
                {"title": "Event B"},
                {"@id": "https://example.com/3", "title": "Event C"},
            ],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 2
        log = ImportLog.objects.first()
        assert log.status == ImportLog.Status.PARTIAL_SUCCESS
        assert log.records_total == 3
        assert log.records_imported == 2
        assert log.records_failed == 1
        assert log.error_message is not None


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_creates_import_log_on_all_failures(monkeypatch):
    """All items failing creates a FAILED ImportLog."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"title": "Event A"},
                {"title": "Event B"},
            ],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        log = ImportLog.objects.first()
        assert log.status == ImportLog.Status.FAILED
        assert log.records_total == 2
        assert log.records_imported == 0
        assert log.records_failed == 2
        assert log.error_message.startswith("All 2 records failed")


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_creates_import_log_on_fetch_exception(monkeypatch):
    """fetch_viernulvier raising an exception creates a FAILED ImportLog."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:

        def failing_fetch(endpoint="/events", params=None, etag_cache=None):
            raise viernulvier.ScraperError("API connection failed")

        monkeypatch.setattr(viernulvier, "fetch_viernulvier", failing_fetch)

        with pytest.raises(viernulvier.ScraperError):
            viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        log = ImportLog.objects.first()
        assert log.status == ImportLog.Status.FAILED
        assert log.started_at is not None
        assert log.finished_at is not None
        assert log.error_message == "API connection failed"
        assert log.records_total == 0
        assert log.records_imported == 0
        assert log.records_failed == 0


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_creates_import_log_on_empty_response(monkeypatch):
    """Empty API response creates a SUCCESS ImportLog with all-zero counters."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        log = ImportLog.objects.first()
        assert log.status == ImportLog.Status.SUCCESS
        assert log.records_total == 0
        assert log.records_imported == 0
        assert log.records_failed == 0


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_import_log_timestamps_are_sequential(monkeypatch):
    """finished_at >= started_at in the ImportLog."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        log = ImportLog.objects.first()
        assert log.finished_at >= log.started_at


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_import_log_tracks_multiple_syncs(monkeypatch):
    """Each sync call creates its own ImportLog entry."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")
        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert ImportLog.objects.count() == 2
        logs = ImportLog.objects.order_by("started_at")
        assert logs[0].records_imported == 1
        assert logs[1].records_imported == 1


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_import_log_different_endpoints_tracked_separately(monkeypatch):
    """Different endpoints get separate ImportLog source values."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")
        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/venues")

        sources = list(ImportLog.objects.values_list("source", flat=True))
        assert "viernulvier:/events" in sources
        assert "viernulvier:/venues" in sources


# ---------------------------------------------------------------------------
# sync_viernulvier - error branches & savepoints
# ---------------------------------------------------------------------------


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_validation_error_formats_messages(monkeypatch):
    """ValidationError messages (per-field and __all__) are included in ImportLog."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [{"@id": "1", "title": "A"}],
        )

        def raise_validation(*_args, **_kwargs):
            raise ValidationError({"title": ["invalid"], "__all__": ["bad state"]})

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", raise_validation)

        saved = viernulvier.sync_viernulvier(ViernulvierItem, ModelSyncConfig(lookup_field="id"), endpoint="/events")

        assert saved == 0
        log = ImportLog.objects.first()
        assert log.status == ImportLog.Status.FAILED
        assert "title: invalid" in log.error_message
        assert "bad state" in log.error_message


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_database_error_branch(monkeypatch):
    """IntegrityError is caught and logged as a database error."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [{"@id": "1", "title": "A"}],
        )

        def raise_integrity(*_args, **_kwargs):
            raise IntegrityError("db exploded")

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", raise_integrity)

        saved = viernulvier.sync_viernulvier(ViernulvierItem, ModelSyncConfig(lookup_field="id"), endpoint="/events")

        assert saved == 0
        log = ImportLog.objects.first()
        assert "Database error for 1" in log.error_message
        assert log.records_total == 1
        assert log.records_failed == 1


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_unexpected_error_branch(monkeypatch):
    """Non-DB exceptions are caught and still finalize the ImportLog."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [{"@id": "1", "title": "A"}],
        )

        def raise_runtime(*_args, **_kwargs):
            raise RuntimeError("unexpected crash")

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", raise_runtime)

        saved = viernulvier.sync_viernulvier(ViernulvierItem, ModelSyncConfig(lookup_field="id"), endpoint="/events")

        assert saved == 0
        log = ImportLog.objects.first()
        assert "Unexpected error for 1: RuntimeError: unexpected crash" in log.error_message
        assert log.records_total == 1
        assert log.records_failed == 1


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_calls_m2m_and_commits_savepoint(monkeypatch):
    """M2M sync is invoked and savepoint is committed on success."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [{"@id": "1", "title": "A", "rels": []}],
        )

        called = {"m2m": 0, "commits": 0}

        monkeypatch.setattr(
            viernulvier,
            "_sync_m2m",
            lambda *_args, **_kwargs: called.__setitem__("m2m", called["m2m"] + 1),
        )
        monkeypatch.setattr(viernulvier.transaction, "savepoint", lambda: "sid-1")
        monkeypatch.setattr(
            viernulvier.transaction,
            "savepoint_commit",
            lambda _sid: called.__setitem__("commits", called["commits"] + 1),
        )

        config = ModelSyncConfig(
            lookup_field="id",
            m2m=[
                M2MConfig(
                    api_key="rels",
                    related_model=object,
                    through_model=object,
                    parent_fk="parent",
                    related_fk="related",
                )
            ],
        )

        saved = viernulvier.sync_viernulvier(ViernulvierItem, config, endpoint="/events")

        assert saved == 1
        assert called["m2m"] == 1
        assert called["commits"] == 1
        assert ImportLog.objects.first().records_total == 1


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_executes_translations(monkeypatch):
    """_sync_all_translations is called when translation config is provided."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [{"@id": "1", "title": "A"}],
        )

        called = {"translations": 0}

        def fake_sync_all_translations(*_args, **_kwargs):
            called["translations"] += 1

        monkeypatch.setattr(viernulvier, "_sync_all_translations", fake_sync_all_translations)

        config = ModelSyncConfig(
            lookup_field="id",
            translations=[
                TranslationConfig(
                    api_key="title",
                    model=object,
                    parent_fk="parent",
                    flat_field="title",
                )
            ],
        )

        saved = viernulvier.sync_viernulvier(ViernulvierItem, config, endpoint="/events")

        assert saved == 1
        assert called["translations"] == 1


# ---------------------------------------------------------------------------
# Flexible field mapping / _build_defaults
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFlexibleFieldMapping:
    def test_throws_no_error_for_year_minus_one_date(self):
        """Negative-year datetime strings are repaired and parsed."""
        from apps.events.models import Event

        field = Event._meta.get_field("starts_at")
        result = _parse_field_value(field, "-0001-01-01T00:00:00+00:00")

        assert result == datetime.datetime(1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    def test_throws_no_error_for_year_zero_date(self):
        """Year-0000 datetime strings are repaired to 1970."""
        from apps.events.models import Event

        field = Event._meta.get_field("starts_at")
        result = _parse_field_value(field, "0000-01-01T00:00:00+00:00")

        assert result == datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    def test_returns_none_for_missing_value(self):
        from apps.events.models import Event

        field = Event._meta.get_field("starts_at")
        assert _parse_field_value(field, None) is None

    def test_build_defaults_does_not_raise_for_missing_required_fields(self):
        """_build_defaults doesn't validate; it only builds the defaults dict."""
        from apps.events.models import Event

        item = {
            "external_id": "/api/events/1",
            "ticketing_url": "https://example.com",
        }
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(Event, item, _PassThroughConfig(), fk_cache)

        assert "ticketing_url" in defaults
        assert defaults["ticketing_url"] == "https://example.com"

    def test_skips_unknown_fields_event_price(self):
        """Unknown API fields are silently ignored."""
        from apps.events.models import Event, EventPrice
        from apps.pricing.models import PriceRank
        from apps.productions.models import Production

        prod = Production.objects.create(external_id="/api/productions/1")
        event = Event.objects.create(external_id="1", production=prod)
        price_rank = PriceRank.objects.create(external_id="1", position=1)

        item = {
            "external_id": "/api/event_prices/1",
            "event": event.external_id,
            "priceRank": price_rank.external_id,
            "amount": "25.50",
            "available": 100,
            "unknownField": "should be ignored",
            "anotherUnknownField": 123,
            "yetAnotherField": {"nested": "object"},
        }
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(EventPrice, item, _PassThroughConfig(), fk_cache)

        assert "event_id" in defaults
        assert "price_rank_id" in defaults
        assert "amount" in defaults
        assert "available" in defaults
        assert "unknownField" not in defaults
        assert "unknown_field" not in defaults
        assert "anotherUnknownField" not in defaults
        assert "another_unknown_field" not in defaults

    def test_handles_known_fields_correctly(self):
        """Known FK and scalar fields are resolved and placed in defaults."""
        from apps.events.models import Event, EventPrice
        from apps.pricing.models import PriceRank
        from apps.productions.models import Production

        prod = Production.objects.create(external_id="/api/productions/3")
        event = Event.objects.create(external_id="3", production=prod)
        price_rank = PriceRank.objects.create(external_id="3", position=3)

        item = {
            "external_id": "/api/event_prices/3",
            "event": event.external_id,
            "priceRank": price_rank.external_id,
            "amount": "20.00",
            "available": 75,
        }
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(EventPrice, item, _PassThroughConfig(), fk_cache)

        assert "price_rank_id" in defaults
        assert "event_id" in defaults
        assert "amount" in defaults


# ---------------------------------------------------------------------------
# _parse_field_value - comprehensive type coverage
# ---------------------------------------------------------------------------


class TestParseFieldValue:
    def test_charfield_cleans_and_returns(self):
        f = models.CharField(max_length=100)
        assert _parse_field_value(f, "  hello  ") == "hello"

    def test_charfield_truncates_to_max_length(self):
        f = models.CharField(max_length=5)
        result = _parse_field_value(f, "hello world")
        assert result == "hello"
        assert len(result) == 5

    def test_textfield_none_returns_none(self):
        assert _parse_field_value(models.TextField(), None) is None

    def test_urlfield_valid_url_returned(self):
        f = models.URLField()
        assert _parse_field_value(f, "https://example.com") == "https://example.com"

    def test_booleanfield_ja_true(self):
        assert _parse_field_value(models.BooleanField(), "ja") is True

    def test_booleanfield_nee_false(self):
        assert _parse_field_value(models.BooleanField(), "nee") is False

    def test_decimalfield_valid_string(self):
        f = models.DecimalField(max_digits=10, decimal_places=2)
        assert _parse_field_value(f, "25.50") == Decimal("25.50")

    def test_decimalfield_integer_input(self):
        f = models.DecimalField(max_digits=10, decimal_places=2)
        assert _parse_field_value(f, 10) == Decimal("10")

    def test_decimalfield_invalid_returns_none(self, caplog):
        f = models.DecimalField(max_digits=10, decimal_places=2)
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        assert _parse_field_value(f, "not-a-decimal") is None

    def test_integerfield_valid_string(self):
        assert _parse_field_value(models.IntegerField(), "42") == 42

    def test_integerfield_invalid_returns_none(self, caplog):
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        assert _parse_field_value(models.IntegerField(), "abc") is None

    def test_floatfield_valid(self):
        assert _parse_field_value(models.FloatField(), "3.14") == pytest.approx(3.14)

    def test_floatfield_invalid_returns_none(self, caplog):
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        assert _parse_field_value(models.FloatField(), "xyz") is None

    def test_datetimefield_negative_year_repaired(self):
        result = _parse_field_value(models.DateTimeField(), "-2024-06-01T00:00:00Z")
        assert result is not None
        assert result.year == 2024

    def test_datetimefield_year_zero_mapped_to_1970(self):
        result = _parse_field_value(models.DateTimeField(), "0000-12-25T10:00:00Z")
        assert result is not None
        assert result.year == 1970

    def test_datetimefield_unparseable_returns_none(self, caplog):
        caplog.set_level(logging.DEBUG, logger=viernulvier.logger.name)
        assert _parse_field_value(models.DateTimeField(), "definitely-not-a-date") is None

    def test_datefield_valid_string(self):
        result = _parse_field_value(models.DateField(), "2024-07-04")
        assert result is not None
        assert result.year == 2024
        assert result.month == 7
        assert result.day == 4

    def test_jsonfield_passthrough(self):
        assert _parse_field_value(models.JSONField(), {"key": "val"}) == {"key": "val"}

    def test_none_passthrough(self):
        assert _parse_field_value(models.IntegerField(), None) is None


def test_parse_field_value_datetime_negative_year():
    field = models.DateTimeField()
    result = viernulvier._parse_field_value(field, "-2024-01-01T12:00:00Z")
    assert result is not None
    assert result.year == 2024


def test_parse_field_value_datetime_year_zero():
    field = models.DateTimeField()
    result = viernulvier._parse_field_value(field, "0000-12-25T23:59:59Z")
    assert result is not None
    assert result.year == 1970
    assert result.month == 12


def test_parse_field_value_datefield_string():
    field = models.DateField()
    result = viernulvier._parse_field_value(field, "2024-06-15")
    assert result is not None
    assert result.year == 2024
    assert result.month == 6
    assert result.day == 15


def test_parse_field_value_none_returns_none():
    field = models.DateTimeField()
    assert viernulvier._parse_field_value(field, None) is None


# ---------------------------------------------------------------------------
# Value normalization
# ---------------------------------------------------------------------------


class TestNormalizeUrl:
    @pytest.mark.parametrize("value", ["", "0", "none", "null", "undefined", "-", "n/a", "nvt", None])
    def test_empty_like_values_return_empty_string(self, value):
        assert normalize_url(value) == ""

    def test_valid_https_url_returned(self):
        assert normalize_url("https://example.com/path") == "https://example.com/path"

    def test_invalid_url_returns_empty(self):
        assert normalize_url("not-a-url") == ""

    def test_whitespace_stripped_before_validation(self):
        assert normalize_url("  https://example.com  ") == "https://example.com"

    def test_case_insensitive_empty_checks(self):
        assert normalize_url("NONE") == ""
        assert normalize_url("NULL") == ""
        assert normalize_url("N/A") == ""


class TestCleanString:
    def test_strips_surrounding_whitespace(self):
        assert clean_string("  hello  ") == "hello"

    def test_removes_null_byte(self):
        result = clean_string("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result

    def test_keeps_tab_newline_cr(self):
        # Use CR in the middle - str.strip() inside clean_string would eat a trailing \r
        result = clean_string("a\tb\rc\nd")
        assert "\t" in result
        assert "\r" in result
        assert "\n" in result

    def test_removes_other_control_chars(self):
        assert clean_string("a\x01\x08\x0b\x0c\x0e\x1fb") == "ab"

    def test_none_returns_empty_string(self):
        assert clean_string(None) == ""

    def test_preserves_unicode(self):
        assert clean_string("Café 🎭") == "Café 🎭"


class TestCleanVendorId:
    def test_none_returns_none(self):
        assert clean_vendor_id(None) is None

    def test_empty_string_returns_none(self):
        assert clean_vendor_id("") is None

    def test_whitespace_only_returns_none(self):
        assert clean_vendor_id("   ") is None

    def test_html_like_value_returns_none(self):
        assert clean_vendor_id("<i class='icon'>vendor</i>") is None

    def test_valid_string_returned_stripped(self):
        assert clean_vendor_id("  ABC123  ") == "ABC123"

    def test_valid_string_no_stripping_needed(self):
        assert clean_vendor_id("V42") == "V42"


class TestNormalizePerformerType:
    def test_person_maps_to_solo(self):
        assert normalize_performer_type("person") == "solo"

    def test_group_passed_through_lowercase(self):
        assert normalize_performer_type("GROUP") == "group"

    def test_none_returns_empty_string(self):
        assert normalize_performer_type(None) == ""

    def test_unknown_value_lowercased(self):
        assert normalize_performer_type("DUO") == "duo"


# ---------------------------------------------------------------------------
# _extract_external_id_from_url
# ---------------------------------------------------------------------------


def test_extract_external_id_handles_int():
    assert viernulvier._extract_external_id_from_url(42) == "42"
    assert viernulvier._extract_external_id_from_url(123) == "123"


def test_extract_external_id_handles_dict_at_id():
    assert viernulvier._extract_external_id_from_url({"@id": "/api/v1/x"}) == "/api/v1/x"


def test_extract_external_id_handles_dict_external_id_fallback():
    assert viernulvier._extract_external_id_from_url({"external_id": "test123"}) == "test123"


def test_extract_external_id_handles_dict_id_fallback():
    assert viernulvier._extract_external_id_from_url({"id": "test456"}) == "test456"


def test_extract_external_id_handles_blank_string():
    assert viernulvier._extract_external_id_from_url("   ") is None


def test_extract_external_id_handles_none():
    assert viernulvier._extract_external_id_from_url(None) is None


def test_extract_external_id_handles_empty_dict():
    assert viernulvier._extract_external_id_from_url({}) is None


def test_extract_external_id_handles_list():
    assert viernulvier._extract_external_id_from_url([]) is None


def test_extract_external_id_handles_dict_all_none_values():
    assert viernulvier._extract_external_id_from_url({"foo": "bar"}) is None


def test_extract_external_id_non_string_non_int_non_dict_returns_none():
    assert viernulvier._extract_external_id_from_url(3.14) is None


# ---------------------------------------------------------------------------
# _extract_lookup_value
# ---------------------------------------------------------------------------


def test_extract_lookup_value_uses_api_id_key():
    config = ModelSyncConfig(api_id_key="@id")
    assert viernulvier._extract_lookup_value({"@id": "val"}, config) == "val"


def test_extract_lookup_value_falls_back_to_external_id():
    config = ModelSyncConfig(api_id_key="@id")
    assert viernulvier._extract_lookup_value({"external_id": "ext123"}, config) == "ext123"


def test_extract_lookup_value_falls_back_to_id():
    config = ModelSyncConfig(api_id_key="@id")
    assert viernulvier._extract_lookup_value({"id": "test123"}, config) == "test123"


def test_extract_lookup_value_unwraps_nested_dict():
    config = ModelSyncConfig(api_id_key="@id")
    assert viernulvier._extract_lookup_value({"external_id": {"id": "x-1"}}, config) == "x-1"
    assert viernulvier._extract_lookup_value({"@id": {"@id": "nested123"}}, config) == "nested123"


def test_extract_lookup_value_strips_whitespace():
    config = ModelSyncConfig(api_id_key="@id")
    assert viernulvier._extract_lookup_value({"@id": "  value  "}, config) == "value"


def test_extract_lookup_value_returns_none_on_missing():
    config = ModelSyncConfig(api_id_key="@id")
    assert viernulvier._extract_lookup_value({}, config) is None


# ---------------------------------------------------------------------------
# _resolve_fk
# ---------------------------------------------------------------------------


def test_resolve_fk_returns_pk_on_cache_hit():
    """Cache hit returns the PK directly without hitting the DB."""

    class FakeRelatedModel:
        __name__ = "FakeRelated"

        class DoesNotExist(Exception):
            pass

    field = SimpleNamespace(remote_field=SimpleNamespace(model=FakeRelatedModel))
    fk_cache = FKCache()
    fk_cache.set(FakeRelatedModel, "rel-1", 77)

    assert viernulvier._resolve_fk(field, "rel-1", fk_cache) == 77


def test_resolve_fk_returns_none_for_none_input():
    field = SimpleNamespace(remote_field=SimpleNamespace(model=object))
    fk_cache = FKCache()
    assert viernulvier._resolve_fk(field, None, fk_cache) is None


def test_resolve_fk_warns_on_missing_related(caplog):
    """Missing FK logs a warning and returns None."""

    class FakeDoesNotExist(Exception):
        pass

    class FakeValuesList:
        def get(self, external_id=None, **_):
            raise FakeRelatedModel.DoesNotExist()

    class FakeRelatedModel:
        __name__ = "FakeRelated"
        DoesNotExist = FakeDoesNotExist

        class objects:
            @staticmethod
            def values_list(*_args, **_kwargs):
                return FakeValuesList()

    field = SimpleNamespace(remote_field=SimpleNamespace(model=FakeRelatedModel))
    fk_cache = FKCache()
    fk_cache._loaded[FakeRelatedModel] = True

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    result = viernulvier._resolve_fk(field, "missing", fk_cache)

    assert result is None
    assert any("FK not found" in r.message for r in caplog.records)


def test_resolve_fk_logs_error_on_unexpected_exception(caplog):
    """Unexpected exceptions are logged as errors and None is returned."""

    class FakeValuesList:
        def get(self, **_):
            raise RuntimeError("boom")

    class FakeRelatedModel:
        __name__ = "FakeRelated"

        class DoesNotExist(Exception):
            pass

        class objects:
            @staticmethod
            def values_list(*_args, **_kwargs):
                return FakeValuesList()

    field = SimpleNamespace(remote_field=SimpleNamespace(model=FakeRelatedModel))
    fk_cache = FKCache()
    fk_cache._loaded[FakeRelatedModel] = True

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = viernulvier._resolve_fk(field, "error", fk_cache)

    assert result is None
    assert any("Error resolving FK" in r.message for r in caplog.records)


def test_resolve_fk_db_hit_populates_cache():
    """Successful DB lookup on cache miss stores the result in the cache."""

    class FakeValuesList:
        def get(self, external_id=None, **_):
            return 42

    class FakeRelatedModel:
        __name__ = "FakeRelated"

        class DoesNotExist(Exception):
            pass

        class objects:
            @staticmethod
            def values_list(*_args, **_kwargs):
                return FakeValuesList()

    field = SimpleNamespace(remote_field=SimpleNamespace(model=FakeRelatedModel))
    fk_cache = FKCache()
    fk_cache._loaded[FakeRelatedModel] = True

    result = viernulvier._resolve_fk(field, "ext-42", fk_cache)
    assert result == 42
    # Second call hits cache
    assert fk_cache.get(FakeRelatedModel, "ext-42") == 42


# ---------------------------------------------------------------------------
# FKCache
# ---------------------------------------------------------------------------


class TestFKCache:
    def _make_queryable(self, rows):
        class QS:
            def iterator(self):
                return iter(rows)

        class M:
            __name__ = "M"

            class objects:
                @staticmethod
                def values_list(*a, **k):
                    return QS()

        return M

    def test_warmup_populates_cache(self):
        M = self._make_queryable([("ext-1", 1), ("ext-2", 2)])
        cache = FKCache()
        cache.warmup(M)
        assert cache._loaded[M] is True
        assert cache.get(M, "ext-1") == 1
        assert cache.get(M, "ext-2") == 2

    def test_warmup_skipped_on_second_call(self):
        call_count = [0]

        class QS:
            def iterator(self):
                call_count[0] += 1
                return iter([])

        class M:
            __name__ = "M"

            class objects:
                @staticmethod
                def values_list(*a, **k):
                    return QS()

        cache = FKCache()
        cache.warmup(M)
        cache.warmup(M)
        assert call_count[0] == 1

    def test_warmup_failure_marks_loaded_false(self, caplog):
        class QS:
            def iterator(self):
                raise Exception("no external_id")

        class M:
            __name__ = "NoExtId"

            class objects:
                @staticmethod
                def values_list(*a, **k):
                    return QS()

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        cache = FKCache()
        cache.warmup(M)
        assert cache._loaded[M] is False

    def test_warmup_failure_not_retried(self):
        call_count = [0]

        class QS:
            def iterator(self):
                call_count[0] += 1
                raise Exception("boom")

        class M:
            __name__ = "Bad"

            class objects:
                @staticmethod
                def values_list(*a, **k):
                    return QS()

        cache = FKCache()
        cache.warmup(M)
        cache.warmup(M)
        assert call_count[0] == 1

    def test_set_then_get_returns_value(self):
        cache = FKCache()

        class M:
            __name__ = "M"

        cache._loaded[M] = True
        cache.set(M, "ext-99", 99)
        assert cache.get(M, "ext-99") == 99

    def test_get_returns_none_on_miss(self):
        cache = FKCache()

        class M:
            __name__ = "M"

        cache._loaded[M] = True
        assert cache.get(M, "nonexistent") is None


# ---------------------------------------------------------------------------
# _build_defaults
# ---------------------------------------------------------------------------


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_explicit_mapping_pk_skip_fk_and_transform():
    """Explicit field_map: missing values, unknown field, PK skip, FK resolver, transform."""

    class DefaultsModel(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        title = models.CharField(max_length=255, null=True)
        parent = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(DefaultsModel)
    try:
        config = ModelSyncConfig(
            field_map={
                "missing_key": "title",
                "unknown_model_field": "does_not_exist",
                "pk_field": "id",
                "dict_translation": "title",
                "fk_custom": "parent",
                "title_field": "title",
            },
            value_transforms={"title": lambda v: str(v).upper()},
            fk_resolvers={"parent": lambda raw: 99 if raw else None},
            lookup_field="id",
        )

        item = {
            "pk_field": "item-1",
            "dict_translation": {"nl": "Titel"},
            "fk_custom": "/api/v1/parents/99",
            "title_field": "hello",
        }
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(DefaultsModel, item, config, fk_cache)

        assert defaults["parent_id"] == 99
        assert defaults["title"] == "HELLO"
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DefaultsModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_uses_auto_fk_resolver(monkeypatch):
    """Without a custom fk_resolver, the default _resolve_fk branch is used."""

    class AutoFkModel(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        parent = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(AutoFkModel)
    try:
        monkeypatch.setattr(viernulvier, "_resolve_fk", lambda _field, _raw, _cache: 123)

        config = ModelSyncConfig(field_map={"fk_auto": "parent"}, lookup_field="id")
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(
            AutoFkModel,
            {"fk_auto": "/api/v1/parents/123"},
            config,
            fk_cache,
        )

        assert defaults["parent_id"] == 123
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(AutoFkModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_auto_mapping_skips_at_keys_and_none():
    """Auto-mapping skips @ keys, None values, and maps scalar fields."""

    class AutoMapModel(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        title = models.CharField(max_length=255, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(AutoMapModel)
    try:
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(
            AutoMapModel,
            {"@id": "x", "title": "mapped", "unused": None},
            ModelSyncConfig(lookup_field="id"),
            fk_cache,
        )

        assert defaults == {"title": "mapped"}
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(AutoMapModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_skips_none_field_map_value():
    """field_map entry with None value explicitly skips that API key."""

    class TestModel(models.Model):
        name = models.CharField(max_length=100)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(TestModel)
    try:
        config = ModelSyncConfig(
            field_map={"api_name": None},
            lookup_field="external_id",
        )
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(TestModel, {"api_name": "should_be_ignored"}, config, fk_cache)
        assert "name" not in defaults
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(TestModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_auto_maps_camel_case():
    """Auto-mapping converts camelCase API keys to snake_case field names."""

    class CamelModel(models.Model):
        my_field = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(CamelModel)
    try:
        defaults = _build_defaults(
            CamelModel,
            {"myField": "hello"},
            ModelSyncConfig(),
            FKCache(),
        )
        assert defaults.get("my_field") == "hello"
    finally:
        with connection.schema_editor() as se:
            se.delete_model(CamelModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_auto_map_skips_list_values():
    """Auto-mapping skips list values (they are handled via M2M configs)."""

    class LModel(models.Model):
        title = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(LModel)
    try:
        defaults = _build_defaults(
            LModel,
            {"title": "ok", "genres": ["url1", "url2"]},
            ModelSyncConfig(),
            FKCache(),
        )
        assert "title" in defaults
        assert "genres" not in defaults
    finally:
        with connection.schema_editor() as se:
            se.delete_model(LModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_explicit_map_dict_value_for_non_relation_skipped():
    """A flat-dict value for a non-relation field in field_map is skipped (it's a translation)."""

    class TModel(models.Model):
        title = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(TModel)
    try:
        config = ModelSyncConfig(field_map={"title_dict": "title"})
        defaults = _build_defaults(
            TModel,
            {"title_dict": {"nl": "Titel", "en": "Title"}},
            config,
            FKCache(),
        )
        assert "title" not in defaults
    finally:
        with connection.schema_editor() as se:
            se.delete_model(TModel)


# ---------------------------------------------------------------------------
# _sync_all_translations
# ---------------------------------------------------------------------------


def _fake_trans_model(call_log):
    class FakeMeta:
        def get_field(self, name):
            f = models.CharField(name=name, max_length=255)
            return f

    class FakeManager:
        def update_or_create(self, **kwargs):
            call_log.append(kwargs)
            return (Mock(), True)

    class FakeTrans:
        __name__ = "FakeTrans"
        _meta = FakeMeta()
        objects = FakeManager()

    return FakeTrans


class TestSyncAllTranslations:
    def test_multiple_configs_same_model_batched_per_language(self):
        """Two TranslationConfigs for the same model -> ONE update_or_create per language."""
        calls = []
        FT = _fake_trans_model(calls)

        configs = [
            TranslationConfig("title", FT, "parent", "title"),
            TranslationConfig("description", FT, "parent", "description"),
        ]
        _sync_all_translations(
            SimpleNamespace(pk=1),
            {
                "title": {"nl": "Titel", "en": "Title"},
                "description": {"nl": "Beschrijving", "en": "Description"},
            },
            configs,
        )
        assert len(calls) == 2
        langs = {c["language_id"] for c in calls}
        assert langs == {"nl", "en"}
        nl_call = next(c for c in calls if c["language_id"] == "nl")
        assert nl_call["defaults"]["title"] == "Titel"
        assert nl_call["defaults"]["description"] == "Beschrijving"

    def test_empty_language_code_skipped(self):
        """Empty string language codes are silently skipped."""
        calls = []
        FT = _fake_trans_model(calls)
        cfg = TranslationConfig("title", FT, "parent", "title")
        _sync_all_translations(
            SimpleNamespace(pk=1),
            {"title": {"": "no-lang", "nl": "Hallo"}},
            [cfg],
        )
        assert len(calls) == 1
        assert calls[0]["language_id"] == "nl"

    def test_returns_for_non_dict_payload(self):
        """Early exit when translation payload is not a dict."""

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
        )
        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": "not-dict"}, [cfg])

    def test_returns_on_empty_config_list(self):
        """Empty translation_configs list causes immediate return."""
        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "X"}}, [])

    def test_logs_warning_on_missing_field(self, caplog):
        """Warning is logged when a configured flat_field does not exist on the model."""

        class FakeMeta:
            def get_field(self, _name):
                raise FieldDoesNotExist("missing")

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "Hallo"}}, [cfg])
        assert any("Translation field" in r.message for r in caplog.records)

    def test_logs_error_on_update_or_create_failure(self, caplog):
        """update_or_create exceptions are caught and logged as errors."""

        class FakeMeta:
            def get_field(self, _name):
                f = models.CharField(name="title", max_length=255)
                return f

        class FakeManager:
            def update_or_create(self, **_kwargs):
                raise RuntimeError("write failed")

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()
            objects = FakeManager()

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
        )

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "Hallo"}}, [cfg])
        assert any("Error syncing" in r.message for r in caplog.records)

    def test_skips_none_language_values(self):
        """Languages with None values are skipped; non-None values are processed."""
        called_with_langs = []

        class FakeMeta:
            def get_field(self, _name):
                return models.CharField(name="title", max_length=255)

        class FakeManager:
            def update_or_create(self, **kwargs):
                called_with_langs.append(kwargs.get("language_id"))
                return (Mock(), True)

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()
            objects = FakeManager()

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
        )

        viernulvier._sync_all_translations(
            SimpleNamespace(pk=1),
            {"title": {"nl": "Hallo", "fr": "Bonjour", "de": None}},
            [cfg],
        )

        assert "nl" in called_with_langs
        assert "fr" in called_with_langs
        assert "de" not in called_with_langs

    def test_applies_value_transform(self):
        """value_transforms are applied before persisting translated values."""
        calls = []
        FT = _fake_trans_model(calls)
        cfg = TranslationConfig(
            "title",
            FT,
            "parent",
            "title",
            value_transforms={"title": str.upper},
        )
        _sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "hallo"}}, [cfg])
        assert calls[0]["defaults"]["title"] == "HALLO"

    def test_transform_returning_none_omits_field_no_call(self):
        """If the only field has transform -> None, update_or_create is never called."""

        class FakeMeta:
            def get_field(self, _name):
                return models.CharField(name="title", max_length=255)

        mock_manager = Mock()

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()
            objects = mock_manager

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
            value_transforms={"title": lambda v: None},
        )

        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "hallo"}}, [cfg])

        mock_manager.update_or_create.assert_not_called()


# ---------------------------------------------------------------------------
# _sync_m2m
# ---------------------------------------------------------------------------


def _make_m2m_setup():
    created_rows = []

    class FakeRelated:
        __name__ = "FakeRelated"
        DoesNotExist = Exception

        def __init__(self, pk=None):
            self.pk = pk

    class FakeThrough:
        __name__ = "FakeThrough"

        def __init__(self, **kwargs):
            created_rows.append(dict(kwargs))

        class objects:
            @staticmethod
            def filter(**_):
                return SimpleNamespace(delete=lambda: None)

    return FakeRelated, FakeThrough, created_rows


class TestSyncM2M:
    def test_returns_early_when_payload_is_not_list(self):
        """_sync_m2m does nothing if the API value for the key is not a list."""
        through_model = Mock()
        cfg = M2MConfig(
            api_key="genres",
            related_model=Mock(),
            through_model=through_model,
            parent_fk="parent",
            related_fk="related",
        )
        fk_cache = FKCache()
        viernulvier._sync_m2m(SimpleNamespace(pk=1), {"genres": "not-a-list"}, cfg, fk_cache)
        through_model.objects.filter.assert_not_called()

    def test_warns_when_related_object_not_found(self, caplog):
        """A missing related object is skipped with a warning."""

        class FakeDoesNotExist(Exception):
            pass

        class FakeRelatedModel:
            __name__ = "FakeRelated"
            DoesNotExist = FakeDoesNotExist

            class objects:
                @staticmethod
                def get(**_kwargs):
                    raise FakeRelatedModel.DoesNotExist()

        class FakeThroughModel:
            __name__ = "FakeThroughModel"

            class objects:
                @staticmethod
                def filter(**_kw):
                    return SimpleNamespace(delete=lambda: None)

        cfg = M2MConfig(
            api_key="items",
            related_model=FakeRelatedModel,
            through_model=FakeThroughModel,
            parent_fk="parent",
            related_fk="related",
        )
        fk_cache = FKCache()
        fk_cache._loaded[FakeRelatedModel] = True

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        viernulvier._sync_m2m(SimpleNamespace(pk=1), {"items": ["ext-missing"]}, cfg, fk_cache)
        assert any("not found" in r.message for r in caplog.records)

    def test_logs_error_on_bulk_create_fallback_failure(self, caplog):
        """When bulk_create fails and individual save also fails, an error is logged."""

        class FakeRelatedModel:
            __name__ = "FakeRelated"

            class DoesNotExist(Exception):
                pass

            def __init__(self, **kwargs):
                self._kwargs = kwargs
                self.pk = kwargs.get("pk", 1)

        created_objs = []

        class FakeThroughModel:
            __name__ = "FakeThroughModel"

            def __init__(self, **kwargs):
                self._kwargs = kwargs
                created_objs.append(self)

            def save(self):
                raise RuntimeError("save failed")

            class objects:
                @staticmethod
                def filter(**_kw):
                    return SimpleNamespace(delete=lambda: None)

        cfg = M2MConfig(
            api_key="items",
            related_model=FakeRelatedModel,
            through_model=FakeThroughModel,
            parent_fk="parent",
            related_fk="related",
        )
        fk_cache = FKCache()
        fk_cache._loaded[FakeRelatedModel] = True
        fk_cache.set(FakeRelatedModel, "ext-1", 1)

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        viernulvier._sync_m2m(SimpleNamespace(pk=1), {"items": ["ext-1"]}, cfg, fk_cache)
        assert any("Error creating" in r.message for r in caplog.records)

    def test_extra_fields_from_dict_item_applied(self):
        """position field in dict item is stored in the through row."""
        FR, FT, rows = _make_m2m_setup()
        cache = FKCache()
        cache._loaded[FR] = True
        cache.set(FR, "ext-1", 1)

        cfg = M2MConfig(
            api_key="genres",
            related_model=FR,
            through_model=FT,
            parent_fk="production",
            related_fk="genre",
            extra_fields={"position": "position"},
        )
        _sync_m2m(
            SimpleNamespace(pk=10),
            {"genres": [{"@id": "ext-1", "position": 7}]},
            cfg,
            cache,
        )
        assert rows[0]["position"] == 7

    def test_position_auto_filled_from_index_for_url_strings(self):
        """When raw item is a plain string, position is the list index."""
        FR, FT, rows = _make_m2m_setup()
        cache = FKCache()
        cache._loaded[FR] = True
        cache.set(FR, "ext-A", 10)
        cache.set(FR, "ext-B", 20)

        cfg = M2MConfig(
            api_key="genres",
            related_model=FR,
            through_model=FT,
            parent_fk="production",
            related_fk="genre",
            extra_fields={"position": "position"},
        )
        _sync_m2m(
            SimpleNamespace(pk=10),
            {"genres": ["ext-A", "ext-B"]},
            cfg,
            cache,
        )
        assert rows[0]["position"] == 0
        assert rows[1]["position"] == 1

    def test_empty_ext_id_items_skipped(self):
        """None / empty string / empty dict items are skipped."""
        bulk_called = [False]
        FR, _, _ = _make_m2m_setup()

        class FT:
            __name__ = "FT"

            class objects:
                @staticmethod
                def filter(**_):
                    return SimpleNamespace(delete=lambda: None)

        cache = FKCache()
        cache._loaded[FR] = True

        cfg = M2MConfig(
            api_key="items",
            related_model=FR,
            through_model=FT,
            parent_fk="prod",
            related_fk="rel",
        )
        _sync_m2m(
            SimpleNamespace(pk=1),
            {"items": [None, "", {}]},
            cfg,
            cache,
        )
        assert not bulk_called[0]

    def test_cache_miss_triggers_db_lookup(self):
        """Cache miss falls back to DB and populates cache on success."""

        class FR:
            __name__ = "FR"
            DoesNotExist = Exception

            def __init__(self, pk=None):
                self.pk = pk

            class objects:
                @staticmethod
                def get(**kwargs):
                    return SimpleNamespace(pk=99)

        created_rows = []

        class FT:
            __name__ = "FT"

            def __init__(self, **kw):
                created_rows.append(kw)

            class objects:
                @staticmethod
                def filter(**_):
                    return SimpleNamespace(delete=lambda: None)

        cache = FKCache()
        cache._loaded[FR] = True

        cfg = M2MConfig(
            api_key="items",
            related_model=FR,
            through_model=FT,
            parent_fk="prod",
            related_fk="rel",
        )
        _sync_m2m(SimpleNamespace(pk=1), {"items": ["ext-miss"]}, cfg, cache)
        assert created_rows


def test_build_session_mounts_https_and_http_adapters(monkeypatch):
    """_build_session attaches HTTPAdapter to both https:// and http://."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    from apps.imports.scrapers.viernulvier import _build_session

    session = _build_session()
    assert any(p == "https://" for p in session.adapters)
    assert any(p == "http://" for p in session.adapters)
    assert session.headers.get("X-AUTH-TOKEN") == "test-key"


def test_fetch_retries_exhausted_fallthrough(monkeypatch):
    """Setting MAX_RETRIES=-1 empties the retry loop, hitting the unreachable raise."""
    monkeypatch.setattr(viernulvier, "MAX_RETRIES", -1)
    monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)

    with pytest.raises(viernulvier.ScraperError, match="Retries exhausted"):
        viernulvier._fetch_with_retry(Mock(), "https://example.com/test")


def test_fetch_raises_immediately_on_non_retryable_http_error(monkeypatch):
    """A 404 (not in RETRY_STATUS_CODES) raises ScraperError immediately without retrying."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    call_count = [0]

    def responses(url, n):
        call_count[0] = n
        r = _make_status_response(404, {})
        r.ok = False
        return r

    _mock_session(monkeypatch, responses)

    with pytest.raises(viernulvier.ScraperError, match="API error: 404"):
        viernulvier.fetch_viernulvier(endpoint="/events")

    assert call_count[0] == 1  # no retries


def test_concurrent_page_etag_stored_in_cache(monkeypatch):
    """ETag returned by a concurrent extra page is stored in etag_cache."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def responses(url, n):
        if "page=2" in url:
            return _make_ok_response({"member": [{"@id": "2"}]}, etag="page-2-etag")
        return _make_ok_response(
            {
                "@context": "ctx",
                "member": [{"@id": "1"}],
                "totalItems": 2,
                "view": {"last": "https://www.viernulvier.gent/api/v1/events?page=2"},
            }
        )

    _mock_session(monkeypatch, responses)
    etag_cache = {}
    viernulvier.fetch_viernulvier(endpoint="/events", etag_cache=etag_cache)
    assert "page-2-etag" in etag_cache.values()


def test_sequential_page_etag_stored_in_cache(monkeypatch):
    """ETag returned by a sequential next-page is stored in etag_cache."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    call_count = [0]

    def responses(url, n):
        call_count[0] = n
        if n == 1:
            return _make_ok_response(
                {
                    "@context": "ctx",
                    "member": [{"@id": "1"}],
                    "view": {"next": "https://www.viernulvier.gent/api/v1/events?page=2"},
                }
            )
        return _make_ok_response({"member": [{"@id": "2"}]}, etag="seq-page-2-etag")

    _mock_session(monkeypatch, responses)
    etag_cache = {}
    viernulvier.fetch_viernulvier(endpoint="/events", etag_cache=etag_cache)
    assert "seq-page-2-etag" in etag_cache.values()


def test_parse_field_value_urlfield_branch(monkeypatch):
    """URLField branch is reachable only by bypassing the CharField check,
    since URLField inherits CharField and would otherwise be caught first."""
    import builtins

    url_field = models.URLField()
    url_field.name = "url"

    original_isinstance = builtins.isinstance

    def patched_isinstance(obj, classes):
        if obj is url_field and classes == (models.TextField, models.CharField):
            return False
        return original_isinstance(obj, classes)

    monkeypatch.setattr(builtins, "isinstance", patched_isinstance)

    assert viernulvier._parse_field_value(url_field, "https://example.com") == "https://example.com"
    assert viernulvier._parse_field_value(url_field, "not-a-url") == ""


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_skips_field_map_key_missing_from_item():
    """When a field_map key is not present in the API item, it is silently skipped."""

    class MissingKeyModel(models.Model):
        title = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(MissingKeyModel)
    try:
        config = ModelSyncConfig(field_map={"absent_key": "title"}, lookup_field="id")
        defaults = _build_defaults(MissingKeyModel, {}, config, FKCache())
        assert "title" not in defaults
    finally:
        with connection.schema_editor() as se:
            se.delete_model(MissingKeyModel)


def test_sync_all_translations_skips_empty_string_for_non_blank_field():
    """Empty string raw value is skipped when the model field has blank=False."""

    class FakeMeta:
        def get_field(self, _name):
            f = models.CharField(name="title", max_length=255)
            f.blank = False
            return f

    mock_manager = Mock()
    mock_manager.update_or_create.return_value = (Mock(), True)

    class FakeTranslationModel:
        __name__ = "FakeTranslationModel"
        _meta = FakeMeta()
        objects = mock_manager

    cfg = TranslationConfig(
        api_key="title",
        model=FakeTranslationModel,
        parent_fk="parent",
        flat_field="title",
    )
    viernulvier._sync_all_translations(
        SimpleNamespace(pk=1),
        {"title": {"nl": "", "fr": "Bonjour"}},
        [cfg],
    )

    # update_or_create called once (for "fr"); "nl" skipped because blank=False + empty
    assert mock_manager.update_or_create.call_count == 1
    call_kwargs = mock_manager.update_or_create.call_args[1]
    assert call_kwargs["language_id"] == "fr"


def test_sync_all_translations_skips_non_dict_raw_dict_for_individual_config():
    """If one config's api_key maps to a non-dict, that config is skipped per language."""
    calls = []

    class FakeMeta:
        def get_field(self, name):
            return models.CharField(name=name, max_length=255)

    class FakeManager:
        def update_or_create(self, **kwargs):
            calls.append(kwargs)
            return (Mock(), True)

    class FakeTranslationModel:
        __name__ = "FakeTranslationModel"
        _meta = FakeMeta()
        objects = FakeManager()

    configs = [
        TranslationConfig("title", FakeTranslationModel, "parent", "title"),
        TranslationConfig("subtitle", FakeTranslationModel, "parent", "subtitle"),
    ]
    viernulvier._sync_all_translations(
        SimpleNamespace(pk=1),
        {"title": {"nl": "Hallo"}, "subtitle": "plain-string"},
        configs,
    )
    assert len(calls) == 1
    assert "title" in calls[0]["defaults"]
    assert "subtitle" not in calls[0]["defaults"]


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_caches_external_id_after_create(monkeypatch):
    """After update_or_create, the object's external_id is stored in fk_cache."""

    class CachedModel(models.Model):
        external_id = models.CharField(max_length=255, unique=True)
        title = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(CachedModel)
    try:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint=None, params=None, etag_cache=None: [{"@id": "ext-001", "title": "Cached Item"}],
        )

        captured_cache = {}

        original_set = FKCache.set

        def spy_set(self, model, ext_id, pk):
            captured_cache[ext_id] = pk
            original_set(self, model, ext_id, pk)

        monkeypatch.setattr(FKCache, "set", spy_set)

        config = ModelSyncConfig(lookup_field="external_id")
        count = viernulvier.sync_viernulvier(CachedModel, config, endpoint="/test")

        assert count == 1
        assert "ext-001" in captured_cache
    finally:
        with connection.schema_editor() as se:
            se.delete_model(CachedModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_logs_warning_for_nonexistent_field(caplog):
    """FieldDoesNotExist in field_map logs a warning and skips that entry."""

    class SimpleModel(models.Model):
        title = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(SimpleModel)
    try:
        config = ModelSyncConfig(
            field_map={
                "api_title": "title",
                "api_ghost": "does_not_exist_on_model",
            },
            lookup_field="id",
        )
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        defaults = _build_defaults(
            SimpleModel,
            {"api_title": "hello", "api_ghost": "ignored"},
            config,
            FKCache(),
        )

        # Valid field is still mapped
        assert defaults.get("title") == "hello"
        # Warning was logged for the missing field
        assert any("does_not_exist_on_model" in r.message and "does not exist" in r.message for r in caplog.records)
    finally:
        with connection.schema_editor() as se:
            se.delete_model(SimpleModel)
