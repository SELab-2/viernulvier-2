"""Tests for Viernulvier scraper fetch, error handling, and persistence.

Key fixes vs original:
- HTTP mocking: source uses requests.Session internally; tests mock _build_session
  instead of patching requests.get (which is never called directly).
- _sync_translations removed; _sync_all_translations takes a LIST of TranslationConfig
  and calls update_or_create with language_id (not language).
- _build_defaults / _resolve_fk / _sync_m2m all require a FKCache argument.
- _fetch_single_page does not exist; removed tests that depend on it.
- Log messages corrected to match English source strings.
- _sync_m2m uses bulk_create + individual-save fallback, not objects.create.
- dict payload without @context returns [] (not ScraperError).
"""

import datetime
import logging
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock, patch, call

import pytest
import requests
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import IntegrityError
from django.db import connection, models
from django.test.utils import isolate_apps

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    FKCache,
    M2MConfig,
    ModelSyncConfig,
    TranslationConfig,
    _parse_field_value,
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
    # Skip real sleeps in retry loops
    monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)

    return call_index  # callers can inspect how many requests were made


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


# ---------------------------------------------------------------------------
# fetch_viernulvier — HTTP layer
# ---------------------------------------------------------------------------


def test_fetch_raises_on_http_error(monkeypatch):
    """5xx errors after all retries are exhausted raise ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    # Return 500 for every call (covers all MAX_RETRIES attempts)
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

    with pytest.raises(
        viernulvier.ScraperError, match="status=403.*detail=Forbidden: access denied"
    ):
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

    # Source: members = data.get("member", []) → [], @context not in data → all_items = []
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
# fetch_viernulvier — query parameter support
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

    viernulvier.fetch_viernulvier(
        endpoint="/events", params={"created_at[after]": "2024-01-01T00:00:00Z"}
    )

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

    result = viernulvier.fetch_viernulvier(
        endpoint="/events", params={"created_at[after]": "2024-01-01T00:00:00Z"}
    )

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
    viernulvier.fetch_viernulvier(
        endpoint="/events", params={"created_at[after]": iso_timestamp}
    )

    assert captured["params"]["created_at[after]"] == iso_timestamp


# ---------------------------------------------------------------------------
# sync_viernulvier — basic persistence
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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "https://example.com/1", "title": "new"}
            ],
        )

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        # Source: "Missing '@id' in item: ..."
        assert any("Missing '@id' in item:" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_empty_string_id(monkeypatch, caplog):
    """An empty string @id is treated the same as missing."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "", "title": "A"}
            ],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        # Source: "Duplicate item skipped: %s"
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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 1
        obj = ViernulvierItem.objects.get(id="https://example.com/9")
        assert obj.title == "Café 🎭"
        assert obj.description is None


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_handles_large_payload(monkeypatch):
    """50-item batch is fully persisted."""
    with _temp_viernulvier_model() as ViernulvierItem:
        items = [
            {"@id": f"https://example.com/{i}", "title": f"T{i}"} for i in range(50)
        ]
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None, etag_cache=None: items,
        )

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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
                {"title": "no id"},  # will fail
            ],
        )

        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 1
        # Source: "Sync complete: saved=%d, errors=%d%s"
        assert any(
            "Sync complete:" in r.message
            and "saved=1" in r.message
            and "errors=1" in r.message
            for r in caplog.records
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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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
        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events", params=params
        )

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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 1
        assert ViernulvierItem.objects.count() == 1


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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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
        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events", params=params
        )

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
                {"title": "Event B"},  # missing @id → fails
                {"@id": "https://example.com/3", "title": "Event C"},
            ],
        )

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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
            viernulvier.sync_viernulvier(
                ViernulvierItem, _PassThroughConfig(), endpoint="/events"
            )

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

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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

        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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

        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )
        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

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

        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )
        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/venues"
        )

        sources = list(ImportLog.objects.values_list("source", flat=True))
        assert "viernulvier:/events" in sources
        assert "viernulvier:/venues" in sources


