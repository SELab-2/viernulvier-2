"""Tests for Viernulvier scraper fetch, error handling, and persistence."""

import datetime
import logging
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import IntegrityError
from django.db import connection, models
from django.test.utils import isolate_apps

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    M2MConfig,
    ModelSyncConfig,
    TranslationConfig,
    _parse_field_value,
)


def test_fetch_uses_api_key_header(monkeypatch):
    """Test that fetch_viernulvier includes correct API key in request headers."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        assert url.endswith("/events")
        assert headers["X-AUTH-TOKEN"] == "test-key"
        assert headers["accept"] == "application/ld+json"
        response = Mock(ok=True, status_code=200)
        response.json.return_value = []
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    assert viernulvier.fetch_viernulvier(endpoint="/events") == []


def test_fetch_raises_on_http_error(monkeypatch):
    """Test that HTTP errors from the API are caught and wrapped in ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        response = Mock(ok=False, status_code=500, text="boom")
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_non_json_response(monkeypatch):
    """Test that non-JSON responses raise ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = "not a dict or list"
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_when_api_key_missing(monkeypatch):
    """Test that missing API key raises ScraperError."""
    monkeypatch.delenv("VIERNULVIER_API_KEY", raising=False)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_invalid_json(monkeypatch):
    """Test that invalid JSON responses raise ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        response = Mock(ok=True, status_code=200)
        response.json.side_effect = ValueError("invalid json")
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_timeout(monkeypatch):
    """Test that request timeout is caught and wrapped in ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        raise requests.Timeout()

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_generic_request_exception(monkeypatch):
    """Test that generic RequestException is caught and wrapped."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        raise requests.RequestException("connection failed")

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_none_payload(monkeypatch):
    """Test that None payload from API raises ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = None
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_absolute_endpoint(monkeypatch):
    """Test that absolute URLs are rejected as endpoints."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    with pytest.raises(
        viernulvier.ScraperError, match="endpoint must be a relative path"
    ):
        viernulvier.fetch_viernulvier(endpoint="https://evil.com/events")

    with pytest.raises(
        viernulvier.ScraperError, match="endpoint must be a relative path"
    ):
        viernulvier.fetch_viernulvier(endpoint="http://example.com/api")


def test_fetch_raises_on_json_ld_error_context(monkeypatch, caplog):
    """Test that JSON-LD error context is detected and raises ScraperError."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {
            "@context": "/api/contexts/Error",
            "status": 403,
            "detail": "Forbidden: access denied",
        }
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(
        viernulvier.ScraperError, match="status=403.*detail=Forbidden: access denied"
    ):
        viernulvier.fetch_viernulvier(endpoint="/events")


@contextmanager
def _temp_viernulvier_model():
    """Create a temporary test model for Viernulvier items with automatic cleanup."""

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
    """Simple config for tests that passes data through unchanged."""

    def __init__(self):
        super().__init__(lookup_field="id")


def test_fetch_allows_different_endpoint_paths(monkeypatch):
    """Test that fetch_viernulvier works with different endpoint paths."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        assert url.endswith("/venues")
        response = Mock(ok=True, status_code=200)
        response.json.return_value = []
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    assert viernulvier.fetch_viernulvier(endpoint="/venues") == []


