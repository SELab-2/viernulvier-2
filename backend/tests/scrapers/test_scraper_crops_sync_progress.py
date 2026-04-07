"""Progress callback tests for `sync_media_item_crops`."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import ScraperError, sync_media_item_crops
from apps.media_library import models as media_models


@pytest.mark.django_db
def test_on_progress_called_when_external_id_missing(monkeypatch) -> None:
    """on_progress is invoked even when an item is skipped due to missing external_id."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": ""}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 1)]


@pytest.mark.django_db
def test_on_progress_called_after_fetch_scraper_error(monkeypatch) -> None:
    """on_progress is invoked after a ScraperError on the individual item fetch."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (_ for _ in ()).throw(ScraperError("boom")),
    )

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 1)]


@pytest.mark.django_db
def test_on_progress_called_after_304_not_modified(monkeypatch) -> None:
    """on_progress is invoked when the item fetch returns None (304 Not Modified)."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(viernulvier, "_fetch_with_retry", lambda *_a, **_kw: (None, None))

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 1)]


@pytest.mark.django_db
def test_on_progress_called_after_non_list_crops(monkeypatch) -> None:
    """on_progress is invoked when the crops field is not a list."""
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": "not-a-list"}, None),
    )

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 1)]


@pytest.mark.django_db
def test_on_progress_covers_all_four_early_exit_branches_in_one_run(monkeypatch) -> None:
    """Four items, each triggering a different early-exit; on_progress fired for all four."""
    mock_qs = Mock()
    mock_qs.values.return_value = [
        {"pk": 1, "external_id": ""},  # branch: no external_id
        {"pk": 2, "external_id": "/api/v1/media/items/2"},  # branch: ScraperError
        {"pk": 3, "external_id": "/api/v1/media/items/3"},  # branch: 304 (None)
        {"pk": 4, "external_id": "/api/v1/media/items/4"},  # branch: non-list crops
    ]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", Mock)

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 4), (2, 4), (3, 4), (4, 4)]
