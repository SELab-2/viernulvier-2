"""
Tests for apps/media_library/filters.py and apps/media_library/views.py.
"""

from django.test import TestCase, override_settings
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.media_library.filters import MediaGalleryFilter, MediaItemFilter
from apps.media_library.models import MediaGallery, MediaItem
from tests.factories.language import LanguageFactory
from tests.factories.media_library import (
    MediaGalleryFactory,
    MediaItemFactory,
    MediaItemTranslationFactory,
)

pytestmark = pytest.mark.django_db

PUB_KEY = "pub-media-filter-test-key"
INT_KEY = "int-media-filter-test-key"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


# =====================================================
# MediaGalleryFilter
# =====================================================


class TestMediaGalleryFilter:
    def _qs(self, params):
        return MediaGalleryFilter(params, queryset=MediaGallery.objects.all()).qs

    def test_name_icontains(self) -> None:
        MediaGalleryFactory(name="Season 2024")
        MediaGalleryFactory(name="Press Photos")

        assert self._qs({"name": "season"}).count() == 1
        assert self._qs({"name": "2024"}).count() == 1

    def test_name_case_insensitive(self) -> None:
        MediaGalleryFactory(name="Season 2024")

        assert self._qs({"name": "SEASON"}).count() == 1

    def test_name_no_match_returns_empty(self) -> None:
        MediaGalleryFactory(name="Season 2024")

        assert self._qs({"name": "archive"}).count() == 0

    def test_external_id_iexact(self) -> None:
        MediaGalleryFactory(external_id="GAL-001")
        MediaGalleryFactory(external_id="GAL-002")

        assert self._qs({"external_id": "gal-001"}).count() == 1

    def test_no_params_returns_all(self) -> None:
        MediaGalleryFactory.create_batch(3)

        assert self._qs({}).count() == 3


# =====================================================
# MediaItemFilter
# =====================================================


class TestMediaItemFilter:
    def _qs(self, params):
        return MediaItemFilter(params, queryset=MediaItem.objects.all()).qs

    def test_filter_by_gallery(self) -> None:
        gallery_a = MediaGalleryFactory()
        gallery_b = MediaGalleryFactory()
        MediaItemFactory(gallery=gallery_a, type="foto")
        MediaItemFactory(gallery=gallery_b, type="foto")

        assert self._qs({"gallery": gallery_a.id}).count() == 1

    def test_filter_by_type_foto(self) -> None:
        MediaItemFactory(type="foto")
        MediaItemFactory(type="video")

        assert self._qs({"type": "foto"}).count() == 1

    def test_filter_by_type_video(self) -> None:
        MediaItemFactory(type="foto")
        MediaItemFactory(type="video")

        assert self._qs({"type": "video"}).count() == 1

    def test_filter_by_type_audio(self) -> None:
        MediaItemFactory(type="audio")
        MediaItemFactory(type="other")

        assert self._qs({"type": "audio"}).count() == 1

    def test_invalid_type_returns_one(self) -> None:
        MediaItemFactory(type="foto")

        assert self._qs({"type": "pdf"}).count() == 1

    def test_file_format_icontains(self) -> None:
        MediaItemFactory(type="foto", format="jpg")
        MediaItemFactory(type="foto", format="png")

        assert self._qs({"file_format": "jpg"}).count() == 1

    def test_file_format_case_insensitive(self) -> None:
        MediaItemFactory(type="foto", format="JPG")

        assert self._qs({"file_format": "jpg"}).count() == 1

    def test_original_filename_icontains(self) -> None:
        MediaItemFactory(type="foto", original_filename="poster-hamlet.jpg")
        MediaItemFactory(type="foto", original_filename="cover-macbeth.jpg")

        assert self._qs({"original_filename": "poster"}).count() == 1
        assert self._qs({"original_filename": "hamlet"}).count() == 1

    def test_external_id_iexact(self) -> None:
        MediaItemFactory(type="foto", external_id="ITEM-001")
        MediaItemFactory(type="foto", external_id="ITEM-002")

        assert self._qs({"external_id": "item-001"}).count() == 1

    def test_gallery_and_type_combined(self) -> None:
        gallery = MediaGalleryFactory()
        MediaItemFactory(gallery=gallery, type="foto")
        MediaItemFactory(gallery=gallery, type="video")
        MediaItemFactory(type="foto")

        assert self._qs({"gallery": gallery.id, "type": "foto"}).count() == 1

    def test_no_params_returns_all(self) -> None:
        MediaItemFactory.create_batch(3, type="foto")

        assert self._qs({}).count() == 3


