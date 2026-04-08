"""Tests for Viernulvier scraper HTTP behavior and shared test helper fixtures."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import _build_session
from apps.imports.scrapers.viernulvier_http import _collect_page_members
from tests.scrapers.conftest import _mock_build_session


def test_fetch_raises_on_http_error(monkeypatch) -> None:
    """5xx errors after all retries are exhausted raise ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(500, "")] * (viernulvier.MAX_RETRIES + 1))

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_non_json_response(monkeypatch) -> None:
    """A payload that is not a list or dict raises ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(200, "not a dict or list")])

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_when_api_key_missing(monkeypatch) -> None:
    """Missing VIERNULVIER_API_KEY raises ScraperError before any HTTP call."""
    monkeypatch.delenv("VIERNULVIER_API_KEY", raising=False)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_invalid_json(monkeypatch) -> None:
    """A response whose .json() raises ValueError is wrapped in ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(200, ValueError("invalid json"))])

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_timeout(monkeypatch) -> None:
    """Connection timeouts after MAX_RETRIES raise ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(
        monkeypatch,
        raise_exc=requests.Timeout(),
    )

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_generic_request_exception(monkeypatch) -> None:
    """Non-retryable RequestException is immediately wrapped in ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(
        monkeypatch,
        raise_exc=requests.RequestException("connection failed"),
    )

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_none_payload(monkeypatch) -> None:
    """A null JSON payload raises ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(200, None)])

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_absolute_endpoint(monkeypatch) -> None:
    """Absolute URLs passed as endpoint are rejected immediately."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    with pytest.raises(viernulvier.ScraperError, match="endpoint must be a relative path"):
        viernulvier.fetch_viernulvier(endpoint="https://evil.com/events")

    with pytest.raises(viernulvier.ScraperError, match="endpoint must be a relative path"):
        viernulvier.fetch_viernulvier(endpoint="http://example.com/api")


def test_fetch_raises_on_json_ld_error_context(monkeypatch) -> None:
    """JSON-LD error context payload raises ScraperError with status/detail."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    error_payload = {
        "@context": "/api/contexts/Error",
        "status": 403,
        "detail": "Forbidden: access denied",
    }
    _mock_build_session(monkeypatch, [(200, error_payload)])

    with pytest.raises(viernulvier.ScraperError, match=r"status=403.*detail=Forbidden: access denied"):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_allows_different_endpoint_paths(monkeypatch) -> None:
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


def test_fetch_dict_without_context_or_member_returns_empty(monkeypatch) -> None:
    """A dict payload without @context or member key returns an empty list."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    _mock_build_session(monkeypatch, [(200, {"foo": "bar"})])

    result = viernulvier.fetch_viernulvier(endpoint="/events")
    assert result == []


def test_collect_page_members_fallback_returns_empty_list() -> None:
    """Non-dict and non-list page payloads fall back to an empty list."""
    assert _collect_page_members(None) == []


def test_fetch_extracts_member_collection(monkeypatch) -> None:
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


def test_fetch_collects_single_item_dict_with_context(monkeypatch) -> None:
    """A single-item dict with @context but no 'member' key is returned as one-element list."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    single_item = {"@context": "ctx", "@id": "/api/v1/events/1"}
    _mock_build_session(monkeypatch, [(200, single_item)])

    result = viernulvier.fetch_viernulvier(endpoint="/events")

    assert result == [single_item]


def test_build_session_mounts_https_and_http_adapters(monkeypatch) -> None:
    """_build_session attaches HTTPAdapter to both https:// and http://."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    session = _build_session()
    assert any(p == "https://" for p in session.adapters)
    assert any(p == "http://" for p in session.adapters)
    assert session.headers.get("X-AUTH-TOKEN") == "test-key"


@pytest.mark.django_db(transaction=True)
def test_shared_helper_fixtures_are_callable(
    monkeypatch,
    mock_build_session_helper,
    mock_session_helper,
    temp_viernulvier_model,
    fake_trans_model_fixture,
    m2m_setup_fixture,
) -> None:
    """Exercise wrapper fixtures so conftest helper return branches stay covered."""
    mock_build_session_helper([(200, [])])
    assert viernulvier._build_session is not None

    def responses(_url, _n):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = []
        return response

    call_count = mock_session_helper(responses)
    assert call_count == [0]
    session = viernulvier._build_session()
    assert session.get("https://example.com").json() == []

    with temp_viernulvier_model() as model:
        obj = model.objects.create(id="x")
        assert obj.id == "x"

    calls = []
    fake_trans_model = fake_trans_model_fixture(calls)
    fake_trans_model.objects.update_or_create(language_id="nl", defaults={"title": "Hallo"})
    assert calls[0]["language_id"] == "nl"

    related, through, rows = m2m_setup_fixture()
    _ = related(pk=1)
    through(parent_id=1, related_id=2)
    assert rows
    assert rows[0]["parent_id"] == 1
