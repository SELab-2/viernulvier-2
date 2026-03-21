"""Tests for gallery->item link synchronization in the Viernulvier scraper."""

from __future__ import annotations

import pytest

from apps.imports.scrapers.viernulvier import sync_media_item_gallery_links
from apps.import_log.models import ImportLog
from apps.media_library.models import MediaGalleryItem
from tests.factories.media_library import MediaGalleryFactory, MediaItemFactory


@pytest.mark.django_db
def test_sync_media_item_gallery_links_updates_gallery_and_position(monkeypatch):
    gallery_a = MediaGalleryFactory.create(external_id="/api/v1/media/galleries/1")
    gallery_b = MediaGalleryFactory.create(external_id="/api/v1/media/galleries/2")

    item_1 = MediaItemFactory.create(external_id="/api/v1/media/items/10", gallery=None, position=99)
    item_2 = MediaItemFactory.create(external_id="/api/v1/media/items/11", gallery=None, position=99)
    item_3 = MediaItemFactory.create(external_id="/api/v1/media/items/12", gallery=gallery_a, position=8)

    payload = [
        {
            "@id": "/api/v1/media/galleries/1",
            "items": ["/api/v1/media/items/10", "/api/v1/media/items/11"],
        },
        {
            "@id": "/api/v1/media/galleries/2",
            "items": ["/api/v1/media/items/12"],
        },
    ]
    monkeypatch.setattr("apps.imports.scrapers.viernulvier.fetch_viernulvier", lambda **_: payload)

    changed = sync_media_item_gallery_links()

    item_1.refresh_from_db()
    item_2.refresh_from_db()
    item_3.refresh_from_db()
    links = list(
        MediaGalleryItem.objects.order_by("gallery_id", "position").values_list("gallery_id", "media_item_id", "position")
    )

    assert changed == 3
    assert item_1.gallery_id == gallery_a.pk and item_1.position == 0
    assert item_2.gallery_id == gallery_a.pk and item_2.position == 1
    assert item_3.gallery_id == gallery_b.pk and item_3.position == 0
    assert links == [
        (gallery_a.pk, item_1.pk, 0),
        (gallery_a.pk, item_2.pk, 1),
        (gallery_b.pk, item_3.pk, 0),
    ]


@pytest.mark.django_db
def test_sync_media_item_gallery_links_clears_stale_links(monkeypatch):
    gallery = MediaGalleryFactory.create(external_id="/api/v1/media/galleries/1")
    stale_item = MediaItemFactory.create(
        external_id="/api/v1/media/items/10",
        gallery=gallery,
        position=2,
    )

    payload = [{"@id": "/api/v1/media/galleries/1", "items": []}]
    monkeypatch.setattr("apps.imports.scrapers.viernulvier.fetch_viernulvier", lambda **_: payload)

    changed = sync_media_item_gallery_links()

    stale_item.refresh_from_db()
    assert changed == 1
    assert stale_item.gallery_id is None
    assert MediaGalleryItem.objects.filter(gallery=gallery).count() == 0


@pytest.mark.django_db
def test_sync_media_item_gallery_links_dry_run_does_not_write(monkeypatch):
    gallery = MediaGalleryFactory.create(external_id="/api/v1/media/galleries/1")
    item = MediaItemFactory.create(external_id="/api/v1/media/items/10", gallery=None, position=5)

    payload = [{"@id": "/api/v1/media/galleries/1", "items": ["/api/v1/media/items/10"]}]
    monkeypatch.setattr("apps.imports.scrapers.viernulvier.fetch_viernulvier", lambda **_: payload)

    changed = sync_media_item_gallery_links(dry_run=True)

    item.refresh_from_db()
    assert changed == 1
    assert item.gallery_id is None
    assert item.position == 5
    assert MediaGalleryItem.objects.count() == 0
    assert gallery.pk is not None


