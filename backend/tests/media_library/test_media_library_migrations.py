"""Unit tests for media_library data migration helpers."""

from __future__ import annotations

import importlib


migration_module = importlib.import_module(
    "apps.media_library.migrations.0002_mediagalleryitem_mediagallery_items_and_more"
)


class FakeMediaItem:
    def __init__(self, *, item_id: int, gallery_id: int | None, position: int | None):
        self.id = item_id
        self.gallery_id = gallery_id
        self.position = position


class FakeMediaItemQuerySet:
    def __init__(self, items):
        self._items = items
        self.only_fields = None
        self.chunk_size = None

    def only(self, *fields):
        self.only_fields = fields
        return self

    def iterator(self, chunk_size):
        self.chunk_size = chunk_size
        return iter(self._items)


class FakeMediaItemManager:
    def __init__(self, items):
        self.exclude_kwargs = None
        self.queryset = FakeMediaItemQuerySet(items)

    def exclude(self, **kwargs):
        self.exclude_kwargs = kwargs
        return self.queryset


class FakeMediaItemModel:
    def __init__(self, items):
        self.objects = FakeMediaItemManager(items)


class FakeMediaGalleryItemRecord:
    def __init__(self, *, gallery_id, media_item_id, position):
        self.gallery_id = gallery_id
        self.media_item_id = media_item_id
        self.position = position


class FakeMediaGalleryItemManager:
    def __init__(self):
        self.bulk_create_calls = []

    def bulk_create(self, rows, **kwargs):
        self.bulk_create_calls.append((list(rows), kwargs))


class FakeMediaGalleryItemModel:
    def __init__(self):
        self.objects = FakeMediaGalleryItemManager()

    def __call__(self, *, gallery_id, media_item_id, position):
        return FakeMediaGalleryItemRecord(
            gallery_id=gallery_id,
            media_item_id=media_item_id,
            position=position,
        )


class FakeApps:
    def __init__(self, media_item_model, media_gallery_item_model):
        self._models = {
            ("media_library", "MediaItem"): media_item_model,
            ("media_library", "MediaGalleryItem"): media_gallery_item_model,
        }

    def get_model(self, app_label, model_name):
        return self._models[(app_label, model_name)]


def test_backfill_gallery_item_links_flushes_at_batch_size_threshold():
    items = [
        FakeMediaItem(item_id=i, gallery_id=10, position=2)
        for i in range(1, 1001)
    ]
    media_item_model = FakeMediaItemModel(items)
    media_gallery_item_model = FakeMediaGalleryItemModel()

    migration_module.backfill_gallery_item_links(
        FakeApps(media_item_model, media_gallery_item_model),
        schema_editor=None,
    )

    calls = media_gallery_item_model.objects.bulk_create_calls
    assert len(calls) == 1
    rows, kwargs = calls[0]
    assert len(rows) == 1000
    assert kwargs == {"batch_size": 1000, "ignore_conflicts": True}


def test_backfill_gallery_item_links_flushes_remaining_rows_after_loop():
    items = [FakeMediaItem(item_id=1, gallery_id=99, position=None)]
    media_item_model = FakeMediaItemModel(items)
    media_gallery_item_model = FakeMediaGalleryItemModel()

    migration_module.backfill_gallery_item_links(
        FakeApps(media_item_model, media_gallery_item_model),
        schema_editor=None,
    )

    calls = media_gallery_item_model.objects.bulk_create_calls
    assert len(calls) == 1
    rows, kwargs = calls[0]
    assert kwargs == {"batch_size": 1000, "ignore_conflicts": True}
    assert len(rows) == 1
    assert rows[0].gallery_id == 99
    assert rows[0].media_item_id == 1
    assert rows[0].position == 0


def test_backfill_gallery_item_links_with_no_items_does_not_bulk_create():
    media_item_model = FakeMediaItemModel([])
    media_gallery_item_model = FakeMediaGalleryItemModel()

    migration_module.backfill_gallery_item_links(
        FakeApps(media_item_model, media_gallery_item_model),
        schema_editor=None,
    )

    assert media_item_model.objects.exclude_kwargs == {"gallery_id__isnull": True}
    assert media_item_model.objects.queryset.only_fields == ("gallery_id", "id", "position")
    assert media_item_model.objects.queryset.chunk_size == 1000
    assert media_gallery_item_model.objects.bulk_create_calls == []


def test_noop_reverse_returns_none_and_does_nothing():
    result = migration_module.noop_reverse(apps=object(), schema_editor=object())

    assert result is None


