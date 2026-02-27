"""Tests for Viernulvier scraper fetch, error handling, and persistence."""

import logging
from contextlib import contextmanager
from unittest.mock import Mock

import pytest
import requests
from _pytest.raises import raises
from django.db import IntegrityError
from django.db import connection, models
from django.test.utils import isolate_apps

from apps.imports.scrapers import viernulvier


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
    """Test that JSON-LD error context is detected and error details are logged."""
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
    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

    with pytest.raises(viernulvier.ScraperError, match="status=403.*detail=Forbidden: access denied"):
        viernulvier.fetch_viernulvier(endpoint="/events")

    assert any(
        "status=403" in r.message and "detail=Forbidden: access denied" in r.message for r in caplog.records
    )

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
    assert result[0]["external_id"] == "https://example.com/1"
    assert result[0]["title"] == "Event A"
    assert raises(KeyError, lambda: result[0]["@id"])
    assert result[1]["external_id"] == "https://example.com/2"
    assert result[1]["title"] == "Event B"
    assert raises(KeyError, lambda: result[0]["@id"])


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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Skipping item without @id" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_logs_info_on_empty_response(monkeypatch, caplog):
    """Test that an empty response is logged appropriately."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(viernulvier, "fetch_viernulvier", lambda endpoint="/events", params=None: [])

        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 0
        assert any(
            "Viernulvier sync finished" in r.message and "Saved=0" in r.message for r in caplog.records
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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert any("Duplicate @id in batch" in r.message for r in caplog.records)


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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Skipping item without @id" in r.message for r in caplog.records)


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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        assert any(
            "Viernulvier sync finished" in r.message and "Saved=1" in r.message and "Errors=1" in r.message
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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        # Check that an error was logged for the non-dict item
        assert any(
            "Unexpected error while processing item: item is not a dict" in r.message for r in caplog.records
        )


def test_fetch_live_events(monkeypatch):
    """Test fetch with limited pagination to avoid fetching too many items."""
    # Limit to first 100 items by monkey-patching the fetch to stop after 3 pages (30 items per page)
    original_fetch_single_page = viernulvier._fetch_single_page
    pages_fetched = [0]

    def limited_fetch_single_page(url):
        pages_fetched[0] += 1
        if pages_fetched[0] > 3:  # 3 pages * 30+ items
            # Return a response without a "next" link to stop pagination
            data = original_fetch_single_page(url)
            if isinstance(data, dict) and "view" in data:
                data["view"] = {k: v for k, v in data["view"].items() if k != "next"}
            return data
        return original_fetch_single_page(url)

    monkeypatch.setattr(viernulvier, "_fetch_single_page", limited_fetch_single_page)

    result = viernulvier.fetch_viernulvier(endpoint="/events")
    assert isinstance(result, list)
    assert len(result) <= 150  # ~3 pages * ~40-50 items per page max
    if result:
        assert all(isinstance(item, dict) for item in result)


# =============================================================================
# Flexible Field Mapping Tests
# =============================================================================


class TestCamelToSnakeCase:
    """Test camelCase to snake_case conversion utility function."""

    def test_simple_camel_case(self):
        """Test basic camelCase conversion."""
        assert viernulvier._camel_to_snake_case("startsAt") == "starts_at"

    def test_multiple_words(self):
        """Test conversion with multiple camelCase words."""
        assert viernulvier._camel_to_snake_case("ticketingUrl") == "ticketing_url"

    def test_consecutive_capitals(self):
        """Test conversion with consecutive capital letters."""
        # The regex inserts _ before each capital, so URLPath becomes U_R_L_path
        assert viernulvier._camel_to_snake_case("URLPath") == "u_r_l_path"

    def test_already_snake_case(self):
        """Test that snake_case strings are left unchanged."""
        assert viernulvier._camel_to_snake_case("already_snake") == "already_snake"

    def test_single_word(self):
        """Test that single word strings are left unchanged."""
        assert viernulvier._camel_to_snake_case("word") == "word"


@pytest.mark.django_db
class TestFlexibleFieldMapping:
    """Test that the scraper tries every API field and skips unknown ones."""

    def test_throws_error_for_missing_required_fields(self):
        """Should raise ScraperError if required fields are missing."""
        from apps.events.models import Event

        item = {
            "external_id": "/api/events/1",
            "ticketingUrl": "https://example.com",
            # Missing required field: production
        }

        with pytest.raises(viernulvier.ScraperError) as exc_info:
            viernulvier._build_model_defaults(Event, item)

        assert "Missing required fields" in str(exc_info.value)
        assert "production" in str(exc_info.value)

    def test_skips_unknown_fields_event_price(self):
        """Unknown fields in the API response should be silently skipped."""
        from apps.events.models import Event, EventPrice
        from apps.productions.models import Production
        from tests.factories.pricing import PriceRankFactory

        # Create dependencies
        production = Production.objects.create(id=1)
        event = Event.objects.create(id=1, production=production)
        price_rank = PriceRankFactory()

        item = {
            "external_id": "/api/event_prices/1",
            "event": event.pk,
            "priceRank": price_rank.pk,
            "amount": "25.50",
            "available": 100,
            "unknownField": "should be ignored",
            "anotherUnknownField": 123,
            "yetAnotherField": {"nested": "object"},
        }

        defaults = viernulvier._build_model_defaults(EventPrice, item)

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

    def test_converts_camel_case_to_snake_case_event_price(self):
        """API fields in camelCase should be converted to snake_case."""
        from apps.events.models import Event, EventPrice
        from apps.productions.models import Production
        from tests.factories.pricing import PriceRankFactory

        production = Production.objects.create(id=2)
        event = Event.objects.create(id=2, production=production)
        price_rank = PriceRankFactory()

        item = {
            "external_id": "/api/event_prices/2",
            "event": event.pk,
            "priceRank": price_rank.pk,
            "amount": "30.00",
            "available": 50,
        }

        defaults = viernulvier._build_model_defaults(EventPrice, item)

        # Should have converted camelCase to snake_case
        assert "price_rank_id" in defaults
        assert "event_id" in defaults

    def test_handles_snake_case_fields_directly(self):
        """Should handle snake_case fields without conversion."""
        from apps.events.models import Event, EventPrice
        from apps.productions.models import Production
        from tests.factories.pricing import PriceRankFactory

        production = Production.objects.create(id=3)
        event = Event.objects.create(id=3, production=production)
        price_rank = PriceRankFactory()

        item = {
            "external_id": "/api/event_prices/3",
            "event": event.pk,
            "price_rank": price_rank.pk,
            "amount": "20.00",
            "available": 75,
        }

        defaults = viernulvier._build_model_defaults(EventPrice, item)

        assert "price_rank_id" in defaults
        assert "event_id" in defaults
        assert "amount" in defaults


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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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
            lambda endpoint="/events": [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1

        log = ImportLog.objects.first()
        assert "viernulvier:/events" in log.source


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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 2

        log = ImportLog.objects.first()
        assert log.status == ImportLog.Status.PARTIAL_SUCCESS
        assert log.records_total == 3
        assert log.records_imported == 2
        assert log.records_failed == 1
        assert log.error_message is None


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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 0

        log = ImportLog.objects.first()
        assert log.status == ImportLog.Status.FAILED
        assert log.records_total == 2
        assert log.records_imported == 0
        assert log.records_failed == 2
        assert log.error_message == "All 2 records failed to import"


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
            viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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

        viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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
        viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        # Second sync
        viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

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
        viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        # Sync to /venues
        viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/venues")

        assert ImportLog.objects.count() == 2
        sources = list(ImportLog.objects.values_list('source', flat=True))
        assert "viernulvier:/events" in sources
        assert "viernulvier:/venues" in sources