@pytest.mark.django_db
def test_sync_media_item_gallery_links_fetch_failure_marks_log_failed(monkeypatch):
    monkeypatch.setattr(
        "apps.imports.scrapers.viernulvier.fetch_viernulvier",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(RuntimeError, match="boom"):
        sync_media_item_gallery_links()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.FAILED
    assert "boom" in (log.error_message or "")


@pytest.mark.django_db
def test_sync_media_item_gallery_links_empty_payload_creates_success_log(monkeypatch):
    monkeypatch.setattr("apps.imports.scrapers.viernulvier.fetch_viernulvier", lambda **_: [])

    changed = sync_media_item_gallery_links()

    log = ImportLog.objects.latest("started_at")
    assert changed == 0
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_total == 0
    assert log.records_imported == 0
    assert log.records_failed == 0


@pytest.mark.django_db
def test_sync_media_item_gallery_links_dry_run_records_link_errors(monkeypatch):
    gallery = MediaGalleryFactory.create(external_id="/api/v1/media/galleries/1")
    payload = [
        "not-a-dict",
        {"items": []},
        {"@id": "/api/v1/media/galleries/999", "items": []},
        {"@id": "/api/v1/media/galleries/1", "items": "not-a-list"},
        {"@id": "/api/v1/media/galleries/1", "items": [None, "/api/v1/media/items/999"]},
    ]
    monkeypatch.setattr("apps.imports.scrapers.viernulvier.fetch_viernulvier", lambda **_: payload)

    progress_calls = []
    changed = sync_media_item_gallery_links(dry_run=True, on_progress=lambda idx, total: progress_calls.append((idx, total)))

    log = ImportLog.objects.latest("started_at")
    assert gallery.pk is not None
    assert changed == 0
    assert log.status == ImportLog.Status.PARTIAL_SUCCESS
    assert log.records_failed >= 1
    assert "link issues" in (log.error_message or "")
    assert progress_calls[-1] == (len(payload), len(payload))


@pytest.mark.django_db
def test_sync_media_item_gallery_links_non_dry_failed_when_only_errors(monkeypatch):
    MediaGalleryFactory.create(external_id="/api/v1/media/galleries/1")
    payload = [{"@id": "/api/v1/media/galleries/1", "items": ["/api/v1/media/items/999"]}]
    monkeypatch.setattr("apps.imports.scrapers.viernulvier.fetch_viernulvier", lambda **_: payload)

    changed = sync_media_item_gallery_links()

    log = ImportLog.objects.latest("started_at")
    assert changed == 0
    assert log.status == ImportLog.Status.FAILED
    assert "link resolutions failed" in (log.error_message or "")


@pytest.mark.django_db
def test_sync_media_item_gallery_links_partial_success_with_changes_and_errors(monkeypatch):
    gallery = MediaGalleryFactory.create(external_id="/api/v1/media/galleries/1")
    item = MediaItemFactory.create(external_id="/api/v1/media/items/10", gallery=None, position=9)

    payload = [{"@id": "/api/v1/media/galleries/1", "items": ["/api/v1/media/items/10", "/api/v1/media/items/999"]}]
    monkeypatch.setattr("apps.imports.scrapers.viernulvier.fetch_viernulvier", lambda **_: payload)

    changed = sync_media_item_gallery_links()

    log = ImportLog.objects.latest("started_at")
    item.refresh_from_db()
    assert changed == 1
    assert item.gallery_id == gallery.pk
    assert item.position == 0
    assert log.status == ImportLog.Status.PARTIAL_SUCCESS
    assert "link issues" in (log.error_message or "")


@pytest.mark.django_db
def test_sync_media_item_gallery_links_atomic_exception_is_logged_and_reraised(monkeypatch):
    MediaGalleryFactory.create(external_id="/api/v1/media/galleries/1")
    MediaItemFactory.create(external_id="/api/v1/media/items/10")
    payload = [{"@id": "/api/v1/media/galleries/1", "items": ["/api/v1/media/items/10"]}]
    monkeypatch.setattr("apps.imports.scrapers.viernulvier.fetch_viernulvier", lambda **_: payload)
    monkeypatch.setattr(
        "apps.media_library.models.MediaGalleryItem.objects.bulk_create",
        lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("write failed")),
    )

    with pytest.raises(RuntimeError, match="write failed"):
        sync_media_item_gallery_links()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.FAILED
    assert "Exception during gallery link sync" in (log.error_message or "")

