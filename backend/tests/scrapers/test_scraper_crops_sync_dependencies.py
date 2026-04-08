"""Dependency-resolution tests for `sync_media_item_crops`."""

from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest

from apps.import_log.models import ImportLog
from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import sync_media_item_crops
from apps.media_library import models as media_models


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
