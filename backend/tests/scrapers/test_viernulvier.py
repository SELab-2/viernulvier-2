"""Tests for Viernulvier scraper fetch, error handling, and persistence."""
from contextlib import contextmanager
import logging

import pytest
from unittest.mock import Mock
import requests
from django.core.exceptions import FieldError
from django.db import DatabaseError, IntegrityError

from django.db import connection, models
from django.test.utils import isolate_apps

from apps.imports.scrapers import viernulvier


def test_fetch_uses_api_key_header(monkeypatch):
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
        assert url.endswith("/events")
        assert headers["X-Api-Key"] == "test-key"
        response = Mock(ok=True, status_code=200)
        response.json.return_value = []
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    assert viernulvier.fetch_viernulvier(endpoint="/events") == []


def test_fetch_raises_on_http_error(monkeypatch):
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
        response = Mock(ok=False, status_code=500, text="boom")
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("VIERNULVIER_API_KEY", raising=False)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_invalid_json(monkeypatch):
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
        response = Mock(ok=True, status_code=200)
        response.json.side_effect = ValueError("invalid json")
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_timeout(monkeypatch):
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
        raise requests.Timeout()

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_raises_on_generic_request_exception(monkeypatch):
    """Test that generic RequestException is caught and wrapped."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
        raise requests.RequestException("connection failed")

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_fetch_allows_data_key_payload(monkeypatch):
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"data": [{"id": 1}]}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    assert viernulvier.fetch_viernulvier(endpoint="/events") == [{"id": 1}]


def test_fetch_allows_items_key_payload(monkeypatch):
    """Test that payload with 'items' key is properly extracted."""
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"items": [{"id": 1}, {"id": 2}]}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    assert viernulvier.fetch_viernulvier(endpoint="/events") == [{"id": 1}, {"id": 2}]


def test_fetch_raises_on_none_payload(monkeypatch):
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
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


@contextmanager
def _temp_viernulvier_model():
    class ViernulvierItem(models.Model):
        external_id = models.CharField(max_length=255, unique=True)
        payload = models.JSONField()

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
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
        assert url.endswith("/venues")
        response = Mock(ok=True, status_code=200)
        response.json.return_value = []
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    assert viernulvier.fetch_viernulvier(endpoint="/venues") == []


def test_fetch_raises_on_unexpected_payload(monkeypatch):
    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    def fake_get(url, headers, timeout):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"foo": "bar"}
        return response

    monkeypatch.setattr(viernulvier.requests, "get", fake_get)

    with pytest.raises(viernulvier.ScraperError):
        viernulvier.fetch_viernulvier(endpoint="/events")


def test_default_transform_uses_id():
    item = {"id": 123, "title": "A"}
    data = viernulvier.default_transform(item)

    assert data["external_id"] == "123"
    assert data["payload"]["title"] == "A"


def test_default_transform_allows_zero_id():
    item = {"id": 0, "title": "Zero"}
    data = viernulvier.default_transform(item)

    assert data["external_id"] == "0"


def test_default_transform_uses_uuid_when_no_id():
    """Test that uuid is used as external_id when id is not present."""
    item = {"uuid": "abc-123", "title": "A"}
    data = viernulvier.default_transform(item)

    assert data["external_id"] == "abc-123"
    assert data["payload"]["title"] == "A"


def test_default_transform_uses_slug_when_no_id_or_uuid():
    """Test that slug is used as external_id when id and uuid are not present."""
    item = {"slug": "my-event", "title": "A"}
    data = viernulvier.default_transform(item)

    assert data["external_id"] == "my-event"
    assert data["payload"]["title"] == "A"


def test_default_transform_raises_on_non_dict():
    """Test that default_transform raises ScraperError for non-dict input."""
    with pytest.raises(viernulvier.ScraperError, match="Invalid item type"):
        viernulvier.default_transform("not a dict")

    with pytest.raises(viernulvier.ScraperError, match="Invalid item type"):
        viernulvier.default_transform(123)

    with pytest.raises(viernulvier.ScraperError, match="Invalid item type"):
        viernulvier.default_transform([])


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_persists_items(monkeypatch):
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 2
        assert ViernulvierItem.objects.count() == 2


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_updates_existing_item(monkeypatch):
    with _temp_viernulvier_model() as ViernulvierItem:
        ViernulvierItem.objects.create(external_id="1", payload={"title": "old"})

        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "new"}],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert ViernulvierItem.objects.get(external_id="1").payload["title"] == "new"


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_items_without_external_id(monkeypatch, caplog):
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"title": "no id"}],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Skipping item without external_id" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_logs_info_on_empty_response(monkeypatch, caplog):
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(viernulvier, "fetch_viernulvier", lambda endpoint="/events": [])

        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 0
        assert any("Viernulvier sync finished" in r.message and "Saved=0" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_uses_custom_transform(monkeypatch):
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"custom_id": "x-1", "name": "X"}],
        )

        def custom_transform(item):
            return {"external_id": item["custom_id"], "payload": {"name": item["name"]}}

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, endpoint="/events", transform=custom_transform
        )

        assert count == 1
        obj = ViernulvierItem.objects.get(external_id="x-1")
        assert obj.payload == {"name": "X"}


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_handles_special_chars_and_nulls(monkeypatch):
    with _temp_viernulvier_model() as ViernulvierItem:
        payload = {"id": 9, "title": "Café 🎭", "desc": None}
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [payload],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        obj = ViernulvierItem.objects.get(external_id="9")
        assert obj.payload["title"] == "Café 🎭"
        assert obj.payload["desc"] is None


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_handles_large_payload(monkeypatch):
    with _temp_viernulvier_model() as ViernulvierItem:
        items = [{"id": i, "title": f"T{i}"} for i in range(50)]
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": items,
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 50
        assert ViernulvierItem.objects.count() == 50


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_logs_exact_message_format(monkeypatch, caplog):
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}],
        )

        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        assert any(
            "Viernulvier sync finished" in r.message and "Saved=1" in r.message and "Errors=0" in r.message
            for r in caplog.records
        )


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_duplicate_external_ids_in_batch(monkeypatch, caplog):
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"id": 1, "title": "B"}],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert any("Duplicate external_id in batch" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_when_transform_missing_external_id(monkeypatch, caplog):
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}],
        )

        def bad_transform(_item):
            return {"payload": {"title": "A"}}

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, endpoint="/events", transform=bad_transform
        )

        assert count == 0
        assert any("Skipping item without external_id" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_empty_string_external_id(monkeypatch, caplog):
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": "", "title": "A"}],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Skipping item without external_id" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_on_integrity_error(monkeypatch, caplog):
    """Test that sync continues processing other items when one fails with IntegrityError."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}],
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
def test_sync_continues_on_transform_exception(monkeypatch, caplog):
    """Test that sync continues when transform fails for one item."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}],
        )

        call_count = [0]

        def bad_transform(item):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("bad transform")
            return viernulvier.default_transform(item)

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, endpoint="/events", transform=bad_transform
        )

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert any("Unexpected error" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_on_transform_non_dict(monkeypatch, caplog):
    """Test that sync continues when transform returns non-dict for one item."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}],
        )

        call_count = [0]

        def bad_transform(item):
            call_count[0] += 1
            if call_count[0] == 1:
                return "not-a-dict"
            return viernulvier.default_transform(item)

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, endpoint="/events", transform=bad_transform
        )

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert any("Invalid transform output" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_on_transform_missing_payload(monkeypatch, caplog):
    """Test that sync continues when transform returns dict without payload."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}],
        )

        call_count = [0]

        def bad_transform(item):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"external_id": "1"}
            return viernulvier.default_transform(item)

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(
            ViernulvierItem, endpoint="/events", transform=bad_transform
        )

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert any("Invalid transform output" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_on_database_error(monkeypatch, caplog):
    """Test that sync continues processing when database error occurs for one item."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}],
        )

        call_count = [0]
        original_update_or_create = ViernulvierItem.objects.update_or_create

        def boom_once(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise DatabaseError("generic db error")
            return original_update_or_create(*args, **kwargs)

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", boom_once)

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert any("Database error" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_on_field_error(monkeypatch, caplog):
    """Test that sync continues when field error occurs for one item."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}],
        )

        call_count = [0]
        original_update_or_create = ViernulvierItem.objects.update_or_create

        def boom_once(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise FieldError("unknown field")
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
    """Test that sync returns 0 when all items fail."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}],
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
            lambda endpoint="/events": [{"id": 1, "title": "A"}, {"title": "no id"}],
        )

        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        assert any("Viernulvier sync finished" in r.message and "Saved=1" in r.message and "Errors=1" in r.message for r in info_records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_when_item_is_not_dict(monkeypatch, caplog):
    """Test that sync continues when fetch returns non-dict items in the list."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda endpoint="/events": ["not-a-dict", {"id": 2, "title": "B"}],
        )

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        # Check that an error was logged for the non-dict item
        assert any("Unexpected error" in r.message for r in caplog.records)
        # Verify the exception contains the ScraperError about invalid item type
        assert any(r.exc_info and "Invalid item type" in str(r.exc_info[1]) for r in caplog.records)