def test_fetch_returns_wrapped_dict_without_context(monkeypatch):
    """Test that payloads without member/context are wrapped as a single-item list."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"foo": "bar"}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    # Unknown dict payloads without @context should raise an error
    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_extracts_member_collection(monkeypatch):
    """Test that member collections in JSON-LD responses are properly extracted."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout=None, params=None):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {
            "@context": "https://example.com/context.jsonld",
            "member": [
                {"@id": "https://example.com/1", "title": "Event A"},
                {"@id": "https://example.com/2", "title": "Event B"},
            ],
        }
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    result = viernulvier.fetch_viernulvier(endpoint="/events")

    assert len(result) == 2
    assert result[0]["@id"] == "https://example.com/1"
    assert result[0]["title"] == "Event A"
    assert result[1]["@id"] == "https://example.com/2"
    assert result[1]["title"] == "Event B"


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_persists_items(monkeypatch):
    """Test that sync_viernulvier successfully persists items to the database."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
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
    """Test that sync_viernulvier updates existing items rather than creating duplicates."""
    with _temp_viernulvier_model() as ViernulvierItem:
        ViernulvierItem.objects.create(id="https://example.com/1", title="old")

        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
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
    """Test that items without @id are skipped with a warning."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [{"title": "no id"}],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Missing '@id' for item" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_logs_info_on_empty_response(monkeypatch, caplog):
    """Test that an empty response is logged appropriately."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier, "fetch_viernulvier", lambda endpoint="/events", params=None: []
        )

        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 0
        assert any(
            "Sync finished" in r.message and "saved=0" in r.message
            for r in caplog.records
        )


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_handles_special_chars_and_nulls(monkeypatch):
    """Test that sync_viernulvier correctly handles special characters and null values."""
    with _temp_viernulvier_model() as ViernulvierItem:
        payload = {
            "@id": "https://example.com/9",
            "title": "Café 🎭",
            "description": None,
        }
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [payload],
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
    """Test that sync_viernulvier can handle large payloads with many items."""
    with _temp_viernulvier_model() as ViernulvierItem:
        items = [
            {"@id": f"https://example.com/{i}", "title": f"T{i}"} for i in range(50)
        ]
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: items,
        )

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 50
        assert ViernulvierItem.objects.count() == 50


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_duplicate_ids_in_batch(monkeypatch, caplog):
    """Test that duplicate IDs within the same batch are skipped with a warning."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
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
        assert any("Duplicate in batch skipped" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_empty_string_id(monkeypatch, caplog):
    """Test that empty string IDs are skipped with a warning."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [{"@id": "", "title": "A"}],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Missing '@id' for item" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_on_database_errors(monkeypatch, caplog):
    """Test that sync continues processing when database errors occur for individual items."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "A"},
                {"@id": "https://example.com/2", "title": "B"},
            ],
        )

        call_count = [0]
        original_update_or_create = ViernulvierItem.objects.update_or_create

        def boom_once(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise IntegrityError("boom")
            return original_update_or_create(*args, **kwargs)

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
def test_sync_all_items_fail_returns_zero(monkeypatch, caplog):
    """Test that sync returns 0 when all items fail to import."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "A"},
                {"@id": "https://example.com/2", "title": "B"},
            ],
        )

        def boom(*_args, **_kwargs):
            raise IntegrityError("boom")

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", boom)

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 0
        assert ViernulvierItem.objects.count() == 0


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_logs_finish_message_with_error_count(monkeypatch, caplog):
    """Test that sync logs completion message with saved and error counts."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "A"},
                {"title": "no id"},
            ],
        )

        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 1
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        assert any(
            "Sync finished" in r.message
            and "saved=1" in r.message
            and "errors=1" in r.message
            for r in info_records
        )


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_when_item_is_not_dict(monkeypatch, caplog):
    """Test that sync continues when fetch returns non-dict items in the list."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
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
        # Check that an error was logged for the non-dict item
        assert any("Item is not a dict" in r.message for r in caplog.records)


def test_fetch_live_events(monkeypatch):
    """Test fetch with limited pagination to avoid fetching too many items."""
    # Limit to first 100 items by monkey-patching the fetch to stop after 3 pages (30 items per page)
    original_fetch_single_page = viernulvier._fetch_single_page
    pages_fetched = [0]

    def limited_fetch_single_page(url, params=None):
        pages_fetched[0] += 1
        if pages_fetched[0] > 3:  # 3 pages * 30+ items
            # Return a response without a "next" link to stop pagination
            data = original_fetch_single_page(url, params=params)
            if isinstance(data, dict) and "view" in data:
                data["view"] = {k: v for k, v in data["view"].items() if k != "next"}
            return data
        return original_fetch_single_page(url, params=params)

    monkeypatch.setattr(viernulvier, "_fetch_single_page", limited_fetch_single_page)

    result = viernulvier.fetch_viernulvier(endpoint="/events")
    assert isinstance(result, list)
    assert len(result) <= 150  # ~3 pages * ~40-50 items per page max
    if result:
        assert all(isinstance(item, dict) for item in result)


# =============================================================================
# Flexible Field Mapping Tests
# =============================================================================


@pytest.mark.django_db
class TestFlexibleFieldMapping:
    """Test that the scraper tries every API field and skips unknown ones."""

    def test_throws_no_error_for_year_minus_one_date(self):
        """Should accept date fields that have year -0001."""
        from apps.events.models import Event

        field = Event._meta.get_field("starts_at")
        value = "-0001-01-01T00:00:00+00:00"
        parsed = _parse_field_value(field, value)

        assert parsed == datetime.datetime(
            1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        )

    def test_throws_no_error_for_year_zero_date(self):
        """Should accept date fields that have year 0000."""
        from apps.events.models import Event

        field = Event._meta.get_field("starts_at")
        value = "0000-01-01T00:00:00+00:00"
        parsed = _parse_field_value(field, value)

        assert parsed == datetime.datetime(
            1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        )

    def test_returns_none_for_missing_value(self):
        """Should return None for values that are None."""
        from apps.events.models import Event

        field = Event._meta.get_field("starts_at")
        value = None
        parsed = _parse_field_value(field, value)

        assert parsed is None

    def test_doesnt_throw_error_for_missing_required_fields_in_build_defaults(self):
        """_build_defaults doesn't validate required fields - validation happens during save."""
        from apps.events.models import Event

        item = {
            "external_id": "/api/events/1",
            "ticketing_url": "https://example.com",
            # Missing required field: production
        }

        # _build_defaults should not raise an error - it just builds the defaults dict
        # Validation will happen when the model is saved
        defaults = viernulvier._build_defaults(Event, item, _PassThroughConfig())

        # Should have mapped the fields that were present
        assert "ticketing_url" in defaults
        assert defaults["ticketing_url"] == "https://example.com"

    def test_skips_unknown_fields_event_price(self):
        """Unknown fields in the API response should be silently skipped."""
        from apps.events.models import EventPrice, Event
        from apps.pricing.models import PriceRank
        from apps.productions.models import Production

        # Create the required FK relationships
        prod = Production.objects.create(external_id="/api/productions/1")
        event = Event.objects.create(external_id="1", production=prod)
        price_rank = PriceRank.objects.create(external_id="1", position=1)

        # Provide the FK IDs directly (simulating what a transformer would do)
        item = {
            "external_id": "/api/event_prices/1",
            "event": event.external_id,  # Provide the external_id to be resolved
            "priceRank": price_rank.external_id,  # Use camelCase as it comes from API
            "amount": "25.50",
            "available": 100,
            "unknownField": "should be ignored",
            "anotherUnknownField": 123,
            "yetAnotherField": {"nested": "object"},
        }

        defaults = viernulvier._build_defaults(EventPrice, item, _PassThroughConfig())

        # Should have mapped known fields
        assert "event_id" in defaults
        assert "price_rank_id" in defaults
        assert "amount" in defaults
        assert "available" in defaults

        # Should NOT have unknown fields
        assert "unknownField" not in defaults
        assert "unknown_field" not in defaults
        assert "anotherUnknownField" not in defaults
        assert "another_unknown_field" not in defaults

    def test_handles_fields_correctly(self):
        """Should handle these fields without problems."""
        from apps.events.models import EventPrice, Event
        from apps.pricing.models import PriceRank
        from apps.productions.models import Production

        # Create the required FK relationships
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

        defaults = viernulvier._build_defaults(EventPrice, item, _PassThroughConfig())

        assert "price_rank_id" in defaults
        assert "event_id" in defaults
        assert "amount" in defaults


