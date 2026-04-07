"""Input-processing and filtering tests for `sync_media_item_crops`."""

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
def test_sync_crops_no_foto_items_returns_zero_and_logs_success(monkeypatch) -> None:
    """No foto items should return zero and write a successful all-zero import log."""
    mock_qs = Mock()
    mock_qs.values.return_value = []
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)

    result = sync_media_item_crops()

    assert result == 0
    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_total == 0
    assert log.records_imported == 0
    assert log.records_failed == 0


@pytest.mark.django_db
@pytest.mark.parametrize("external_id", ["", None])
def test_sync_crops_missing_external_id_skipped(monkeypatch, caplog, external_id) -> None:
    """Rows without an external_id value are skipped and logged as warnings."""
    _patch_crop_dependencies(monkeypatch, foto_items=[{"pk": 1, "external_id": external_id}])

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("no external_id" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_fetch_failure_logged_as_error(monkeypatch, caplog) -> None:
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
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(viernulvier, "_fetch_with_retry", lambda *_a, **_kw: (None, None))

    result = sync_media_item_crops()

    assert result == 0


@pytest.mark.django_db
def test_sync_crops_non_list_crops_field_skipped(monkeypatch, caplog) -> None:
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
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    result = sync_media_item_crops()

    assert result == 0
    mock_crop_cls.objects.update_or_create.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_crop_missing_url_warns_and_skips(monkeypatch, caplog) -> None:
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
def test_sync_crops_crop_dict_not_dict_skipped(monkeypatch) -> None:
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
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

    assert result == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("external_id", "expected_url"),
    [
        (
            "https://www.viernulvier.gent/api/v1/media/items/99",
            "https://www.viernulvier.gent/api/v1/media/items/99",
        ),
        ("/api/v1/media/items/10", "https://www.viernulvier.gent/api/v1/media/items/10"),
    ],
)
def test_sync_crops_external_id_url_resolution(monkeypatch, external_id, expected_url) -> None:
    captured_urls = []
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": external_id}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)

    def fake_fetch(_session, url, **_kw):
        captured_urls.append(url)
        return ({"crops": []}, None)

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch)

    sync_media_item_crops()

    assert captured_urls[0] == expected_url


@pytest.mark.django_db
def test_sync_crops_multiple_items_and_crops_counted_correctly(monkeypatch) -> None:
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

    assert result == 4


@pytest.mark.django_db
def test_sync_crops_on_progress_called_per_item(monkeypatch) -> None:
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

    assert calls == [(1, 2), (2, 2)]

