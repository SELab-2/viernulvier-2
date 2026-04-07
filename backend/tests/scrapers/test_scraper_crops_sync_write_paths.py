"""Write-path, dry-run, and persistence tests for `sync_media_item_crops`."""

from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import sync_media_item_crops
from apps.media_library import models as media_models
from tests.scrapers._scraper_crops_helpers import _patch_crop_dependencies


@pytest.mark.django_db
def test_sync_crops_download_failure_counted_as_error(monkeypatch, caplog) -> None:
    mock_crop_cls = _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=None,
    )

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    mock_crop_cls.objects.update_or_create.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_successful_save_returns_count(monkeypatch) -> None:
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=b"image-bytes",
    )

    result = sync_media_item_crops()

    assert result == 1


@pytest.mark.django_db
def test_sync_crops_dry_run_does_not_write(monkeypatch) -> None:
    mock_crop_cls = _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    result = sync_media_item_crops(dry_run=True)

    assert result == 1
    mock_crop_cls.objects.update_or_create.assert_not_called()
    mock_crop_cls._meta.get_field.return_value.storage.save.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_dry_run_logs_intended_save(monkeypatch, caplog) -> None:
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    sync_media_item_crops(dry_run=True)

    assert any("[DRY RUN]" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_save_exception_counted_as_error(monkeypatch, caplog) -> None:
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
def test_sync_crops_logs_created_or_updated_debug(monkeypatch, caplog) -> None:
    mock_crop_cls = _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), False)

    caplog.set_level(logging.DEBUG, logger=viernulvier.logger.name)
    sync_media_item_crops()

    assert any("Updated" in r.message or "Created" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_storage_save_called_with_image_bytes(monkeypatch) -> None:
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

