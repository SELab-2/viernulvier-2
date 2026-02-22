"""Tests for Viernulvier scraper fetch, error handling, and persistence."""
from contextlib import contextmanager
import logging

import pytest
from unittest.mock import Mock

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
        assert any("Synced 0 items" in r.message for r in caplog.records)
