"""Shared helpers for crop scraper sync tests."""

from __future__ import annotations

from unittest.mock import Mock

from apps.imports.scrapers import viernulvier
from apps.media_library import models as media_models


def _patch_crop_dependencies(
    monkeypatch,
    *,
    foto_items: list,
    fetch_results: dict | None = None,
    download_result: bytes | None = b"image-data",
    synced_crop_names: set | None = None,
    generate_filename_result: str = "media/crops/item_hd_ready.jpg",
    storage_save_result: str = "media/crops/item_hd_ready.jpg",
):
    """
    Patch all external dependencies of sync_media_item_crops in one call.

    fetch_results: maps external_id -> (item_data, etag) tuple.
    download_result: bytes returned by _download_image (None simulates failure).
    """
    if synced_crop_names is None:
        synced_crop_names = {"hd_ready", "FE3_header"}

    # --- MediaItem queryset ---
    mock_qs = Mock()
    mock_qs.values.return_value = foto_items
    monkeypatch.setattr(
        media_models.MediaItem.objects,
        "filter",
        lambda **_kw: mock_qs,
    )

    # --- _build_session (returns a dummy session; _download_image is patched separately) ---
    monkeypatch.setattr(viernulvier, "_build_session", Mock)

    # --- _fetch_with_retry ---
    def fake_fetch(session, url, etag=None, params=None):
        if fetch_results and url in fetch_results:
            return fetch_results[url]
        # Default: single crop
        return (
            {
                "crops": [
                    {"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"},
                ]
            },
            None,
        )

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch)

    # --- _download_image ---
    monkeypatch.setattr(viernulvier, "_download_image", lambda _session, _url: download_result)

    # --- MediaItemCrop ---
    mock_crop_model = Mock()
    mock_crop_model.SYNCED_CROP_NAMES = synced_crop_names

    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = generate_filename_result
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = storage_save_result
    mock_crop_model._meta = Mock()
    mock_crop_model._meta.get_field.return_value = mock_image_field
    mock_crop_model.objects.update_or_create.return_value = (Mock(), True)

    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_model)

    return mock_crop_model
