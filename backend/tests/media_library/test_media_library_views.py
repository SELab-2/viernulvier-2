"""
Tests for apps/media_library/views.py

Covers:
- MediaGalleryViewSet inherits from ApiModelViewSet
- MediaItemViewSet inherits from ApiModelViewSet
- Queryset model is MediaGallery / MediaItem
- Serializer class is MediaGallerySerializer / MediaItemSerializer
- Queryset prefetch_related for media_items, translations, crops (gallery viewset)
- Queryset select_related for gallery, prefetch_related for translations/crops (item viewset)
- MediaItemViewSet queryset is ordered by position
- GET  /api/media-galleries/       - public key ✓, internal key ✓
- GET  /api/media-galleries/<id>/  - public key ✓, internal key ✓
- POST /api/media-galleries/       - internal key ✓, public key ✗
- PUT  /api/media-galleries/<id>/  - internal key ✓, public key ✗
- PATCH /api/media-galleries/<id>/ - internal key ✓, public key ✗
- DELETE /api/media-galleries/<id>/- internal key ✓, public key ✗
- All methods rejected without auth header
- All methods rejected with a completely wrong key
- Same auth matrix for /api/media-items/
- Response structure / fields on list and detail for both endpoints
- media_items nested in gallery response
- items ordered by position in list response
- Crops expose image_url, not url or image directly
"""

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.media_library.models import (
    MediaGallery,
    MediaItem,
)
from apps.media_library.serializers import MediaGallerySerializer, MediaItemSerializer
from apps.media_library.views import MediaGalleryViewSet, MediaItemViewSet
from tests.factories.language import LanguageFactory
from tests.factories.media_library import (
    MediaGalleryFactory,
    MediaItemCropFactory,
    MediaItemFactory,
    MediaItemTranslationFactory,
)

PUB_KEY = "pub-media-library-view-test-key"
INT_KEY = "int-media-library-view-test-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def wrong_headers():
    return {"HTTP_X_API_KEY": "completely-wrong-key"}


def results_list(response):
    return response.data.get("results", response.data)


# ---------------------------------------------------------------------------
# Class-level tests - MediaGalleryViewSet
# ---------------------------------------------------------------------------


class TestMediaGalleryViewSetClass(TestCase):
    """Verify MediaGalleryViewSet class-level configuration."""

    def test_inherits_from_api_model_viewset(self):
        self.assertTrue(issubclass(MediaGalleryViewSet, ApiModelViewSet))

    def test_queryset_model_is_media_gallery(self):
        self.assertEqual(MediaGalleryViewSet.queryset.model, MediaGallery)

    def test_serializer_class_is_media_gallery_serializer(self):
        self.assertEqual(MediaGalleryViewSet.serializer_class, MediaGallerySerializer)

    def test_queryset_prefetches_media_items(self):
        lookups = MediaGalleryViewSet.queryset._prefetch_related_lookups
        names = [lookup.prefetch_through if hasattr(lookup, "prefetch_through") else lookup for lookup in lookups]
        self.assertIn("media_items", names)

    def test_queryset_prefetches_media_item_translations(self):
        lookups = MediaGalleryViewSet.queryset._prefetch_related_lookups
        names = [lookup.prefetch_through if hasattr(lookup, "prefetch_through") else lookup for lookup in lookups]
        self.assertIn("media_items__translations__language", names)

    def test_queryset_prefetches_media_item_crops(self):
        lookups = MediaGalleryViewSet.queryset._prefetch_related_lookups
        names = [lookup.prefetch_through if hasattr(lookup, "prefetch_through") else lookup for lookup in lookups]
        self.assertIn("media_items__crops", names)


# ---------------------------------------------------------------------------
# Class-level tests - MediaItemViewSet
# ---------------------------------------------------------------------------


class TestMediaItemViewSetClass(TestCase):
    """Verify MediaItemViewSet class-level configuration."""

    def test_inherits_from_api_model_viewset(self):
        self.assertTrue(issubclass(MediaItemViewSet, ApiModelViewSet))

    def test_queryset_model_is_media_item(self):
        self.assertEqual(MediaItemViewSet.queryset.model, MediaItem)

    def test_serializer_class_is_media_item_serializer(self):
        self.assertEqual(MediaItemViewSet.serializer_class, MediaItemSerializer)

    def test_queryset_has_select_related_for_gallery(self):
        qs = MediaItemViewSet.queryset
        self.assertIn("gallery", qs.query.select_related)

    def test_queryset_prefetches_translations(self):
        lookups = MediaItemViewSet.queryset._prefetch_related_lookups
        names = [lookup.prefetch_through if hasattr(lookup, "prefetch_through") else lookup for lookup in lookups]
        self.assertIn("translations__language", names)

    def test_queryset_prefetches_crops(self):
        lookups = MediaItemViewSet.queryset._prefetch_related_lookups
        names = [lookup.prefetch_through if hasattr(lookup, "prefetch_through") else lookup for lookup in lookups]
        self.assertIn("crops", names)

    def test_queryset_is_ordered_by_position(self):
        ordering = MediaItemViewSet.queryset.query.order_by
        self.assertIn("position", ordering)