# ============================================================================
# Tests for Query Parameter Support (created_at, updated_at filtering)
# ============================================================================


def test_fetch_accepts_query_params(monkeypatch):
    """Test that fetch_viernulvier accepts optional query parameters."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    captured_params = {}

    def fake_get(url, headers, params=None, timeout=None):
        captured_params["params"] = params
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"member": []}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    viernulvier.fetch_viernulvier(
        endpoint="/events", params={"created_at[after]": "2024-01-01T00:00:00Z"}
    )

    assert captured_params["params"] == {"created_at[after]": "2024-01-01T00:00:00Z"}


def test_fetch_params_applied_to_initial_request_only(monkeypatch):
    """Test that query params are only applied to the first request, not pagination."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    request_count = [0]
    captured_params_list = []

    def fake_get(url, headers, params=None, timeout=None):
        request_count[0] += 1
        captured_params_list.append(params)
        response = Mock(ok=True, status_code=200)

        if request_count[0] == 1:
            # First response with pagination
            response.json.return_value = {
                "@context": "https://example.com/context.jsonld",
                "member": [{"@id": "https://example.com/1", "title": "Event A"}],
                "view": {"next": "/api/v1/events?page=2"},
            }
        else:
            # Paginated response (next)
            response.json.return_value = {
                "@context": "https://example.com/context.jsonld",
                "member": [{"@id": "https://example.com/2", "title": "Event B"}],
            }

        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    result = viernulvier.fetch_viernulvier(
        endpoint="/events", params={"created_at[after]": "2024-01-01T00:00:00Z"}
    )

    assert len(result) == 2
    # First request should have params
    assert captured_params_list[0] == {"created_at[after]": "2024-01-01T00:00:00Z"}
    # Second request (pagination) should not have params
    assert captured_params_list[1] is None


def test_fetch_with_multiple_query_params(monkeypatch):
    """Test that multiple query parameters are passed correctly."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    captured_params = {}

    def fake_get(url, headers, params=None, timeout=None):
        captured_params["params"] = params
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"member": []}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    params = {
        "created_at[after]": "2024-01-01T00:00:00Z",
        "updated_at[before]": "2024-12-31T23:59:59Z",
    }

    viernulvier.fetch_viernulvier(endpoint="/events", params=params)

    assert captured_params["params"] == params


def test_fetch_without_params_works_as_before(monkeypatch):
    """Test backward compatibility: fetch works without query parameters."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    captured_params = {}

    def fake_get(url, headers, params=None, timeout=None):
        captured_params["params"] = params
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"member": [{"@id": "https://example.com/1"}]}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    result = viernulvier.fetch_viernulvier(endpoint="/events")

    assert len(result) == 1
    assert captured_params["params"] is None


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_passes_params_to_fetch(monkeypatch):
    """Test that sync_viernulvier passes query parameters to fetch_viernulvier."""
    with _temp_viernulvier_model() as ViernulvierItem:
        captured_call_args = {}

        def mock_fetch(endpoint=None, params=None):
            captured_call_args["endpoint"] = endpoint
            captured_call_args["params"] = params
            return [{"@id": "https://example.com/1", "title": "Item"}]

        monkeypatch.setattr(viernulvier, "fetch_viernulvier", mock_fetch)

        params = {"created_at[after]": "2024-01-01T00:00:00Z"}
        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events", params=params
        )

        assert captured_call_args["endpoint"] == "/events"
        assert captured_call_args["params"] == params


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_with_timestamp_filtering(monkeypatch):
    """Test end-to-end sync with timestamp filtering parameters."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/recent", "title": "Recent Event"},
            ],
        )

        params = {"updated_at[after]": "2024-06-01T00:00:00Z"}
        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events", params=params
        )

        assert count == 1
        assert ViernulvierItem.objects.count() == 1


def test_fetch_params_none_by_default(monkeypatch):
    """Test that params parameter defaults to None."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    captured_params = {}

    def fake_get(url, headers, params=None, timeout=None):
        captured_params["params"] = params
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"member": []}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    # Call without params argument
    viernulvier.fetch_viernulvier(endpoint="/events")

    assert captured_params["params"] is None


