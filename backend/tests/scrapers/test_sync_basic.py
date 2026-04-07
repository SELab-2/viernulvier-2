"""
Tests for Viernulvier basic sync persistence and item handling.
"""

from __future__ import annotations

import logging

from django.db import IntegrityError
from django.test.utils import isolate_apps
import pytest

from apps.imports.scrapers import viernulvier
from tests.scrapers.conftest import _PassThroughConfig, _temp_viernulvier_model


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_persists_items(monkeypatch) -> None:
    """Items returned by fetch are persisted to the database."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
                {"@id": "https://example.com/1", "title": "A"},
                {"@id": "https://example.com/2", "title": "B"},
            ],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 2
        assert ViernulvierItem.objects.count() == 2


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_updates_existing_item(monkeypatch) -> None:
    """Existing records are updated, not duplicated."""
    with _temp_viernulvier_model() as ViernulvierItem:
        ViernulvierItem.objects.create(id="https://example.com/1", title="old")

        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [{"@id": "https://example.com/1", "title": "new"}],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
        assert ViernulvierItem.objects.get(id="https://example.com/1").title == "new"


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_items_without_id(monkeypatch, caplog) -> None:
    """Items with no @id are skipped and a warning is logged."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [{"title": "no id"}],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Missing '@id' in item:" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_empty_string_id(monkeypatch, caplog) -> None:
    """An empty string @id is treated the same as missing."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [{"@id": "", "title": "A"}],
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0
        assert any("Missing '@id' in item:" in r.message for r in caplog.records)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_skips_duplicate_ids_in_batch(monkeypatch, caplog) -> None:
    """Duplicate @id values within the same batch are deduplicated."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_handles_special_chars_and_nulls(monkeypatch) -> None:
    """Unicode chars are stored correctly; None values are stored as NULL."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_handles_large_payload(monkeypatch) -> None:
    """50-item batch is fully persisted."""
    with _temp_viernulvier_model() as ViernulvierItem:
        items = [{"@id": f"https://example.com/{i}", "title": f"T{i}"} for i in range(50)]
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: items,
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 50
        assert ViernulvierItem.objects.count() == 50


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_continues_on_database_errors(monkeypatch, caplog) -> None:
    """One item failing with IntegrityError does not abort the rest of the batch."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_all_items_fail_returns_zero(monkeypatch) -> None:
    """All items failing returns 0 saved."""
    from typing import Never

    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
                {"@id": "https://example.com/1", "title": "A"},
                {"@id": "https://example.com/2", "title": "B"},
            ],
        )

        def boom(*_args, **_kwargs) -> Never:
            raise IntegrityError("boom")

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", boom)

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 0
        assert ViernulvierItem.objects.count() == 0


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_logs_finish_message_with_saved_and_error_count(monkeypatch, caplog) -> None:
    """Sync completion log contains saved= and errors= counts."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_continues_when_item_is_not_dict(monkeypatch, caplog) -> None:
    """Non-dict items in the fetch result are logged as errors and skipped."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_passes_params_to_fetch(monkeypatch) -> None:
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
def test_sync_without_params_still_works(monkeypatch) -> None:
    """Backward compatibility: sync works when params is omitted."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
                {"@id": "https://example.com/1", "title": "Item"},
            ],
        )

        count = viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        assert count == 1
        assert ViernulvierItem.objects.count() == 1
