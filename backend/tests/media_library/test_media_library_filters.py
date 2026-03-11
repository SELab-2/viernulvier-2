"""
Tests for apps/media_library/filters.py and apps/media_library/views.py.
"""

import pytest
from django.urls import reverse

from apps.media_library.filters import MediaGalleryFilter, MediaItemFilter
from apps.media_library.models import MediaGallery, MediaItem
from tests.factories.language import LanguageFactory
from tests.factories.media_library import (
    MediaGalleryFactory,
    MediaItemFactory,
    MediaItemTranslationFactory,
)

pytestmark = pytest.mark.django_db


# =====================================================
# MediaGalleryFilter
# =====================================================


class TestMediaGalleryFilter:
    def _qs(self, params):
        return MediaGalleryFilter(params, queryset=MediaGallery.objects.all()).qs

    def test_name_icontains(self):
        MediaGalleryFactory(name="Season 2024")
        MediaGalleryFactory(name="Press Photos")

        assert self._qs({"name": "season"}).count() == 1
        assert self._qs({"name": "2024"}).count() == 1

    def test_name_case_insensitive(self):
        MediaGalleryFactory(name="Season 2024")

        assert self._qs({"name": "SEASON"}).count() == 1

    def test_name_no_match_returns_empty(self):
        MediaGalleryFactory(name="Season 2024")

        assert self._qs({"name": "archive"}).count() == 0

    def test_external_id_iexact(self):
        MediaGalleryFactory(external_id="GAL-001")
        MediaGalleryFactory(external_id="GAL-002")

        assert self._qs({"external_id": "gal-001"}).count() == 1

    def test_no_params_returns_all(self):
        MediaGalleryFactory.create_batch(3)

        assert self._qs({}).count() == 3


# =====================================================
# MediaItemFilter
# =====================================================


class TestMediaItemFilter:
    def _qs(self, params):
        return MediaItemFilter(params, queryset=MediaItem.objects.all()).qs

    def test_filter_by_gallery(self):
        gallery_a = MediaGalleryFactory()
        gallery_b = MediaGalleryFactory()
        MediaItemFactory(gallery=gallery_a, type="foto")
        MediaItemFactory(gallery=gallery_b, type="foto")

        assert self._qs({"gallery": gallery_a.id}).count() == 1

    def test_filter_by_type_foto(self):
        MediaItemFactory(type="foto")
        MediaItemFactory(type="video")

        assert self._qs({"type": "foto"}).count() == 1

    def test_filter_by_type_video(self):
        MediaItemFactory(type="foto")
        MediaItemFactory(type="video")

        assert self._qs({"type": "video"}).count() == 1

    def test_filter_by_type_audio(self):
        MediaItemFactory(type="audio")
        MediaItemFactory(type="other")

        assert self._qs({"type": "audio"}).count() == 1

    def test_invalid_type_returns_empty(self):
        MediaItemFactory(type="foto")

        assert self._qs({"type": "pdf"}).count() == 0

    def test_format_icontains(self):
        MediaItemFactory(type="foto", format="jpg")
        MediaItemFactory(type="foto", format="png")

        assert self._qs({"format": "jpg"}).count() == 1

    def test_format_case_insensitive(self):
        MediaItemFactory(type="foto", format="JPG")

        assert self._qs({"format": "jpg"}).count() == 1

    def test_original_filename_icontains(self):
        MediaItemFactory(type="foto", original_filename="poster-hamlet.jpg")
        MediaItemFactory(type="foto", original_filename="cover-macbeth.jpg")

        assert self._qs({"original_filename": "poster"}).count() == 1
        assert self._qs({"original_filename": "hamlet"}).count() == 1

    def test_external_id_iexact(self):
        MediaItemFactory(type="foto", external_id="ITEM-001")
        MediaItemFactory(type="foto", external_id="ITEM-002")

        assert self._qs({"external_id": "item-001"}).count() == 1

    def test_gallery_and_type_combined(self):
        gallery = MediaGalleryFactory()
        MediaItemFactory(gallery=gallery, type="foto")
        MediaItemFactory(gallery=gallery, type="video")
        MediaItemFactory(type="foto")

        assert self._qs({"gallery": gallery.id, "type": "foto"}).count() == 1

    def test_no_params_returns_all(self):
        MediaItemFactory.create_batch(3, type="foto")

        assert self._qs({}).count() == 3


# =====================================================
# MediaGalleryViewSet
# =====================================================


