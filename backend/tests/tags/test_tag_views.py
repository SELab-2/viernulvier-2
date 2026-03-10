"""
Tests for apps/tags/views.py - TagViewSet

Covers:
- ViewSet inherits from ApiModelViewSet
- GET  /api/tags/        - public key ✓, internal key ✓ (OR logic)
- GET  /api/tags/<id>/   - public key ✓, internal key ✓ (OR logic)
- POST /api/tags/        - internal key ✓, public key ✗
- PUT  /api/tags/<id>/   - internal key ✓, public key ✗
- PATCH /api/tags/<id>/  - internal key ✓, public key ✗
- DELETE /api/tags/<id>/ - internal key ✓, public key ✗
- All methods rejected without auth header
- All methods rejected with a completely wrong key
- Response structure / fields
- Translations are prefetched (N+1 guard)
"""

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.tags.models import Tag
from apps.tags.serializers import TagSerializer
from apps.tags.views import TagViewSet
from tests.factories.language import LanguageFactory
from tests.factories.tag import TagFactory, TagTranslationFactory

PUB_KEY = "pub-tag-view-test-key"
INT_KEY = "int-tag-view-test-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def int_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {INT_KEY}"}


def pub_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {PUB_KEY}"}


def wrong_headers():
    return {"HTTP_AUTHORIZATION": "Api-Key completely-wrong-key"}


def results_list(response):
    return response.data.get("results", response.data)


# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestTagViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        self.assertTrue(issubclass(TagViewSet, ApiModelViewSet))

    def test_queryset_model_is_tag(self):
        self.assertEqual(TagViewSet.queryset.model, Tag)

    def test_serializer_class_is_tag_serializer(self):
        self.assertEqual(TagViewSet.serializer_class, TagSerializer)

    def test_queryset_has_prefetch_related_translations(self):
        queryset = TagViewSet().get_queryset()
        lookups = queryset._prefetch_related_lookups

        lookup_names = [lookup.prefetch_through if hasattr(lookup, "prefetch_through") else lookup for lookup in lookups]

        self.assertIn("translations", lookup_names)


# ---------------------------------------------------------------------------
# N+1 guard - translations
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetPrefetch(TestCase):
    """Ensure tag list stays bounded in queries with translations present."""

    def setUp(self):
        self.client = APIClient()
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")
        self.lang_en = LanguageFactory(code="en", name="English")

        for idx in range(6):
            tag = TagFactory(type="genre")
            TagTranslationFactory(tag=tag, language=self.lang_nl, name=f"NL {idx}")
            TagTranslationFactory(tag=tag, language=self.lang_en, name=f"EN {idx}")

    def test_list_prefetches_translations_bounded_queries(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/tags/?ordering=id", **pub_headers())

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(results_list(response)), 6)
        self.assertLessEqual(len(ctx), 3)


