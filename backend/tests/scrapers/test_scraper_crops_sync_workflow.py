"""Workflow tests for `sync_media_item_crops`."""

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
def test_sync_crops_no_foto_items_returns_zero(monkeypatch) -> None:
    """When there are no foto MediaItems, sync returns 0 immediately."""
    mock_qs = Mock()
    mock_qs.values.return_value = []
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)

    result = sync_media_item_crops()

    assert result == 0


@pytest.mark.django_db
def test_sync_crops_upsert_missing_media_item_resolves_gallery_id(monkeypatch) -> None:
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "fetch_viernulvier",
        lambda **_kw: [{"@id": "/api/v1/media/items/55", "type": "foto"}],
    )
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
            {
                "type": "foto",
                "gallery": "  /api/v1/media/galleries/77  ",
                "original_filename": "missing.jpg",
                "position": 0,
                "format": "jpg",
                "crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}],
            },
            None,
        ),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"img")

    gallery_qs = Mock()
    gallery_qs.values_list.return_value.first.return_value = 777
    gallery_filter = Mock(return_value=gallery_qs)
    monkeypatch.setattr(media_models.MediaGallery.objects, "filter", gallery_filter)

    media_upsert = Mock(return_value=(Mock(pk=4242), True))
    monkeypatch.setattr(media_models.MediaItem.objects, "update_or_create", media_upsert)

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

    result = sync_media_item_crops(params={"updated_at[after]": "2024-01-01T00:00:00+00:00"})

    assert result == 1
    gallery_filter.assert_called_once_with(external_id="/api/v1/media/galleries/77")
    gallery_qs.values_list.assert_called_once_with("pk", flat=True)
    assert media_upsert.call_args.kwargs["defaults"]["gallery_id"] == 777


@pytest.mark.django_db
def test_sync_crops_dry_run_logs_missing_media_item_upsert(monkeypatch, caplog) -> None:
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "fetch_viernulvier",
        lambda **_kw: [{"@id": "/api/v1/media/items/123", "type": "foto"}],
    )
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
            {
                "type": "foto",
                "crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}],
            },
            None,
        ),
    )

    media_upsert = Mock()
    monkeypatch.setattr(media_models.MediaItem.objects, "update_or_create", media_upsert)

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    result = sync_media_item_crops(
        dry_run=True,
        params={"updated_at[after]": "2024-01-01T00:00:00+00:00"},
    )

    assert result == 0
    media_upsert.assert_not_called()
    assert any(
        "[DRY RUN] Would upsert missing MediaItem for crop sync: /api/v1/media/items/123" in r.message
        for r in caplog.records
    )


@pytest.mark.django_db
def test_sync_crops_unresolved_dependency_calls_on_progress(monkeypatch) -> None:
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "fetch_viernulvier",
        lambda **_kw: [{"@id": "/api/v1/media/items/124", "type": "foto"}],
    )
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"type": "foto", "crops": []}, None),
    )

    calls = []
    result = sync_media_item_crops(
        dry_run=True,
        params={"updated_at[after]": "2024-01-01T00:00:00+00:00"},
        on_progress=lambda idx, total: calls.append((idx, total)),
    )

    assert result == 0
    assert calls == [(1, 1)]


