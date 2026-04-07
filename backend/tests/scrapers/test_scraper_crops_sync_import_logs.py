"""ImportLog and completion-summary tests for `sync_media_item_crops`."""

from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest

from apps.import_log.models import ImportLog
from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import ScraperError, sync_media_item_crops
from apps.media_library import models as media_models
from tests.scrapers._scraper_crops_helpers import _patch_crop_dependencies


@pytest.mark.django_db
def test_sync_crops_creates_import_log_success(monkeypatch) -> None:
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_imported == 1
    assert log.records_failed == 0


@pytest.mark.django_db
def test_sync_crops_partial_success_import_log(monkeypatch) -> None:
    mock_qs = Mock()
    mock_qs.values.return_value = [
        {"pk": 1, "external_id": "/api/v1/media/items/1"},
        {"pk": 2, "external_id": ""},
    ]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"data")

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "crops/img.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), True)
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.PARTIAL_SUCCESS
    assert log.records_imported == 1
    assert log.records_failed == 1


@pytest.mark.django_db
def test_sync_crops_all_failed_import_log(monkeypatch) -> None:
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=None,
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.FAILED
    assert log.records_imported == 0
    assert log.records_failed == 1


@pytest.mark.django_db
def test_sync_crops_import_log_source_is_correct(monkeypatch) -> None:
    mock_qs = Mock()
    mock_qs.values.return_value = []
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.source == "viernulvier:media_item_crops"


@pytest.mark.django_db
def test_sync_crops_import_log_timestamps_sequential(monkeypatch) -> None:
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.finished_at >= log.started_at


@pytest.mark.django_db
def test_sync_crops_fetch_error_message_captured_in_import_log(monkeypatch) -> None:
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (_ for _ in ()).throw(ScraperError("network timeout")),
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert "network timeout" in (log.error_message or "")


@pytest.mark.django_db
def test_sync_crops_download_error_message_captured(monkeypatch) -> None:
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=None,
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert "Download failed" in (log.error_message or "")


@pytest.mark.django_db
def test_sync_crops_save_exception_added_to_error_messages(monkeypatch) -> None:
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"data")

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "crops/img.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.side_effect = RuntimeError("db crash")
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.error_message is not None
    assert "db crash" in log.error_message


@pytest.mark.django_db
def test_sync_crops_summary_logged_on_completion(monkeypatch, caplog) -> None:
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    sync_media_item_crops()

    assert any("Crop sync complete" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_dry_run_summary_has_dry_run_suffix(monkeypatch, caplog) -> None:
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    sync_media_item_crops(dry_run=True)

    assert any("[DRY RUN]" in r.message and "Crop sync complete" in r.message for r in caplog.records)