# ---------------------------------------------------------------------------
# GET /api/tags/  - list
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetList(TestCase):
    def setUp(self):
        self.client = APIClient()
        Tag.objects.all().delete()
        self.tag_a = TagFactory.create(type="genre")
        self.tag_b = TagFactory.create(type="theme")

    def test_list_with_public_key_returns_200(self):
        response = self.client.get("/api/tags/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_with_internal_key_also_returns_200(self):
        response = self.client.get("/api/tags/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_returns_all_tags_with_public_key(self):
        response = self.client.get("/api/tags/", **pub_headers())
        results = response.data.get("results", response.data)
        ids = [item["id"] for item in results]
        self.assertIn(self.tag_a.id, ids)
        self.assertIn(self.tag_b.id, ids)

    def test_list_returns_all_tags_with_internal_key(self):
        response = self.client.get("/api/tags/", **int_headers())
        results = response.data.get("results", response.data)
        ids = [item["id"] for item in results]
        self.assertIn(self.tag_a.id, ids)
        self.assertIn(self.tag_b.id, ids)

    def test_list_response_has_correct_fields(self):
        response = self.client.get("/api/tags/", **pub_headers())
        results = response.data.get("results", response.data)
        item = results[0]
        for field in (
            "id",
            "url",
            "source",
            "source_type",
            "type",
            "is_external",
            "is_enabled",
            "name",
            "short_description",
            "url_title",
        ):
            self.assertIn(field, item)

    def test_list_without_auth_returns_401(self):
        response = self.client.get("/api/tags/")
        self.assertEqual(response.status_code, 401)

    def test_list_with_wrong_key_returns_401(self):
        response = self.client.get("/api/tags/", **wrong_headers())
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# GET /api/tags/<id>/  - retrieve
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetRetrieve(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tag = TagFactory.create(type="genre")

    def test_retrieve_with_public_key_returns_200(self):
        response = self.client.get(f"/api/tags/{self.tag.id}/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_retrieve_with_internal_key_returns_200(self):
        response = self.client.get(f"/api/tags/{self.tag.id}/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_retrieve_returns_correct_tag(self):
        response = self.client.get(f"/api/tags/{self.tag.id}/", **pub_headers())
        self.assertEqual(str(response.data["id"]), str(self.tag.id))

    def test_retrieve_without_auth_returns_401(self):
        response = self.client.get(f"/api/tags/{self.tag.id}/")
        self.assertEqual(response.status_code, 401)

    def test_retrieve_with_wrong_key_returns_401(self):
        response = self.client.get(f"/api/tags/{self.tag.id}/", **wrong_headers())
        self.assertEqual(response.status_code, 401)

    def test_retrieve_nonexistent_returns_404(self):
        response = self.client.get("/api/tags/00000000-0000-0000-0000-000000000000/", **int_headers())
        self.assertEqual(response.status_code, 404)

    def test_retrieve_includes_translations(self):
        lang = LanguageFactory.create(code="nl", name="Dutch")
        TagTranslationFactory.create(
            tag=self.tag,
            language=lang,
            name="Genre",
            url_title="genre",
        )
        response = self.client.get(f"/api/tags/{self.tag.id}/", **pub_headers())
        self.assertIsInstance(response.data["name"], dict)
        self.assertIn("nl", response.data["name"])


# ---------------------------------------------------------------------------
# POST /api/tags/  - create
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetCreate(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "type": "mood",
            "source": "manual",
            "source_type": "internal",
            "is_external": False,
            "is_enabled": True,
        }

    def test_create_with_internal_key_returns_201(self):
        response = self.client.post("/api/tags/", self.payload, format="json", **int_headers())
        self.assertEqual(response.status_code, 201)

    def test_create_with_internal_key_persists_to_db(self):
        self.client.post("/api/tags/", self.payload, format="json", **int_headers())
        self.assertTrue(Tag.objects.filter(type="mood").exists())

    def test_create_with_public_key_returns_403(self):
        response = self.client.post("/api/tags/", self.payload, format="json", **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_create_without_auth_returns_401(self):
        response = self.client.post("/api/tags/", self.payload, format="json")
        self.assertEqual(response.status_code, 401)

    def test_create_with_wrong_key_returns_401(self):
        response = self.client.post("/api/tags/", self.payload, format="json", **wrong_headers())
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# PUT /api/tags/<id>/  - full update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetUpdate(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tag = TagFactory.create(type="genre")
        self.payload = {
            "type": "updated-genre",
            "source": "system",
            "source_type": "internal",
            "is_external": False,
            "is_enabled": True,
        }

    def test_put_with_internal_key_returns_200(self):
        response = self.client.put(f"/api/tags/{self.tag.id}/", self.payload, format="json", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_put_with_internal_key_updates_db(self):
        self.client.put(f"/api/tags/{self.tag.id}/", self.payload, format="json", **int_headers())
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.type, "updated-genre")

    def test_put_with_public_key_returns_403(self):
        response = self.client.put(f"/api/tags/{self.tag.id}/", self.payload, format="json", **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_put_without_auth_returns_401(self):
        response = self.client.put(f"/api/tags/{self.tag.id}/", self.payload, format="json")
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# PATCH /api/tags/<id>/  - partial update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetPartialUpdate(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tag = TagFactory.create(type="genre", is_enabled=True)

    def test_patch_with_internal_key_returns_200(self):
        response = self.client.patch(
            f"/api/tags/{self.tag.id}/",
            {"is_enabled": False},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_patch_with_internal_key_updates_field(self):
        self.client.patch(
            f"/api/tags/{self.tag.id}/",
            {"is_enabled": False},
            format="json",
            **int_headers(),
        )
        self.tag.refresh_from_db()
        self.assertFalse(self.tag.is_enabled)

    def test_patch_with_public_key_returns_403(self):
        response = self.client.patch(
            f"/api/tags/{self.tag.id}/",
            {"is_enabled": False},
            format="json",
            **pub_headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_without_auth_returns_401(self):
        response = self.client.patch(f"/api/tags/{self.tag.id}/", {"is_enabled": False}, format="json")
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# DELETE /api/tags/<id>/  - destroy
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetDelete(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_delete_with_internal_key_returns_204(self):
        tag = TagFactory.create(type="genre")
        response = self.client.delete(f"/api/tags/{tag.id}/", **int_headers())
        self.assertEqual(response.status_code, 204)

    def test_delete_with_internal_key_removes_from_db(self):
        tag = TagFactory.create(type="genre")
        self.client.delete(f"/api/tags/{tag.id}/", **int_headers())
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_delete_with_public_key_returns_403(self):
        tag = TagFactory.create(type="genre")
        response = self.client.delete(f"/api/tags/{tag.id}/", **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_delete_without_auth_returns_401(self):
        tag = TagFactory.create(type="genre")
        response = self.client.delete(f"/api/tags/{tag.id}/")
        self.assertEqual(response.status_code, 401)

    def test_delete_with_wrong_key_returns_401(self):
        tag = TagFactory.create(type="genre")
        response = self.client.delete(f"/api/tags/{tag.id}/", **wrong_headers())
        self.assertEqual(response.status_code, 401)