@pytest.mark.django_db
def test_sync_crops_unresolved_media_item_dependency_after_upsert(monkeypatch, caplog) -> None:
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "fetch_viernulvier",
        lambda **_kw: [{"@id": "/api/v1/media/items/999", "type": "foto"}],
    )
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
            {
                "type": "foto",
                "original_filename": "missing.jpg",
                "position": 0,
                "format": "jpg",
                "crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}],
            },
            None,
        ),
    )

    media_upsert = Mock(return_value=(Mock(pk=None), True))
    monkeypatch.setattr(media_models.MediaItem.objects, "update_or_create", media_upsert)

    download_image = Mock(return_value=b"img")
    monkeypatch.setattr(viernulvier, "_download_image", download_image)

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = sync_media_item_crops(params={"updated_at[after]": "2024-01-01T00:00:00+00:00"})

    assert result == 0
    media_upsert.assert_called_once()
    download_image.assert_not_called()
    assert any("MediaItem dependency unresolved for crop sync: /api/v1/media/items/999" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_missing_media_item_upsert_exception_is_logged_and_recorded(monkeypatch, caplog) -> None:
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "fetch_viernulvier",
        lambda **_kw: [{"@id": "/api/v1/media/items/321", "type": "foto"}],
    )
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
            {
                "type": "foto",
                "original_filename": "broken.jpg",
                "position": 0,
                "format": "jpg",
                "crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}],
            },
            None,
        ),
    )

    media_upsert = Mock(side_effect=RuntimeError("upsert exploded"))
    monkeypatch.setattr(media_models.MediaItem.objects, "update_or_create", media_upsert)

    on_progress = Mock()
    download_image = Mock(return_value=b"img")
    monkeypatch.setattr(viernulvier, "_download_image", download_image)

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = sync_media_item_crops(
        params={"updated_at[after]": "2024-01-01T00:00:00+00:00"},
        on_progress=on_progress,
    )

    assert result == 0
    media_upsert.assert_called_once()
    download_image.assert_not_called()
    on_progress.assert_called_once_with(1, 1)
    assert any(
        "Failed to upsert MediaItem dependency for crop sync (/api/v1/media/items/321)" in r.message for r in caplog.records
    )

    log = ImportLog.objects.latest("started_at")
    assert "Missing MediaItem upsert failed for /api/v1/media/items/321" in (log.error_message or "")


@pytest.mark.django_db
def test_sync_crops_no_foto_items_creates_success_import_log(monkeypatch) -> None:
    """Empty foto list creates a SUCCESS ImportLog with all-zero counters."""
    mock_qs = Mock()
    mock_qs.values.return_value = []
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_total == 0
    assert log.records_imported == 0
    assert log.records_failed == 0


@pytest.mark.django_db
def test_sync_crops_item_without_external_id_skipped(monkeypatch, caplog) -> None:
    """MediaItem rows with no external_id are skipped and counted as errors."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": ""}],
    )

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("no external_id" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_none_external_id_skipped(monkeypatch, caplog) -> None:
    """MediaItem rows with external_id=None are also skipped."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": None}],
    )

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("no external_id" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_fetch_failure_logged_as_error(monkeypatch, caplog) -> None:
    """A ScraperError during individual item fetch is logged and counted as error."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (_ for _ in ()).throw(ScraperError("API down")),
    )

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("Failed to fetch media item" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_304_not_modified_skips_item(monkeypatch) -> None:
    """A 304 (fetch returns None) means no crops to process - item is silently skipped."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(viernulvier, "_fetch_with_retry", lambda *_a, **_kw: (None, None))

    result = sync_media_item_crops()

    assert result == 0


@pytest.mark.django_db
def test_sync_crops_non_list_crops_field_skipped(monkeypatch, caplog) -> None:
    """When API crops field is not a list, the item is silently skipped."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": "not-a-list"}, None),
    )

    caplog.set_level(logging.DEBUG, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("Unexpected crops format" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_crop_not_in_wanted_set_skipped(monkeypatch) -> None:
    """Crop names not in SYNCED_CROP_NAMES are silently ignored."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "unknown_variant", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_qs2 = Mock()
    mock_qs2.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]

    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    result = sync_media_item_crops()

    assert result == 0
    mock_crop_cls.objects.update_or_create.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_crop_missing_url_warns_and_skips(monkeypatch, caplog) -> None:
    """A crop dict without a url key is skipped with a warning."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": ""}]}, None),
    )

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}

    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("has no URL" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_download_failure_counted_as_error(monkeypatch, caplog) -> None:
    """When _download_image returns None the crop is counted as an error."""
    mock_crop_cls = _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=None,  # simulate download failure
    )

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    mock_crop_cls.objects.update_or_create.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_successful_save_returns_count(monkeypatch) -> None:
    """A successful crop save increments the saved counter."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=b"image-bytes",
    )

    result = sync_media_item_crops()

    assert result == 1


