"""Tests for Viernulvier scraper fetch, error handling, and persistence."""
import datetime
import logging
from contextlib import contextmanager
from unittest.mock import Mock

import pytest
import requests
from django.db import IntegrityError
from django.db import connection, models
from django.test.utils import isolate_apps

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import _parse_field_value, ModelSyncConfig


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

    with pytest.raises(viernulvier.ScraperError, match="endpoint must be a relative path"):
        viernulvier.fetch_viernulvier(endpoint="https://evil.com/events")

    with pytest.raises(viernulvier.ScraperError, match="endpoint must be a relative path"):
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

    with pytest.raises(viernulvier.ScraperError, match="status=403.*detail=Forbidden: access denied"):
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

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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
            lambda endpoint="/events", params=None: [{"@id": "https://example.com/1", "title": "new"}],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Missing '@id' for item" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_logs_info_on_empty_response(monkeypatch, caplog):
    """Test that an empty response is logged appropriately."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(viernulvier, "fetch_viernulvier", lambda endpoint="/events", params=None: [])

        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        assert any(
            "Sync finished" in r.message and "saved=0" in r.message for r in caplog.records
        )


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_handles_special_chars_and_nulls(monkeypatch):
    """Test that sync_viernulvier correctly handles special characters and null values."""
    with _temp_viernulvier_model() as ViernulvierItem:
        payload = {"@id": "https://example.com/9", "title": "Café 🎭", "description": None}
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [payload],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        obj = ViernulvierItem.objects.get(id="https://example.com/9")
        assert obj.title == "Café 🎭"
        assert obj.description is None


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_handles_large_payload(monkeypatch):
    """Test that sync_viernulvier can handle large payloads with many items."""
    with _temp_viernulvier_model() as ViernulvierItem:
        items = [{"@id": f"https://example.com/{i}", "title": f"T{i}"} for i in range(50)]
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: items,
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        assert any(
            "Sync finished" in r.message and "saved=1" in r.message and "errors=1" in r.message
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
            lambda endpoint="/events", params=None: ["not-a-dict", {"@id": "https://example.com/2", "title": "B"}],
        )

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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

        assert parsed == datetime.datetime(1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    def test_throws_no_error_for_year_zero_date(self):
        """Should accept date fields that have year 0000."""
        from apps.events.models import Event

        field = Event._meta.get_field("starts_at")
        value = "0000-01-01T00:00:00+00:00"
        parsed = _parse_field_value(field, value)

        assert parsed == datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

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

        original_fetch = viernulvier.fetch_viernulvier

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
        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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
        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events", params=params)

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
    """Test that sync_viernulvier creates a FAILED log when fetch_viernulvier raises an exception."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        def failing_fetch(endpoint="/events", params=None):
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
    """Test that sync_viernulvier creates a SUCCESS log even with empty response."""
    from apps.import_log.models import ImportLog

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events", params=None: [],
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

        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

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
        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        # Second sync
        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert ImportLog.objects.count() == 2
        logs = ImportLog.objects.all().order_by('started_at')
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
        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        # Sync to /venues
        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/venues")

        assert ImportLog.objects.count() == 2
        sources = list(ImportLog.objects.values_list('source', flat=True))
        assert "viernulvier:/events" in sources
        assert "viernulvier:/venues" in sources