# ---------------------------------------------------------------------------
# sync_viernulvier — error branches & savepoints
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
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "1", "title": "A"}
            ],
        )

        def raise_validation(*_args, **_kwargs):
            raise ValidationError({"title": ["invalid"], "__all__": ["bad state"]})

        monkeypatch.setattr(
            ViernulvierItem.objects, "update_or_create", raise_validation
        )

        saved = viernulvier.sync_viernulvier(
            ViernulvierItem, ModelSyncConfig(lookup_field="id"), endpoint="/events"
        )

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
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "1", "title": "A"}
            ],
        )

        def raise_integrity(*_args, **_kwargs):
            raise IntegrityError("db exploded")

        monkeypatch.setattr(
            ViernulvierItem.objects, "update_or_create", raise_integrity
        )

        saved = viernulvier.sync_viernulvier(
            ViernulvierItem, ModelSyncConfig(lookup_field="id"), endpoint="/events"
        )

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
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "1", "title": "A"}
            ],
        )

        def raise_runtime(*_args, **_kwargs):
            raise RuntimeError("unexpected crash")

        monkeypatch.setattr(
            ViernulvierItem.objects, "update_or_create", raise_runtime
        )

        saved = viernulvier.sync_viernulvier(
            ViernulvierItem, ModelSyncConfig(lookup_field="id"), endpoint="/events"
        )

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
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "1", "title": "A", "rels": []}
            ],
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

        saved = viernulvier.sync_viernulvier(
            ViernulvierItem, config, endpoint="/events"
        )

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
            lambda endpoint="/events", params=None, etag_cache=None: [
                {"@id": "1", "title": "A"}
            ],
        )

        called = {"translations": 0}

        def fake_sync_all_translations(*_args, **_kwargs):
            called["translations"] += 1

        # Source calls _sync_all_translations, not _sync_translations
        monkeypatch.setattr(
            viernulvier, "_sync_all_translations", fake_sync_all_translations
        )

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

        saved = viernulvier.sync_viernulvier(
            ViernulvierItem, config, endpoint="/events"
        )

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
        from apps.events.models import EventPrice, Event
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
        from apps.events.models import EventPrice, Event
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
# _parse_field_value
# ---------------------------------------------------------------------------


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
    # dict value with "id" key
    assert viernulvier._extract_lookup_value({"external_id": {"id": "x-1"}}, config) == "x-1"
    # dict value with "@id" key
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
    fk_cache._loaded[FakeRelatedModel] = True  # skip warmup

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
                "missing_key": "title",       # api key absent → skipped
                "unknown_model_field": "does_not_exist",  # model field absent → skipped
                "pk_field": "id",              # PK → skipped
                "dict_translation": "title",   # dict value without relation → skipped
                "fk_custom": "parent",         # FK with custom resolver
                "title_field": "title",        # scalar with transform
            },
            value_transforms={"title": lambda v: str(v).upper()},
            fk_resolvers={"parent": lambda raw: 99 if raw else None},
            lookup_field="id",
        )

        item = {
            "pk_field": "item-1",
            "dict_translation": {"nl": "Titel"},  # dict value for non-FK field → skipped
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
        monkeypatch.setattr(
            viernulvier, "_resolve_fk", lambda _field, _raw, _cache: 123
        )

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
        defaults = viernulvier._build_defaults(
            TestModel, {"api_name": "should_be_ignored"}, config, fk_cache
        )
        assert "name" not in defaults
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(TestModel)


# ---------------------------------------------------------------------------
# _sync_all_translations  (was _sync_translations in old tests)
# ---------------------------------------------------------------------------


def test_sync_all_translations_returns_for_non_dict_payload():
    """Early exit when translation payload is not a dict."""

    class FakeTranslationModel:
        __name__ = "FakeTranslationModel"

    cfg = TranslationConfig(
        api_key="title",
        model=FakeTranslationModel,
        parent_fk="parent",
        flat_field="title",
    )

    # Should not raise; update_or_create never called
    viernulvier._sync_all_translations(
        SimpleNamespace(pk=1), {"title": "not-dict"}, [cfg]
    )


def test_sync_all_translations_returns_on_empty_config_list():
    """Empty translation_configs list causes immediate return."""
    viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "X"}}, [])


def test_sync_all_translations_logs_warning_on_missing_field(caplog):
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
    viernulvier._sync_all_translations(
        SimpleNamespace(pk=1), {"title": {"nl": "Hallo"}}, [cfg]
    )

    # Source: "Translation field '%s' not found on %s"
    assert any("Translation field" in r.message for r in caplog.records)