@pytest.mark.django_db
def test_sync_crops_creates_import_log_success(monkeypatch) -> None:
    """A fully successful run produces a SUCCESS ImportLog."""
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
    """One crop saved + one failed produces a PARTIAL_SUCCESS ImportLog."""
    # Two items; first succeeds, second has bad external_id (empty -> error)
    mock_qs = Mock()
    mock_qs.values.return_value = [
        {"pk": 1, "external_id": "/api/v1/media/items/1"},
        {"pk": 2, "external_id": ""},  # will be skipped as error
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
    """All items failing produces a FAILED ImportLog."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=None,  # download always fails
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.FAILED
    assert log.records_imported == 0
    assert log.records_failed == 1


@pytest.mark.django_db
def test_sync_crops_dry_run_does_not_write(monkeypatch) -> None:
    """dry_run=True logs intentions but writes neither images nor DB rows."""
    mock_crop_cls = _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    result = sync_media_item_crops(dry_run=True)

    assert result == 1  # "would save"
    mock_crop_cls.objects.update_or_create.assert_not_called()
    mock_crop_cls._meta.get_field.return_value.storage.save.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_dry_run_logs_intended_save(monkeypatch, caplog) -> None:
    """dry_run mode logs what would be saved for each crop."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    sync_media_item_crops(dry_run=True)

    assert any("[DRY RUN]" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_on_progress_called_per_item(monkeypatch) -> None:
    """on_progress callback receives (idx, total) for every processed item."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[
            {"pk": 1, "external_id": "/api/v1/media/items/1"},
            {"pk": 2, "external_id": "/api/v1/media/items/2"},
        ],
        fetch_results={
            "https://www.viernulvier.gent/api/v1/media/items/1": (
                {"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/a.jpg"}]},
                None,
            ),
            "https://www.viernulvier.gent/api/v1/media/items/2": (
                {"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/b.jpg"}]},
                None,
            ),
        },
    )

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert len(calls) == 2
    assert calls[0] == (1, 2)
    assert calls[1] == (2, 2)


@pytest.mark.django_db
def test_sync_crops_save_exception_counted_as_error(monkeypatch, caplog) -> None:
    """An unexpected exception during update_or_create is caught and counted as error."""
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

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("Error saving crop" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_save_exception_added_to_error_messages(monkeypatch) -> None:
    """Exceptions during save are captured in the ImportLog error_message."""
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
def test_sync_crops_external_id_as_absolute_url_used_directly(monkeypatch) -> None:
    """external_id already starting with http is used as-is (not prefixed)."""
    captured_urls = []
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "https://www.viernulvier.gent/api/v1/media/items/99"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)

    def fake_fetch(session, url, **_kw):
        captured_urls.append(url)
        return ({"crops": []}, None)

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch)

    sync_media_item_crops()

    assert captured_urls[0] == "https://www.viernulvier.gent/api/v1/media/items/99"


@pytest.mark.django_db
def test_sync_crops_external_id_as_relative_path_prefixed_with_base_domain(monkeypatch) -> None:
    """Relative external_id is prefixed with BASE_DOMAIN before fetching."""
    captured_urls = []
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/10"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)

    def fake_fetch(session, url, **_kw):
        captured_urls.append(url)
        return ({"crops": []}, None)

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch)

    sync_media_item_crops()

    assert captured_urls[0].startswith("https://")
    assert "/api/v1/media/items/10" in captured_urls[0]


@pytest.mark.django_db
def test_sync_crops_multiple_items_and_crops_counted_correctly(monkeypatch) -> None:
    """Two items, each with two wanted crops -> four total crops saved."""
    items_data = [
        {"pk": 1, "external_id": "/api/v1/media/items/1"},
        {"pk": 2, "external_id": "/api/v1/media/items/2"},
    ]
    mock_qs = Mock()
    mock_qs.values.return_value = items_data
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
            {
                "crops": [
                    {"name": "hd_ready", "url": "https://cdn.example.com/hd.jpg"},
                    {"name": "FE3_header", "url": "https://cdn.example.com/fe3.jpg"},
                ]
            },
            None,
        ),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"img")

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready", "FE3_header"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "crops/img.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), True)
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    result = sync_media_item_crops()

    assert result == 4  # 2 items x 2 crops each


@pytest.mark.django_db
def test_sync_crops_crop_dict_not_dict_skipped(monkeypatch) -> None:
    """Non-dict entries inside the crops list are silently ignored."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
            # Mix of valid and non-dict crops
            {
                "crops": [
                    "not-a-dict",
                    42,
                    None,
                    {"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"},
                ]
            },
            None,
        ),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"img")

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

    result = sync_media_item_crops()

    assert result == 1  # Only the valid dict crop was processed


