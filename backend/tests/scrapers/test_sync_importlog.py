"""
Tests for Viernulvier ImportLog integration, sync options (dry_run, on_progress, etc).
"""

from __future__ import annotations

import logging
from typing import Never

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test.utils import isolate_apps
import pytest

from apps.events.models import Event, EventPrice
from apps.import_log.models import ImportLog
from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    FKCache,
    M2MConfig,
    ModelSyncConfig,
    TranslationConfig,
    _sync_m2m,
    _sync_all_translations,
    sync_viernulvier,
)
from apps.pricing.models import PriceRank
from apps.productions.models import Production

from tests.scrapers.conftest import _temp_viernulvier_model, _PassThroughConfig


# ---------------------------------------------------------------------------
# sync_viernulvier - dry_run / on_progress / item_filter / MAX_ERROR_MESSAGES
# ---------------------------------------------------------------------------


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_dry_run_does_not_write_to_db(monkeypatch) -> None:
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
def test_sync_on_progress_called_with_cumulative_counts(monkeypatch) -> None:
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
def test_sync_dry_run_on_progress_also_called(monkeypatch) -> None:
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
def test_sync_item_filter_excludes_items(monkeypatch) -> None:
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
def test_sync_max_error_messages_capped(monkeypatch) -> None:
    """Error messages list is capped at MAX_ERROR_MESSAGES."""
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
def test_sync_etag_cache_passed_to_fetch(monkeypatch) -> None:
    """sync_viernulvier passes the same etag_cache object to fetch_viernulvier."""
    with _temp_viernulvier_model() as M:
        captured = {}
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **kwargs: captured.update({"etag_cache": kwargs.get("etag_cache")}) or [],
        )
        shared_cache = {"key": "val"}
        sync_viernulvier(M, _PassThroughConfig(), endpoint="/e", etag_cache=shared_cache)
        assert captured["etag_cache"] is shared_cache


# ---------------------------------------------------------------------------
# ImportLog integration
# ---------------------------------------------------------------------------


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_creates_import_log_on_success(monkeypatch) -> None:
    """Successful sync creates a SUCCESS ImportLog with correct counters."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_creates_import_log_with_params_in_source(monkeypatch) -> None:
    """Params are included (sorted) in the ImportLog source field."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_creates_import_log_on_partial_success(monkeypatch) -> None:
    """Some items failing creates a PARTIAL_SUCCESS ImportLog."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_creates_import_log_on_all_failures(monkeypatch) -> None:
    """All items failing creates a FAILED ImportLog."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_creates_import_log_on_fetch_exception(monkeypatch) -> None:
    """fetch_viernulvier raising an exception creates a FAILED ImportLog."""
    with _temp_viernulvier_model() as ViernulvierItem:

        def failing_fetch(endpoint="/events", params=None, etag_cache=None) -> Never:
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
def test_sync_creates_import_log_on_empty_response(monkeypatch) -> None:
    """Empty API response creates a SUCCESS ImportLog with all-zero counters."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [],
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
def test_sync_import_log_timestamps_are_sequential(monkeypatch) -> None:
    """finished_at >= started_at in the ImportLog."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
                {"@id": "https://example.com/1", "title": "Event A"},
            ],
        )

        viernulvier.sync_viernulvier(ViernulvierItem, _PassThroughConfig(), endpoint="/events")

        log = ImportLog.objects.first()
        assert log.finished_at >= log.started_at


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_import_log_tracks_multiple_syncs(monkeypatch) -> None:
    """Each sync call creates its own ImportLog entry."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_import_log_different_endpoints_tracked_separately(monkeypatch) -> None:
    """Different endpoints get separate ImportLog source values."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [
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
def test_sync_validation_error_formats_messages(monkeypatch) -> None:
    """ValidationError messages (per-field and __all__) are included in ImportLog."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [{"@id": "1", "title": "A"}],
        )

        def raise_validation(*_args, **_kwargs) -> Never:
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
def test_sync_database_error_branch(monkeypatch) -> None:
    """IntegrityError is caught and logged as a database error."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [{"@id": "1", "title": "A"}],
        )

        def raise_integrity(*_args, **_kwargs) -> Never:
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
def test_sync_unexpected_error_branch(monkeypatch) -> None:
    """Non-DB exceptions are caught and still finalize the ImportLog."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [{"@id": "1", "title": "A"}],
        )

        def raise_runtime(*_args, **_kwargs) -> Never:
            raise RuntimeError("unexpected crash")

        monkeypatch.setattr(ViernulvierItem.objects, "update_or_create", raise_runtime)

        saved = viernulvier.sync_viernulvier(ViernulvierItem, ModelSyncConfig(lookup_field="id"), endpoint="/events")

        assert saved == 0
        log = ImportLog.objects.first()
        assert "Unexpected error for 1: RuntimeError" in log.error_message
        assert log.records_total == 1
        assert log.records_failed == 1


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_calls_m2m_and_commits_savepoint(monkeypatch) -> None:
    """M2M sync is invoked and savepoint is committed on success."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [{"@id": "1", "title": "A"}],
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
def test_sync_executes_translations(monkeypatch) -> None:
    """_sync_all_translations is called when translation config is provided."""
    with _temp_viernulvier_model() as ViernulvierItem:
        monkeypatch.setattr(
            viernulvier,
            "fetch_viernulvier",
            lambda **__: [{"@id": "1", "title": "A"}],
        )

        called = {"translations": 0}

        def fake_sync_all_translations(*_args, **_kwargs) -> None:
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


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_sync_caches_external_id_after_create(monkeypatch) -> None:
    """After update_or_create, the object's external_id is stored in fk_cache."""

    from django.db import models, connection

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
            lambda **_: [{"@id": "ext-001", "title": "Cached Item"}],
        )

        captured_cache = {}

        original_set = FKCache.set

        def spy_set(self, model, ext_id, pk) -> None:
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