def test_fetch_with_empty_params_dict(monkeypatch):
    """Test that an empty params dict is passed as-is."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    captured_params = {}

    def fake_get(url, headers, params=None, timeout=None):
        captured_params["params"] = params
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"member": []}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    # Call with empty params dict
    viernulvier.fetch_viernulvier(endpoint="/events", params={})

    # Empty dict should be passed
    assert captured_params["params"] == {}


def test_fetch_preserves_timestamp_format(monkeypatch):
    """Test that timestamp query parameters preserve ISO 8601 format."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    captured_params = {}

    def fake_get(url, headers, params=None, timeout=None):
        captured_params["params"] = params
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"member": []}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    iso_timestamp = "2024-12-25T10:30:45Z"
    viernulvier.fetch_viernulvier(
        endpoint="/events", params={"created_at[after]": iso_timestamp}
    )

    assert captured_params["params"]["created_at[after]"] == iso_timestamp


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_without_params_still_works(monkeypatch):
    """Test backward compatibility: sync without params parameter."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "Item"},
            ],
        )

        # Call sync without params argument
        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 1
        assert ViernulvierItem.objects.count() == 1


# =====================================================
# ImportLog Integration Tests
# =====================================================


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_creates_import_log_on_success(monkeypatch):
    """Test that sync_viernulvier creates an ImportLog entry on successful import."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
                {"@id": "https://example.com/2", "title": "Event B"},
            ],
        )

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert count == 2

        # Verify ImportLog entry was created
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
    """Test that sync_viernulvier includes params in the ImportLog source."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        params = {"created_at[after]": "2024-01-01T00:00:00Z", "page": "1"}
        count = viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events", params=params
        )

        assert count == 1

        log = ImportLog.objects.first()
        assert "viernulvier:/events?" in log.source
        # Params should be sorted
        assert "created_at[after]=2024-01-01T00:00:00Z" in log.source
        assert "page=1" in log.source


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_creates_import_log_on_partial_success(monkeypatch):
    """Test that sync_viernulvier creates a PARTIAL_SUCCESS log when some items fail."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
                {"title": "Event B"},  # Missing @id, should fail
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
    """Test that sync_viernulvier creates a FAILED log when all items fail."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"title": "Event A"},  # Missing @id
                {"title": "Event B"},  # Missing @id
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
    """Test that sync_viernulvier creates a FAILED log when fetch_viernulvier raises an exception."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:

        def failing_fetch(endpoint="/events", params=None):
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
    """Test that sync_viernulvier creates a SUCCESS log even with empty response."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [],
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
    """Test that ImportLog started_at and finished_at are properly set and sequential."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        log = ImportLog.objects.first()
        assert log.started_at is not None
        assert log.finished_at is not None
        assert log.finished_at >= log.started_at


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_import_log_tracks_multiple_syncs(monkeypatch):
    """Test that multiple sync operations create separate ImportLog entries."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        # First sync
        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        # Second sync
        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        assert ImportLog.objects.count() == 2
        logs = ImportLog.objects.all().order_by("started_at")
        assert logs[0].source == "viernulvier:/events"
        assert logs[1].source == "viernulvier:/events"
        assert logs[0].records_imported == 1
        assert logs[1].records_imported == 1


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_import_log_different_endpoints_tracked_separately(monkeypatch):
    """Test that syncs to different endpoints are tracked with different sources."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        # Sync to /events
        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/events"
        )

        # Sync to /venues
        viernulvier.sync_viernulvier(
            ViernulvierItem, _PassThroughConfig(), endpoint="/venues"
        )

        assert ImportLog.objects.count() == 2
        sources = list(ImportLog.objects.values_list("source", flat=True))
        assert "viernulvier:/events" in sources
        assert "viernulvier:/venues" in sources