@pytest.mark.django_db
def test_sync_crops_logs_created_or_updated_debug(monkeypatch, caplog) -> None:
    """Created vs Updated status is logged at DEBUG level."""
    mock_crop_cls = _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), False)  # updated

    caplog.set_level(logging.DEBUG, logger=viernulvier.logger.name)
    sync_media_item_crops()

    assert any("Updated" in r.message or "Created" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_import_log_source_is_correct(monkeypatch) -> None:
    """The ImportLog source is set to 'viernulvier:media_item_crops'."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[],
    )
    mock_qs = Mock()
    mock_qs.values.return_value = []
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.source == "viernulvier:media_item_crops"


@pytest.mark.django_db
def test_sync_crops_import_log_timestamps_sequential(monkeypatch) -> None:
    """finished_at >= started_at in the ImportLog."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.finished_at >= log.started_at


@pytest.mark.django_db
def test_sync_crops_fetch_error_message_captured_in_import_log(monkeypatch) -> None:
    """ScraperError messages during fetch are included in the ImportLog error_message."""
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
def test_sync_crops_summary_logged_on_completion(monkeypatch, caplog) -> None:
    """'Crop sync complete' with saved= and errors= is logged after running."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    sync_media_item_crops()

    assert any("Crop sync complete" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_dry_run_summary_has_dry_run_suffix(monkeypatch, caplog) -> None:
    """The completion log includes '[DRY RUN]' suffix when dry_run=True."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    sync_media_item_crops(dry_run=True)

    assert any("[DRY RUN]" in r.message and "Crop sync complete" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_download_error_message_captured(monkeypatch) -> None:
    """Download failures are captured in the ImportLog error_message."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=None,
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert "Download failed" in (log.error_message or "")


@pytest.mark.django_db
def test_sync_crops_storage_save_called_with_image_bytes(monkeypatch) -> None:
    """The storage backend's save() is called with a ContentFile wrapping the downloaded bytes."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"raw-pixels")

    storage_save_calls = []

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_storage = Mock()

    def capture_save(upload_name, content_file):
        storage_save_calls.append((upload_name, content_file.read()))
        return upload_name

    mock_storage.save.side_effect = capture_save
    mock_image_field.storage = mock_storage
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), True)
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    sync_media_item_crops()

    assert storage_save_calls
    assert storage_save_calls[0][1] == b"raw-pixels"


@pytest.mark.django_db
def test_sync_crops_update_or_create_receives_correct_kwargs(monkeypatch) -> None:
    """update_or_create is called with media_item_id, name, and defaults={image:...}."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 42, "external_id": "/api/v1/media/items/42"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"data")

    uoc_calls = []

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "saved/path.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field

    def capture_uoc(**kwargs):
        uoc_calls.append(kwargs)
        return Mock(), True

    mock_crop_cls.objects.update_or_create.side_effect = capture_uoc
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    sync_media_item_crops()

    assert uoc_calls
    call_kw = uoc_calls[0]
    assert call_kw["media_item_id"] == 42
    assert call_kw["name"] == "hd_ready"
    assert call_kw["defaults"] == {"image": "saved/path.jpg"}
