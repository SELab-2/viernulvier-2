"""
Tests for Viernulvier HTTP retry logic, backoff, and rate limiting.
"""

from __future__ import annotations

import pytest
import requests

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    RETRY_BACKOFF_MAX,
    RateLimitError,
    _backoff_seconds,
    _parse_retry_after,
)
from tests.scrapers.conftest import _make_ok_response, _make_status_response, _mock_session

# ---------------------------------------------------------------------------
# _parse_retry_after
# ---------------------------------------------------------------------------


def test_parse_retry_after_integer_header() -> None:
    from unittest.mock import Mock

    r = Mock()
    r.headers = Mock()
    r.headers.get = Mock(return_value="30")
    assert _parse_retry_after(r) == 30


def test_parse_retry_after_non_integer_returns_none() -> None:
    from unittest.mock import Mock

    r = Mock()
    r.headers = Mock()
    r.headers.get = Mock(return_value="Wed, 21 Oct 2015 07:28:00 GMT")
    assert _parse_retry_after(r) is None


def test_parse_retry_after_missing_returns_none() -> None:
    from unittest.mock import Mock

    r = Mock()
    r.headers = Mock()
    r.headers.get = Mock(return_value=None)
    assert _parse_retry_after(r) is None


def test_fetch_viernulvier_impl_returns_empty_list_when_fetch_returns_none(monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(viernulvier, "_build_session", SimpleNamespace)
    monkeypatch.setattr(viernulvier, "_fetch_with_retry", lambda *_args, **_kwargs: (None, None))

    result = viernulvier.fetch_viernulvier(endpoint="/events")

    assert result == []


# ---------------------------------------------------------------------------
# Rate Limiting (429)
# ---------------------------------------------------------------------------


def test_429_with_numeric_retry_after_uses_header_as_wait(monkeypatch) -> None:
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

    _mock_session(monkeypatch, responses)
    sleep_args = []
    monkeypatch.setattr(viernulvier.time, "sleep", sleep_args.append)

    result = viernulvier.fetch_viernulvier(endpoint="/events")
    assert result == []
    assert 45.0 in sleep_args


def test_429_without_retry_after_uses_backoff(monkeypatch) -> None:
    """HTTP 429 with no Retry-After falls back to exponential backoff."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def responses(url, n):
        if n == 1:
            r = _make_status_response(429, {})
            r.ok = False
            return r
        return _make_ok_response([])

    _mock_session(monkeypatch, responses)
    sleep_args = []
    monkeypatch.setattr(viernulvier.time, "sleep", sleep_args.append)

    result = viernulvier.fetch_viernulvier(endpoint="/events")
    assert result == []
    assert sleep_args
    assert sleep_args[0] != 45.0


def test_429_all_retries_exhausted_raises_rate_limit_error(monkeypatch) -> None:
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


def test_429_without_retry_after_raises_with_none(monkeypatch) -> None:
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


# ---------------------------------------------------------------------------
# RateLimitError
# ---------------------------------------------------------------------------


def test_rate_limit_error_with_retry_after() -> None:
    err = RateLimitError(retry_after=120)
    assert err.retry_after == 120
    assert "120" in str(err)


def test_rate_limit_error_without_retry_after() -> None:
    err = RateLimitError()
    assert err.retry_after is None
    assert "Rate limited" in str(err)


# ---------------------------------------------------------------------------
# _backoff_seconds
# ---------------------------------------------------------------------------


def test_backoff_seconds_capped_at_max() -> None:
    for attempt in range(10):
        val = _backoff_seconds(attempt)
        assert 0 < val <= RETRY_BACKOFF_MAX


def test_backoff_seconds_increases_with_attempt() -> None:
    avg_0 = sum(_backoff_seconds(0) for _ in range(20)) / 20
    avg_3 = sum(_backoff_seconds(3) for _ in range(20)) / 20
    assert avg_3 > avg_0


# ---------------------------------------------------------------------------
# Server Error Retries (5xx)
# ---------------------------------------------------------------------------


def test_5xx_retries_then_succeeds(monkeypatch) -> None:
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


# ---------------------------------------------------------------------------
# Connection Errors
# ---------------------------------------------------------------------------


def test_connection_error_retries_then_succeeds(monkeypatch) -> None:
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


def test_connection_error_all_retries_exhausted(monkeypatch) -> None:
    """ScraperError raised after all ConnectionError retries exhausted."""
    from typing import Never

    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def responses(url, n) -> Never:
        raise requests.ConnectionError("always down")

    _mock_session(monkeypatch, responses)
    with pytest.raises(viernulvier.ScraperError, match="Connection failed"):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_timeout_retries_then_succeeds(monkeypatch) -> None:
    """Timeout on attempt 1, success on attempt 2."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def responses(url, n):
        if n == 1:
            raise requests.Timeout
        return _make_ok_response([])

    _mock_session(monkeypatch, responses)
    result = viernulvier.fetch_viernulvier(endpoint="/events")
    assert result == []


# ---------------------------------------------------------------------------
# ETag Caching (304)
# ---------------------------------------------------------------------------


def test_304_not_modified_returns_empty_and_preserves_etag(monkeypatch) -> None:
    """304 returns empty list; cached ETag is preserved in etag_cache."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def responses(url, n):
        return _make_status_response(304, {})

    _mock_session(monkeypatch, responses)
    etag_cache = {"https://www.viernulvier.gent/api/v1/events": "old-etag"}
    result = viernulvier.fetch_viernulvier(endpoint="/events", etag_cache=etag_cache)
    assert result == []
    assert etag_cache["https://www.viernulvier.gent/api/v1/events"] == "old-etag"


def test_etag_from_response_stored_in_cache(monkeypatch) -> None:
    """ETag header in response is stored in etag_cache."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def responses(url, n):
        return _make_ok_response({"member": []}, etag="new-etag-789")

    _mock_session(monkeypatch, responses)
    etag_cache = {}
    viernulvier.fetch_viernulvier(endpoint="/events", etag_cache=etag_cache)
    assert "new-etag-789" in etag_cache.values()


def test_concurrent_page_etag_stored_in_cache(monkeypatch) -> None:
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


def test_sequential_page_etag_stored_in_cache(monkeypatch) -> None:
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


# ---------------------------------------------------------------------------
# List Payload
# ---------------------------------------------------------------------------


def test_list_payload_returned_directly(monkeypatch) -> None:
    """A plain JSON list (not dict) is returned as-is."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def responses(url, n):
        return _make_ok_response([{"@id": "1"}, {"@id": "2"}])

    _mock_session(monkeypatch, responses)
    result = viernulvier.fetch_viernulvier(endpoint="/events")
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


def test_fetch_retries_exhausted_fallthrough(monkeypatch) -> None:
    """Setting MAX_RETRIES=-1 empties the retry loop, hitting the unreachable raise."""
    from unittest.mock import Mock

    monkeypatch.setattr(viernulvier, "MAX_RETRIES", -1)
    monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)

    with pytest.raises(viernulvier.ScraperError, match="Retries exhausted"):
        viernulvier._fetch_with_retry(Mock(), "https://example.com/test")


def test_fetch_raises_immediately_on_non_retryable_http_error(monkeypatch) -> None:
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
