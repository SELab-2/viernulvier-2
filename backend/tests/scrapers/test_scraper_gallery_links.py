"""Tests for gallery->item link synchronization in the Viernulvier scraper."""

from __future__ import annotations

import pytest

from apps.imports.scrapers.viernulvier import sync_media_item_gallery_links
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
    links = list(MediaGalleryItem.objects.order_by("gallery_id", "position").values_list("gallery_id", "media_item_id", "position"))

    assert changed == 6
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
    assert changed == 0
    assert item.gallery_id is None
    assert item.position == 5
    assert MediaGalleryItem.objects.count() == 0
    assert gallery.pk is not None