def test_sync_all_translations_logs_error_on_update_or_create_failure(caplog):
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
    viernulvier._sync_all_translations(
        SimpleNamespace(pk=1), {"title": {"nl": "Hallo"}}, [cfg]
    )

    # Source: "Error syncing %s translations for ..."
    assert any("Error syncing" in r.message for r in caplog.records)


def test_sync_all_translations_skips_none_language_values():
    """Languages with None values are skipped; non-None values are processed."""
    called_with_langs = []

    class FakeMeta:
        def get_field(self, _name):
            return models.CharField(name="title", max_length=255)

    class FakeManager:
        def update_or_create(self, **kwargs):
            # language_fk default is "language_id"
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

    # "de": None → skipped; "nl" and "fr" (even empty string) → processed
    viernulvier._sync_all_translations(
        SimpleNamespace(pk=1),
        {"title": {"nl": "Hallo", "fr": "Bonjour", "de": None}},
        [cfg],
    )

    assert "nl" in called_with_langs
    assert "fr" in called_with_langs
    assert "de" not in called_with_langs


def test_sync_all_translations_applies_value_transform():
    """value_transforms are applied before persisting translated values."""
    saved_updates = {}

    class FakeMeta:
        def get_field(self, _name):
            return models.CharField(name="title", max_length=255)

    class FakeManager:
        def update_or_create(self, **kwargs):
            saved_updates.update(kwargs.get("defaults", {}))
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
        value_transforms={"title": lambda v: str(v).upper()},
    )

    viernulvier._sync_all_translations(
        SimpleNamespace(pk=1), {"title": {"nl": "hallo"}}, [cfg]
    )

    assert saved_updates.get("title") == "HALLO"


def test_sync_all_translations_skips_when_transform_returns_none():
    """If a transform returns None the field is omitted from the update."""
    update_or_create_called = [False]

    class FakeMeta:
        def get_field(self, _name):
            return models.CharField(name="title", max_length=255)

    class FakeManager:
        def update_or_create(self, **kwargs):
            update_or_create_called[0] = True
            # defaults should be empty because the only field was filtered out
            assert not kwargs.get("defaults"), "Expected no defaults when transform returns None"
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
        value_transforms={"title": lambda v: None},
    )

    viernulvier._sync_all_translations(
        SimpleNamespace(pk=1), {"title": {"nl": "hallo"}}, [cfg]
    )
    # update_or_create should NOT be called because field_updates is empty
    assert not update_or_create_called[0]


# ---------------------------------------------------------------------------
# _sync_m2m
# ---------------------------------------------------------------------------


def test_sync_m2m_returns_early_when_payload_is_not_list():
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

    viernulvier._sync_m2m(
        SimpleNamespace(pk=1), {"genres": "not-a-list"}, cfg, fk_cache
    )

    through_model.objects.filter.assert_not_called()


def test_sync_m2m_warns_when_related_object_not_found(caplog):
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

            @staticmethod
            def bulk_create(objs, **_kw):
                pass

    cfg = M2MConfig(
        api_key="items",
        related_model=FakeRelatedModel,
        through_model=FakeThroughModel,
        parent_fk="parent",
        related_fk="related",
    )
    fk_cache = FKCache()
    fk_cache._loaded[FakeRelatedModel] = True  # skip warmup

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    viernulvier._sync_m2m(
        SimpleNamespace(pk=1), {"items": ["ext-missing"]}, cfg, fk_cache
    )

    # Source: "%s with %s=%r not found — sync related models first."
    assert any("not found" in r.message for r in caplog.records)


def test_sync_m2m_logs_error_on_bulk_create_fallback_failure(caplog):
    """When bulk_create fails and individual save also fails, an error is logged."""

    class FakeRelatedModel:
        __name__ = "FakeRelated"

        class DoesNotExist(Exception):
            pass

        def __init__(self, **kwargs):
            self._kwargs = kwargs
            self.pk = kwargs.get("pk", 1)

        class objects:
            @staticmethod
            def get(**_kwargs):
                obj = FakeRelatedModel(pk=1)
                return obj

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

            @staticmethod
            def bulk_create(objs, **_kw):
                raise RuntimeError("bulk_create failed")

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
    viernulvier._sync_m2m(
        SimpleNamespace(pk=1), {"items": ["ext-1"]}, cfg, fk_cache
    )

    # Source: "Error creating %s for %s pk=%s"
    assert any("Error creating" in r.message for r in caplog.records)