class TestMediaGalleryViewSet:
    list_url = reverse("mediagallery-list")

    def detail_url(self, pk):
        return reverse("mediagallery-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self, anon_client):
        assert anon_client.get(self.list_url).status_code in (401, 403)

    def test_public_can_list(self, public_client):
        MediaGalleryFactory.create_batch(2)

        response = public_client.get(self.list_url)

        assert response.status_code == 200
        assert len(response.data["results"]) == 2

    def test_public_cannot_delete(self, public_client):
        assert public_client.delete(self.detail_url(MediaGalleryFactory().pk)).status_code == 403

    def test_internal_can_delete(self, internal_client):
        gallery = MediaGalleryFactory()

        assert internal_client.delete(self.detail_url(gallery.pk)).status_code == 204
        assert not MediaGallery.objects.filter(pk=gallery.pk).exists()

    def test_filter_by_name(self, public_client):
        MediaGalleryFactory(name="Season 2024")
        MediaGalleryFactory(name="Press Photos")

        assert len(public_client.get(self.list_url, {"name": "season"}).data["results"]) == 1

    def test_default_ordering_by_name(self, public_client):
        MediaGalleryFactory(name="Zzz Gallery")
        MediaGalleryFactory(name="Aaa Gallery")

        response = public_client.get(self.list_url)
        names = [r["name"] for r in response.data["results"]]

        assert names == sorted(names)

    def test_ordering_by_id(self, public_client):
        MediaGalleryFactory.create_batch(3)

        response = public_client.get(self.list_url, {"ordering": "id"})
        ids = [r["id"] for r in response.data["results"]]

        assert ids == sorted(ids)

    def test_search_by_name(self, public_client):
        MediaGalleryFactory(name="Season 2024")
        MediaGalleryFactory(name="Press Photos")

        assert len(public_client.get(self.list_url, {"search": "Season"}).data["results"]) == 1


# =====================================================
# MediaItemViewSet
# =====================================================


class TestMediaItemViewSet:
    list_url = reverse("mediaitem-list")

    def detail_url(self, pk):
        return reverse("mediaitem-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self, anon_client):
        assert anon_client.get(self.list_url).status_code in (401, 403)

    def test_public_can_list(self, public_client):
        MediaItemFactory.create_batch(3, type="foto")

        assert public_client.get(self.list_url).status_code == 200

    def test_public_cannot_delete(self, public_client):
        assert public_client.delete(self.detail_url(MediaItemFactory(type="foto").pk)).status_code == 403

    def test_internal_can_delete(self, internal_client):
        item = MediaItemFactory(type="foto")

        assert internal_client.delete(self.detail_url(item.pk)).status_code == 204
        assert not MediaItem.objects.filter(pk=item.pk).exists()

    def test_filter_by_gallery(self, public_client):
        gallery = MediaGalleryFactory()
        MediaItemFactory(gallery=gallery, type="foto")
        MediaItemFactory(type="foto")

        assert len(public_client.get(self.list_url, {"gallery": gallery.id}).data["results"]) == 1

    def test_filter_by_type(self, public_client):
        MediaItemFactory(type="foto")
        MediaItemFactory(type="video")

        assert len(public_client.get(self.list_url, {"type": "foto"}).data["results"]) == 1

    def test_filter_by_format(self, public_client):
        MediaItemFactory(type="foto", format="jpg")
        MediaItemFactory(type="foto", format="png")

        assert len(public_client.get(self.list_url, {"format": "jpg"}).data["results"]) == 1

    def test_default_ordering_by_position(self, public_client):
        MediaItemFactory(type="foto", position=10)
        MediaItemFactory(type="foto", position=1)

        response = public_client.get(self.list_url)
        positions = [r["position"] for r in response.data["results"]]

        assert positions == sorted(positions)

    def test_ordering_by_type(self, public_client):
        MediaItemFactory(type="video")
        MediaItemFactory(type="audio")
        MediaItemFactory(type="foto")

        response = public_client.get(self.list_url, {"ordering": "type"})
        types = [r["type"] for r in response.data["results"]]

        assert types == sorted(types)

    def test_search_by_original_filename(self, public_client):
        MediaItemFactory(type="foto", original_filename="poster-hamlet.jpg")
        MediaItemFactory(type="foto", original_filename="cover-other.jpg")

        assert len(public_client.get(self.list_url, {"search": "hamlet"}).data["results"]) == 1

    def test_search_by_translated_title(self, public_client):
        lang = LanguageFactory(code="en")
        item = MediaItemFactory(type="foto", original_filename="img.jpg")
        MediaItemTranslationFactory(media_item=item, language=lang, title="Hamlet poster")
        MediaItemFactory(type="foto", original_filename="other.jpg")

        assert len(public_client.get(self.list_url, {"search": "Hamlet"}).data["results"]) == 1