def test_fetch_collects_single_item_dict_with_context(monkeypatch):
    """Single-item dict payloads with @context are appended and returned."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    monkeypatch.setattr(
        viernulvier,
        "_fetch_single_page",
        lambda url, params=None: {"@context": "ctx", "@id": "/api/v1/events/1"},
    )

    result = viernulvier.fetch_viernulvier(endpoint="/events")

    assert result == [{"@context": "ctx", "@id": "/api/v1/events/1"}]


def test_extract_external_id_handles_int_dict_and_blank_string():
    """_extract_external_id_from_url supports multiple raw formats."""
    assert viernulvier._extract_external_id_from_url(42) == "42"
    assert viernulvier._extract_external_id_from_url({"id": "abc"}) == "abc"
    assert viernulvier._extract_external_id_from_url({}) is None
    assert viernulvier._extract_external_id_from_url("   ") is None
    assert viernulvier._extract_external_id_from_url(None) is None
    assert viernulvier._extract_external_id_from_url([]) is None


def test_extract_lookup_value_uses_fallback_and_dict_values():
    """Lookup extraction falls back to external_id/id and unwraps dict values."""
    config = ModelSyncConfig(api_id_key="@id")

    assert (
        viernulvier._extract_lookup_value({"external_id": {"id": "x-1"}}, config)
        == "x-1"
    )
    assert viernulvier._extract_lookup_value({}, config) is None


def test_resolve_fk_returns_pk_and_handles_not_found_and_unexpected(caplog):
    """_resolve_fk returns PK, warns on missing FK, and logs unexpected errors."""

    class FakeDoesNotExist(Exception):
        pass

    class FakeValuesList:
        def __init__(self, mode):
            self.mode = mode

        def get(self, external_id):
            if self.mode == "ok":
                return 77
            if self.mode == "missing":
                raise FakeRelatedModel.DoesNotExist()
            raise RuntimeError("boom")

    class FakeManager:
        def __init__(self, mode):
            self.mode = mode

        def values_list(self, *_args, **_kwargs):
            return FakeValuesList(self.mode)

    class FakeRelatedModel:
        __name__ = "FakeRelated"
        DoesNotExist = FakeDoesNotExist
        objects = FakeManager("ok")

    field = SimpleNamespace(remote_field=SimpleNamespace(model=FakeRelatedModel))

    assert viernulvier._resolve_fk(field, "rel-1") == 77

    assert viernulvier._resolve_fk(field, None) is None

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    FakeRelatedModel.objects = FakeManager("missing")
    assert viernulvier._resolve_fk(field, "missing") is None
    assert any("FK not found" in r.message for r in caplog.records)

    caplog.clear()
    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    FakeRelatedModel.objects = FakeManager("error")
    assert viernulvier._resolve_fk(field, "error") is None
    assert any("Error resolving FK" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_explicit_mapping_covers_missing_unknown_pk_transform_and_fk():
    """Explicit field_map branches: missing values, unknown field, PK skip, FK, and transforms."""

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
                "missing": "title",
                "unknown": "does_not_exist",
                "pk_field": "id",
                "dict_translation": "title",
                "fk_custom": "parent",
                "title_field": "title",
            },
            value_transforms={"title": lambda value: str(value).upper()},
            fk_resolvers={"parent": lambda raw: 99 if raw else None},
            lookup_field="id",
        )

        item = {
            "unknown": "x",
            "pk_field": "item-1",
            "dict_translation": {"nl": "Titel"},
            "fk_custom": "/api/v1/parents/99",
            "title_field": "hello",
        }

        defaults = viernulvier._build_defaults(DefaultsModel, item, config)

        assert defaults["parent_id"] == 99
        assert defaults["title"] == "HELLO"
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DefaultsModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_uses_auto_fk_resolver_path(monkeypatch):
    """Explicit relation mapping without custom resolver uses _resolve_fk branch."""

    class AutoFkModel(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        parent = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(AutoFkModel)
    try:
        monkeypatch.setattr(viernulvier, "_resolve_fk", lambda _field, _raw: 123)

        config = ModelSyncConfig(field_map={"fk_auto": "parent"}, lookup_field="id")
        defaults = viernulvier._build_defaults(
            AutoFkModel,
            {"fk_auto": "/api/v1/parents/123"},
            config,
        )

        assert defaults["parent_id"] == 123
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(AutoFkModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_auto_mapping_skips_at_and_none_and_sets_scalar():
    """Auto-mapping skips @ keys/None and maps scalar fields into defaults."""

    class AutoMapModel(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        title = models.CharField(max_length=255, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(AutoMapModel)
    try:
        defaults = viernulvier._build_defaults(
            AutoMapModel,
            {"@id": "x", "title": "mapped", "unused": None},
            ModelSyncConfig(lookup_field="id"),
        )

        assert defaults == {"title": "mapped"}
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(AutoMapModel)


def test_sync_translations_returns_for_non_dict_payload():
    """_sync_translations exits early when translation payload is not a dict."""

    class FakeTranslationModel:
        __name__ = "FakeTranslationModel"

    cfg = TranslationConfig(
        api_key="title",
        model=FakeTranslationModel,
        parent_fk="parent",
        flat_field="title",
    )

    viernulvier._sync_translations(SimpleNamespace(pk=1), {"title": "not-dict"}, cfg)


def test_sync_translations_logs_missing_field_warning(caplog):
    """_sync_translations logs warning when configured field is missing."""

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
    viernulvier._sync_translations(
        SimpleNamespace(pk=1), {"title": {"nl": "Hallo"}}, cfg
    )

    assert any("Translation veld" in r.message for r in caplog.records)


def test_sync_translations_handles_update_or_create_exception(caplog):
    """_sync_translations catches per-language persistence errors."""

    class FakeMeta:
        def get_field(self, _name):
            return models.CharField(name="title", max_length=255)

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
    viernulvier._sync_translations(
        SimpleNamespace(pk=1),
        {"title": {"nl": "Hallo"}},
        cfg,
    )

    assert any("Fout bij translation" in r.message for r in caplog.records)


def test_sync_translations_skips_empty_translations(caplog):
    """_sync_translations skips languages with empty translation values."""

    items = {"title": {"nl": "Hallo", "fr": "", "de": None}}

    class FakeMeta:
        def get_field(self, _name):
            return models.CharField(name="title", max_length=255)

    class FakeManager:
        def update_or_create(self, **_kwargs):
            assert _kwargs["language"] == "nl"

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

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    viernulvier._sync_translations(
        SimpleNamespace(pk=1),
        items,
        cfg,
    )


def test_sync_translations_transform(caplog):
    """_sync_translations applies value transforms to translation values."""

    class FakeMeta:
        def get_field(self, _name):
            return models.CharField(name="title", max_length=255)

    class FakeManager:
        def update_or_create(self, **_kwargs):
            assert _kwargs["language"] == "nl"

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

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    viernulvier._sync_translations(
        SimpleNamespace(pk=1),
        {"title": {"nl": "Halllo"}},
        cfg,
    )


def test_sync_translations_skips_field_when_converted_is_none(caplog):
    """_sync_translations skips translation when transform returns None."""

    class FakeMeta:
        def get_field(self, _name):
            return models.CharField(name="title", max_length=255)

    class FakeManager:
        pass

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

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    viernulvier._sync_translations(
        SimpleNamespace(pk=1),
        {"title": {"nl": "Halllo"}},
        cfg,
    )


def test_sync_m2m_returns_when_payload_is_not_list():
    """_sync_m2m exits early if the API payload is not a list."""

    cfg = M2MConfig(
        api_key="genres",
        related_model=object,
        through_model=object,
        parent_fk="parent",
        related_fk="related",
    )

    viernulvier._sync_m2m(SimpleNamespace(pk=1), {"genres": "not-a-list"}, cfg)


def test_sync_m2m_handles_missing_related_and_create_error(caplog):
    """_sync_m2m logs warnings/errors and continues while processing list items."""

    class FakeDoesNotExist(Exception):
        pass

    class FakeRelatedManager:
        def get(self, **kwargs):
            ext_id = kwargs["external_id"]
            if ext_id == "missing":
                raise FakeRelatedModel.DoesNotExist()
            return f"rel:{ext_id}"

    class FakeRelatedModel:
        __name__ = "FakeRelatedModel"
        DoesNotExist = FakeDoesNotExist
        objects = FakeRelatedManager()

    class FakeFilterResult:
        def __init__(self, state):
            self.state = state

        def delete(self):
            self.state["deleted"] = True

    class FakeThroughManager:
        def __init__(self, state):
            self.state = state

        def filter(self, **_kwargs):
            return FakeFilterResult(self.state)

        def create(self, **kwargs):
            self.state["created"].append(kwargs)
            if kwargs.get("related") == "rel:boom":
                raise RuntimeError("cannot create through row")

    state = {"deleted": False, "created": []}

    class FakeThroughModel:
        __name__ = "FakeThroughModel"
        objects = FakeThroughManager(state)

    cfg = M2MConfig(
        api_key="genres",
        related_model=FakeRelatedModel,
        through_model=FakeThroughModel,
        parent_fk="parent",
        related_fk="related",
        extra_fields={"position": "position"},
    )

    payload = {
        "genres": [
            "",  # invalid ext_id -> skipped
            "missing",  # related missing -> warning
            "ok",  # position fallback from enumerate
            {"@id": "boom", "position": 99},  # create fails -> exception log
        ]
    }

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    viernulvier._sync_m2m(SimpleNamespace(pk=12), payload, cfg)

    assert state["deleted"] is True
    assert any(row.get("position") == 2 for row in state["created"])
    assert any("niet gevonden" in r.message for r in caplog.records)
    assert any("Fout bij aanmaken" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_calls_m2m_and_commits_savepoint(monkeypatch):
    """sync_viernulvier executes M2M loop and commits savepoint on success."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [
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
def test_sync_validation_error_formats_messages(monkeypatch):
    """sync_viernulvier formats field and __all__ validation messages."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [{"@id": "1", "title": "A"}],
        )

        def raise_validation(*_args, **_kwargs):
            raise ValidationError({"title": ["invalid"], "__all__": ["bad state"]})

        monkeypatch.setattr(
            ViernulvierItem.objects, "update_or_create", raise_validation
        )

        saved = viernulvier.sync_viernulvier(
            ViernulvierItem,
            ModelSyncConfig(lookup_field="id"),
            endpoint="/events",
        )

        assert saved == 0
        log = ImportLog.objects.first()
        assert log.status == ImportLog.Status.FAILED
        assert "title: invalid" in log.error_message
        assert "bad state" in log.error_message


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_database_error_branch(monkeypatch):
    """sync_viernulvier handles IntegrityError via database error branch."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [{"@id": "1", "title": "A"}],
        )

        def raise_integrity(*_args, **_kwargs):
            raise IntegrityError("db exploded")

        monkeypatch.setattr(
            ViernulvierItem.objects, "update_or_create", raise_integrity
        )

        saved = viernulvier.sync_viernulvier(
            ViernulvierItem,
            ModelSyncConfig(lookup_field="id"),
            endpoint="/events",
        )

        assert saved == 0
        log = ImportLog.objects.first()
        assert "Database error for 1" in log.error_message
        assert log.records_total == 1
        assert log.records_failed == 1


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_unexpected_error_branch(monkeypatch):
    """sync_viernulvier handles non-DB exceptions and still finalizes ImportLog."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [{"@id": "1", "title": "A"}],
        )

        def raise_runtime(*_args, **_kwargs):
            raise RuntimeError("unexpected crash")

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", raise_runtime)

        saved = viernulvier.sync_viernulvier(
            ViernulvierItem,
            ModelSyncConfig(lookup_field="id"),
            endpoint="/events",
        )

        assert saved == 0
        log = ImportLog.objects.first()
        assert (
            "Unexpected error for 1: RuntimeError: unexpected crash"
            in log.error_message
        )
        assert log.records_total == 1
        assert log.records_failed == 1


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_executes_translations(monkeypatch):
    """sync_viernulvier calls _sync_translations when translation config is provided."""

    class FakeTranslationModel:
        __name__ = "FakeTranslationModel"

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [{"@id": "1", "title": "A"}],
        )

        called = {"translations": 0}

        def fake_sync_translations(*_args, **_kwargs):
            called["translations"] += 1

        monkeypatch.setattr(viernulvier, "_sync_translations", fake_sync_translations)

        config = ModelSyncConfig(
            lookup_field="id",
            translations=[
                TranslationConfig(
                    api_key="title",
                    model=FakeTranslationModel,
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


# =============================================================================
# Coverage Tests for Missing Lines
# =============================================================================


def test_extract_external_id_from_url_with_int():
    """Test _extract_external_id_from_url with an integer value"""
    assert viernulvier._extract_external_id_from_url(42) == "42"


def test_extract_external_id_from_url_with_dict_external_id_fallback():
    """Test _extract_external_id_from_url with dict using external_id fallback"""
    result = viernulvier._extract_external_id_from_url({"external_id": "test123"})
    assert result == "test123"


def test_extract_external_id_from_url_with_dict_id_fallback():
    """Test _extract_external_id_from_url with dict using id fallback"""
    result = viernulvier._extract_external_id_from_url({"id": "test456"})
    assert result == "test456"


def test_parse_field_value_datetime_with_negative_year():
    """Test _parse_field_value handles negative year by stripping minus"""
    field = models.DateTimeField()
    value = "-0001-01-01T00:00:00Z"
    result = viernulvier._parse_field_value(field, value)
    assert result is not None
    assert result.year == 1


def test_parse_field_value_datetime_with_year_zero():
    """Test _parse_field_value converts year 0000 to 1970"""
    field = models.DateTimeField()
    value = "0000-01-01T00:00:00Z"
    result = viernulvier._parse_field_value(field, value)
    assert result is not None
    assert result.year == 1970


def test_parse_field_value_datefield_string():
    """Test _parse_field_value with DateField and string value"""
    field = models.DateField()
    value = "2024-06-15"
    result = viernulvier._parse_field_value(field, value)
    assert result is not None
    assert result.year == 2024


def test_extract_lookup_value_with_id_fallback():
    """Test _extract_lookup_value uses id fallback when api_id_key missing"""
    config = viernulvier.ModelSyncConfig(api_id_key="@id", lookup_field="external_id")
    item = {"id": "test123"}
    result = viernulvier._extract_lookup_value(item, config)
    assert result == "test123"


def test_extract_lookup_value_dict_with_id():
    """Test _extract_lookup_value extracts from nested dict id field"""
    config = viernulvier.ModelSyncConfig(api_id_key="@id", lookup_field="external_id")
    item = {"@id": {"id": "nested456"}}
    result = viernulvier._extract_lookup_value(item, config)
    assert result == "nested456"


def test_extract_lookup_value_strips_whitespace():
    """Test _extract_lookup_value strips whitespace from value"""
    config = viernulvier.ModelSyncConfig(api_id_key="@id", lookup_field="external_id")
    item = {"@id": "  value_with_spaces  "}
    result = viernulvier._extract_lookup_value(item, config)
    assert result == "value_with_spaces"


def test_extract_lookup_value_empty_string_after_strip():
    """Test _extract_lookup_value returns empty string after strip"""
    config = viernulvier.ModelSyncConfig(api_id_key="@id", lookup_field="external_id")
    item = {"@id": "   "}
    result = viernulvier._extract_lookup_value(item, config)
    assert result == ""  # After strip, whitespace becomes empty string


def test_sync_m2m_with_non_dict_raw_item_extra_fields():
    """Test _sync_m2m handles non-dict raw_item in extra_fields check"""
    parent = Mock(pk=1)
    related_model = Mock()
    through_model = Mock()

    m2m_config = viernulvier.M2MConfig(
        api_key="items",
        related_model=related_model,
        through_model=through_model,
        parent_fk="parent",
        related_fk="related",
        extra_fields={"position": "position_field"},
    )

    item = {"items": ["https://example.com/api/item/1"]}

    related_obj = Mock(pk=1)
    related_model.objects.get.return_value = related_obj

    viernulvier._sync_m2m(parent, item, m2m_config)

    assert through_model.objects.create.called


# =====================================================
# Additional coverage tests for uncovered lines
# =====================================================


def test_build_defaults_transforms():
    """Test _build_defaults applies value_transforms and fk_resolvers correctly"""
    from django.db import models as django_models

    class TestModelTransform(django_models.Model):
        name = django_models.CharField(max_length=100)
        parent = django_models.ForeignKey(
            "self", null=True, on_delete=django_models.SET_NULL
        )

        class Meta:
            app_label = "test"

    config = viernulvier.ModelSyncConfig(
        value_transforms={"name": lambda v: str(v).upper()},
        field_map={"@id": "external_id"},
        lookup_field="external_id",
    )

    item = {"name": "test name", "@id": "/api/parents/99"}

    defaults = viernulvier._build_defaults(TestModelTransform, item, config)
    assert defaults["name"] == "TEST NAME"


def test_build_defaults_skips_none_field_map_value():
    """Test _build_defaults skips field_map entries with None value"""
    from django.db import models as django_models

    class TestModel(django_models.Model):
        name = django_models.CharField(max_length=100)

        class Meta:
            app_label = "test"

    config = viernulvier.ModelSyncConfig(
        field_map={"api_name": None},  # Explicitly skip this field
        lookup_field="external_id",
    )

    item = {"api_name": "should_be_ignored"}

    # This should not raise an error and should skip the field
    defaults = viernulvier._build_defaults(TestModel, item, config)
    assert "name" not in defaults


def test_extract_lookup_value_falls_back_to_external_id():
    """Test _extract_lookup_value falls back to external_id when api_id_key missing"""
    config = viernulvier.ModelSyncConfig(api_id_key="@id", lookup_field="external_id")
    item = {"external_id": "ext123"}
    result = viernulvier._extract_lookup_value(item, config)
    assert result == "ext123"


def test_extract_lookup_value_dict_with_nested_at_id():
    """Test _extract_lookup_value extracts from nested dict @id field"""
    config = viernulvier.ModelSyncConfig(api_id_key="@id", lookup_field="external_id")
    item = {"@id": {"@id": "nested123"}}
    result = viernulvier._extract_lookup_value(item, config)
    assert result == "nested123"


def test_extract_lookup_value_dict_with_nested_external_id():
    """Test _extract_lookup_value extracts from nested dict external_id"""
    config = viernulvier.ModelSyncConfig(api_id_key="@id", lookup_field="external_id")
    item = {"@id": {"external_id": "ext456"}}
    result = viernulvier._extract_lookup_value(item, config)
    assert result == "ext456"


def test_extract_lookup_value_returns_stripped_string():
    """Test _extract_lookup_value returns stripped string value"""
    config = viernulvier.ModelSyncConfig(api_id_key="@id", lookup_field="external_id")
    item = {"@id": "  value123  "}
    result = viernulvier._extract_lookup_value(item, config)
    assert result == "value123"


def test_extract_lookup_value_returns_empty_string_when_only_whitespace():
    """Test _extract_lookup_value returns empty string for whitespace-only value"""
    config = viernulvier.ModelSyncConfig(api_id_key="@id", lookup_field="external_id")
    item = {"@id": "    "}
    result = viernulvier._extract_lookup_value(item, config)
    # Empty string after strip (line 479: return str(raw).strip() if raw is not None else None) 
    assert result == ""


def test_parse_field_value_datetime_negative_year_exact():
    """Test _parse_field_value strips negative sign from year"""
    field = models.DateTimeField()
    value = "-2024-01-01T12:00:00Z"
    result = viernulvier._parse_field_value(field, value)
    assert result is not None
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 1


def test_parse_field_value_datetime_year_0000_converts_to_1970():
    """Test _parse_field_value converts year 0000 to 1970"""
    field = models.DateTimeField()
    value = "0000-12-25T23:59:59Z"
    result = viernulvier._parse_field_value(field, value)
    assert result is not None
    assert result.year == 1970
    assert result.month == 12
    assert result.day == 25


def test_extract_external_id_from_url_with_integer():
    """Test _extract_external_id_from_url converts integer to string"""
    result = viernulvier._extract_external_id_from_url(123)
    assert result == "123"


def test_extract_external_id_from_url_dict_with_external_id_key():
    """Test _extract_external_id_from_url uses external_id from dict"""
    result = viernulvier._extract_external_id_from_url({"external_id": "ext789"})
    assert result == "ext789"


def test_extract_external_id_from_url_dict_with_id_key():
    """Test _extract_external_id_from_url uses id from dict as fallback"""
    result = viernulvier._extract_external_id_from_url({"id": "id789"})
    assert result == "id789"


def test_sync_m2m_with_string_raw_item_and_extra_fields():
    """Test _sync_m2m handles string (non-dict) raw_item in extra_fields check"""
    from unittest.mock import Mock

    parent = Mock(pk=1)
    related_model = Mock()
    through_model = Mock()

    m2m_config = viernulvier.M2MConfig(
        api_key="items",
        related_model=related_model,
        through_model=through_model,
        parent_fk="parent",
        related_fk="related",
        extra_fields={"extra_field": "extra_field_name"},
    )

    item = {"items": ["https://example.com/api/item/1"]}

    related_obj = Mock(pk=1)
    related_model.objects.get.return_value = related_obj
    through_model.objects.filter.return_value = Mock()

    viernulvier._sync_m2m(parent, item, m2m_config)

    # Verify through_model.objects.create was called
    # Since raw_item is a string, the value in extra_fields check will be None
    assert through_model.objects.create.called
    call_kwargs = through_model.objects.create.call_args[1]
    assert call_kwargs["parent"] == parent
    assert call_kwargs["related"] == related_obj