# =====================================================
# MediaGalleryViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaGalleryViewSet(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        MediaGallery.objects.all().delete()

    def list_url(self):
        return reverse("v1:media-gallery-list")

    def detail_url(self, pk):
        return reverse("v1:media-gallery-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self) -> None:
        response = self.client.get(self.list_url())
        assert response.status_code in (401, 403)

    def test_public_can_list(self) -> None:
        MediaGalleryFactory.create_batch(2)
        response = self.client.get(self.list_url(), **pub_headers())
        assert response.status_code == 200
        results = response.data.get("results", response.data)
        assert len(results) == 2

    def test_public_cannot_delete(self) -> None:
        gallery = MediaGalleryFactory()
        response = self.client.delete(self.detail_url(gallery.pk), **pub_headers())
        assert response.status_code == 403

    def test_internal_can_delete(self) -> None:
        gallery = MediaGalleryFactory()
        response = self.client.delete(self.detail_url(gallery.pk), **int_headers())
        assert response.status_code == 204
        assert not MediaGallery.objects.filter(pk=gallery.pk).exists()

    def test_filter_by_name(self) -> None:
        MediaGalleryFactory(name="Season 2024")
        MediaGalleryFactory(name="Press Photos")
        response = self.client.get(self.list_url(), {"name": "season"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_default_ordering_by_name(self) -> None:
        MediaGalleryFactory(name="Zzz Gallery")
        MediaGalleryFactory(name="Aaa Gallery")
        response = self.client.get(self.list_url(), **pub_headers())
        names = [r["name"] for r in response.data.get("results", response.data)]
        assert names == sorted(names)

    def test_ordering_by_id(self) -> None:
        MediaGalleryFactory.create_batch(3)
        response = self.client.get(self.list_url(), {"ordering": "id"}, **pub_headers())
        ids = [r["id"] for r in response.data.get("results", response.data)]
        assert ids == sorted(ids)

    def test_search_by_name(self) -> None:
        MediaGalleryFactory(name="Season 2024")
        MediaGalleryFactory(name="Press Photos")
        response = self.client.get(self.list_url(), {"search": "Season"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1


# =====================================================
# MediaItemViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaItemViewSet(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        MediaItem.objects.all().delete()

    def list_url(self):
        return reverse("v1:media-item-list")

    def detail_url(self, pk):
        return reverse("v1:media-item-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self) -> None:
        response = self.client.get(self.list_url())
        assert response.status_code in (401, 403)

    def test_public_can_list(self) -> None:
        MediaItemFactory.create_batch(3, type="foto")
        response = self.client.get(self.list_url(), **pub_headers())
        assert response.status_code == 200

    def test_public_cannot_delete(self) -> None:
        item = MediaItemFactory(type="foto")
        response = self.client.delete(self.detail_url(item.pk), **pub_headers())
        assert response.status_code == 403

    def test_internal_can_delete(self) -> None:
        item = MediaItemFactory(type="foto")
        response = self.client.delete(self.detail_url(item.pk), **int_headers())
        assert response.status_code == 204
        assert not MediaItem.objects.filter(pk=item.pk).exists()

    def test_filter_by_gallery(self) -> None:
        gallery = MediaGalleryFactory()
        MediaItemFactory(gallery=gallery, type="foto")
        MediaItemFactory(type="foto")
        response = self.client.get(self.list_url(), {"gallery": gallery.id}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_by_type(self) -> None:
        MediaItemFactory(type="foto")
        MediaItemFactory(type="video")
        response = self.client.get(self.list_url(), {"type": "foto"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_by_format(self) -> None:
        MediaItemFactory(type="foto", format="jpg")
        MediaItemFactory(type="foto", format="png")
        response = self.client.get(self.list_url(), {"file_format": "jpg"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_default_ordering_by_position(self) -> None:
        MediaItemFactory(type="foto", position=10)
        MediaItemFactory(type="foto", position=1)
        response = self.client.get(self.list_url(), **pub_headers())
        positions = [r["position"] for r in response.data.get("results", response.data)]
        assert positions == sorted(positions)

    def test_ordering_by_type(self) -> None:
        MediaItemFactory(type="video")
        MediaItemFactory(type="audio")
        MediaItemFactory(type="foto")
        response = self.client.get(self.list_url(), {"ordering": "type"}, **pub_headers())
        types = [r["type"] for r in response.data.get("results", response.data)]
        assert types == sorted(types)

    def test_search_by_original_filename(self) -> None:
        MediaItemFactory(type="foto", original_filename="poster-hamlet.jpg")
        MediaItemFactory(type="foto", original_filename="cover-other.jpg")
        response = self.client.get(self.list_url(), {"search": "hamlet"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_search_by_translated_title(self) -> None:
        lang = LanguageFactory(code="en")
        item = MediaItemFactory(type="foto", original_filename="img.jpg")
        MediaItemTranslationFactory(media_item=item, language=lang, title="Hamlet poster")
        MediaItemFactory(type="foto", original_filename="other.jpg")
        response = self.client.get(self.list_url(), {"search": "Hamlet"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1
