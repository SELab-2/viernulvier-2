"""Regression tests for gallery-item links in media gallery serialization."""

import pytest

from apps.media_library.models import MediaGallery, MediaGalleryItem
from apps.media_library.serializers import MediaGallerySerializer
from tests.factories.media_library import MediaGalleryFactory, MediaItemFactory


@pytest.mark.django_db
def test_gallery_serializer_excludes_through_links_when_fk_is_null():
    gallery = MediaGalleryFactory.create()
    item = MediaItemFactory.create(gallery=None, position=7, original_filename="linked.jpg")
    MediaGalleryItem.objects.create(gallery=gallery, media_item=item, position=0)

    gallery_qs = MediaGallery.objects.prefetch_related(
        "media_items",
        "media_items__translations__language",
        "media_items__crops",
    ).get(pk=gallery.pk)
    data = MediaGallerySerializer(gallery_qs).data

    assert data["media_items"] == []