# ---------------------------------------------------------------------------
# GET /api/media-galleries/ - list
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaGalleryViewSetList(TestCase):
    def setUp(self):
        self.client = APIClient()
        MediaGallery.objects.all().delete()
        self.gallery_a = MediaGalleryFactory.create(name="Gallery A")
        self.gallery_b = MediaGalleryFactory.create(name="Gallery B")

    def test_list_with_public_key_returns_200(self):
        response = self.client.get("/api/media-galleries/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_with_internal_key_returns_200(self):
        response = self.client.get("/api/media-galleries/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_without_auth_returns_401_or_403(self):
        response = self.client.get("/api/media-galleries/")
        self.assertIn(response.status_code, (401, 403))

    def test_list_with_wrong_key_returns_401_or_403(self):
        response = self.client.get("/api/media-galleries/", **wrong_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_list_returns_all_galleries(self):
        response = self.client.get("/api/media-galleries/", **pub_headers())
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_response_contains_id_field(self):
        response = self.client.get("/api/media-galleries/", **pub_headers())
        self.assertIn("id", response.data["results"][0])

    def test_list_response_contains_name_field(self):
        response = self.client.get("/api/media-galleries/", **pub_headers())
        self.assertIn("name", response.data["results"][0])

    def test_list_response_contains_media_items_field(self):
        response = self.client.get("/api/media-galleries/", **pub_headers())
        self.assertIn("media_items", response.data["results"][0])


# ---------------------------------------------------------------------------
# GET /api/media-galleries/<id>/ - detail
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaGalleryViewSetDetail(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.gallery = MediaGalleryFactory.create(name="Detail Gallery")

    def test_detail_with_public_key_returns_200(self):
        response = self.client.get(f"/api/media-galleries/{self.gallery.pk}/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_detail_with_internal_key_returns_200(self):
        response = self.client.get(f"/api/media-galleries/{self.gallery.pk}/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_detail_without_auth_returns_401_or_403(self):
        response = self.client.get(f"/api/media-galleries/{self.gallery.pk}/")
        self.assertIn(response.status_code, (401, 403))

    def test_detail_returns_correct_name(self):
        response = self.client.get(f"/api/media-galleries/{self.gallery.pk}/", **pub_headers())
        self.assertEqual(response.data["name"], "Detail Gallery")

    def test_detail_unknown_id_returns_404(self):
        response = self.client.get("/api/media-galleries/999999/", **pub_headers())
        self.assertEqual(response.status_code, 404)

    def test_detail_media_items_is_list(self):
        response = self.client.get(f"/api/media-galleries/{self.gallery.pk}/", **pub_headers())
        self.assertIsInstance(response.data["media_items"], list)

    def test_detail_nested_media_items_included(self):
        MediaItemFactory.create(gallery=self.gallery)
        MediaItemFactory.create(gallery=self.gallery, position=1, original_filename="b.jpg")
        response = self.client.get(f"/api/media-galleries/{self.gallery.pk}/", **pub_headers())
        self.assertEqual(len(response.data["media_items"]), 2)

    def test_detail_nested_crops_expose_image_url(self):
        """Crops nested inside gallery detail must use image_url, not url."""
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemCropFactory.create(media_item=item, name="hd_ready")
        response = self.client.get(f"/api/media-galleries/{self.gallery.pk}/", **pub_headers())
        crops = response.data["media_items"][0]["crops"]
        self.assertEqual(len(crops), 1)
        self.assertIn("image_url", crops[0])
        self.assertNotIn("url", crops[0])
        self.assertNotIn("image", crops[0])


# ---------------------------------------------------------------------------
# Write methods - /api/media-galleries/
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaGalleryViewSetWrite(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.gallery = MediaGalleryFactory.create()

    def test_post_with_internal_key_returns_201(self):
        response = self.client.post(
            "/api/media-galleries/",
            {"name": "New Gallery"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 201)

    def test_post_with_public_key_returns_403(self):
        response = self.client.post(
            "/api/media-galleries/",
            {"name": "New Gallery"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (401, 403))

    def test_post_without_auth_returns_401_or_403(self):
        response = self.client.post(
            "/api/media-galleries/",
            {"name": "New Gallery"},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_put_with_internal_key_returns_200(self):
        response = self.client.put(
            f"/api/media-galleries/{self.gallery.pk}/",
            {"name": "Updated Gallery"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_put_with_public_key_returns_403(self):
        response = self.client.put(
            f"/api/media-galleries/{self.gallery.pk}/",
            {"name": "Updated Gallery"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (401, 403))

    def test_patch_with_internal_key_returns_200(self):
        response = self.client.patch(
            f"/api/media-galleries/{self.gallery.pk}/",
            {"name": "Patched Gallery"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_patch_with_public_key_returns_403(self):
        response = self.client.patch(
            f"/api/media-galleries/{self.gallery.pk}/",
            {"name": "Patched"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (401, 403))

    def test_delete_with_internal_key_returns_204(self):
        response = self.client.delete(
            f"/api/media-galleries/{self.gallery.pk}/",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_with_public_key_returns_403(self):
        response = self.client.delete(
            f"/api/media-galleries/{self.gallery.pk}/",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (401, 403))

    def test_delete_without_auth_returns_401_or_403(self):
        response = self.client.delete(f"/api/media-galleries/{self.gallery.pk}/")
        self.assertIn(response.status_code, (401, 403))


# ---------------------------------------------------------------------------
# GET /api/media-items/ - list
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaItemViewSetList(TestCase):
    def setUp(self):
        self.client = APIClient()
        MediaItem.objects.all().delete()
        self.gallery = MediaGalleryFactory.create()
        self.item_a = MediaItemFactory.create(
            gallery=self.gallery,
            position=0,
            original_filename="a.jpg",
        )
        self.item_b = MediaItemFactory.create(
            gallery=self.gallery,
            position=1,
            original_filename="b.jpg",
        )

    def test_list_with_public_key_returns_200(self):
        response = self.client.get("/api/media-items/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_with_internal_key_returns_200(self):
        response = self.client.get("/api/media-items/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_without_auth_returns_401_or_403(self):
        response = self.client.get("/api/media-items/")
        self.assertIn(response.status_code, (401, 403))

    def test_list_with_wrong_key_returns_401_or_403(self):
        response = self.client.get("/api/media-items/", **wrong_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_list_returns_all_items(self):
        response = self.client.get("/api/media-items/", **pub_headers())
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_response_contains_expected_fields(self):
        response = self.client.get("/api/media-items/", **pub_headers())
        item = response.data["results"][0]
        for field in (
            "id",
            "type",
            "format",
            "original_filename",
            "position",
            "width",
            "height",
            "title",
            "description",
            "credits",
            "link",
            "crops",
        ):
            with self.subTest(field=field):
                self.assertIn(field, item)

    def test_list_items_are_ordered_by_position(self):
        response = self.client.get("/api/media-items/", **pub_headers())
        positions = [item["position"] for item in response.data["results"]]
        self.assertEqual(positions, sorted(positions))

    def test_list_crops_expose_image_url_not_url(self):
        """Crops in the item list must use image_url, not url or image."""
        MediaItemCropFactory.create(media_item=self.item_a, name="hd_ready")
        response = self.client.get("/api/media-items/", **pub_headers())
        # Find the item that has the crop
        item_with_crop = next(i for i in response.data["results"] if i["crops"])
        crop = item_with_crop["crops"][0]
        self.assertIn("image_url", crop)
        self.assertNotIn("url", crop)
        self.assertNotIn("image", crop)


# ---------------------------------------------------------------------------
# GET /api/media-items/<id>/ - detail
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaItemViewSetDetail(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.gallery = MediaGalleryFactory.create()
        self.item = MediaItemFactory.create(
            gallery=self.gallery,
            original_filename="detail.jpg",
        )

    def test_detail_with_public_key_returns_200(self):
        response = self.client.get(f"/api/media-items/{self.item.pk}/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_detail_with_internal_key_returns_200(self):
        response = self.client.get(f"/api/media-items/{self.item.pk}/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_detail_without_auth_returns_401_or_403(self):
        response = self.client.get(f"/api/media-items/{self.item.pk}/")
        self.assertIn(response.status_code, (401, 403))

    def test_detail_returns_correct_filename(self):
        response = self.client.get(f"/api/media-items/{self.item.pk}/", **pub_headers())
        self.assertEqual(response.data["original_filename"], "detail.jpg")

    def test_detail_unknown_id_returns_404(self):
        response = self.client.get("/api/media-items/999999/", **pub_headers())
        self.assertEqual(response.status_code, 404)

    def test_detail_crops_is_list(self):
        response = self.client.get(f"/api/media-items/{self.item.pk}/", **pub_headers())
        self.assertIsInstance(response.data["crops"], list)

    def test_detail_crop_fields_use_image_url(self):
        """Crop in item detail must expose image_url, not url or image."""
        MediaItemCropFactory.create(media_item=self.item, name="hd_ready")
        response = self.client.get(f"/api/media-items/{self.item.pk}/", **pub_headers())
        self.assertEqual(len(response.data["crops"]), 1)
        crop = response.data["crops"][0]
        self.assertIn("image_url", crop)
        self.assertNotIn("url", crop)
        self.assertNotIn("image", crop)

    def test_detail_translated_title_is_dict(self):
        language = LanguageFactory.create(code="nl")
        MediaItemTranslationFactory.create(
            media_item=self.item,
            language=language,
            title="NL Titel",
        )
        response = self.client.get(f"/api/media-items/{self.item.pk}/", **pub_headers())
        self.assertIsInstance(response.data["title"], dict)
        self.assertEqual(response.data["title"]["nl"], "NL Titel")


# ---------------------------------------------------------------------------
# Write methods - /api/media-items/
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaItemViewSetWrite(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.gallery = MediaGalleryFactory.create()
        self.item = MediaItemFactory.create(gallery=self.gallery)

    def test_post_with_internal_key_returns_201(self):
        response = self.client.post(
            "/api/media-items/",
            {
                "gallery_id": self.gallery.pk,
                "type": MediaItem.MediaItemType.IMAGE,
                "format": "png",
                "original_filename": "new.png",
                "position": 5,
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 201)

    def test_post_with_public_key_returns_403(self):
        response = self.client.post(
            "/api/media-items/",
            {"gallery": self.gallery.pk, "type": "foto"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (401, 403))

    def test_post_without_auth_returns_401_or_403(self):
        response = self.client.post(
            "/api/media-items/",
            {"gallery": self.gallery.pk, "type": "foto"},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_patch_with_internal_key_returns_200(self):
        response = self.client.patch(
            f"/api/media-items/{self.item.pk}/",
            {"original_filename": "patched.jpg"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_patch_with_public_key_returns_403(self):
        response = self.client.patch(
            f"/api/media-items/{self.item.pk}/",
            {"original_filename": "patched.jpg"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (401, 403))

    def test_delete_with_internal_key_returns_204(self):
        response = self.client.delete(
            f"/api/media-items/{self.item.pk}/",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_with_public_key_returns_403(self):
        response = self.client.delete(
            f"/api/media-items/{self.item.pk}/",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (401, 403))

    def test_delete_without_auth_returns_401_or_403(self):
        response = self.client.delete(f"/api/media-items/{self.item.pk}/")
        self.assertIn(response.status_code, (401, 403))


# ---------------------------------------------------------------------------
# N+1 guards - queryset prefetches
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaGalleryViewSetPrefetch(TestCase):
    """Ensure gallery list stays bounded in query count when nested data grows."""

    def setUp(self):
        self.client = APIClient()
        self.lang_nl = LanguageFactory.create(code="nl", name="Dutch")
        self.lang_en = LanguageFactory.create(code="en", name="English")

        for g in range(3):
            gallery = MediaGalleryFactory(name=f"Gallery {g}")
            for i in range(3):
                item = MediaItemFactory(gallery=gallery, position=i)
                MediaItemTranslationFactory(media_item=item, language=self.lang_nl, title=f"NL {g}-{i}")
                MediaItemTranslationFactory(media_item=item, language=self.lang_en, title=f"EN {g}-{i}")
                MediaItemCropFactory(media_item=item, name=f"crop_{g}_{i}_1")
                MediaItemCropFactory(media_item=item, name=f"crop_{g}_{i}_2")

    def test_gallery_list_prefetches_nested_relations(self):
        with self.assertNumQueries(7):
            response = self.client.get("/api/media-galleries/", **pub_headers())

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(results_list(response)), 3)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaItemViewSetPrefetch(TestCase):
    """Ensure media item list remains bounded in queries with translations and crops."""

    def setUp(self):
        self.client = APIClient()
        self.lang_nl = LanguageFactory.create(code="nl", name="Dutch")
        self.lang_en = LanguageFactory.create(code="en", name="English")
        self.gallery = MediaGalleryFactory(name="Prefetch Gallery")

        for i in range(6):
            item = MediaItemFactory(gallery=self.gallery, position=i)
            MediaItemTranslationFactory(media_item=item, language=self.lang_nl, title=f"NL {i}")
            MediaItemTranslationFactory(media_item=item, language=self.lang_en, title=f"EN {i}")
            MediaItemCropFactory(media_item=item, name=f"crop_{i}_a")
            MediaItemCropFactory(media_item=item, name=f"crop_{i}_b")

    def test_item_list_prefetches_related_models(self):
        with self.assertNumQueries(5):
            response = self.client.get("/api/media-items/", **pub_headers())

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(results_list(response)), 6)
