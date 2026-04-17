"""
Tests for apps/tags/views.py - TagViewSet

Covers:
- ViewSet inherits from ApiModelViewSet
- GET  /api/v1/tags/        - public key ✓, internal key ✓ (OR logic)
- GET  /api/v1/tags/<id>/   - public key ✓, internal key ✓ (OR logic)
- POST /api/v1/tags/        - internal key ✓, public key ✗
- PUT  /api/v1/tags/<id>/   - internal key ✓, public key ✗
- PATCH /api/v1/tags/<id>/  - internal key ✓, public key ✗
- DELETE /api/v1/tags/<id>/ - internal key ✓, public key ✗
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
    return {"HTTP_X_API_KEY": INT_KEY}


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def wrong_headers():
    return {"HTTP_X_API_KEY": "completely-wrong-key"}


def results_list(response):
    return response.data.get("results", response.data)


# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestTagViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self) -> None:
        assert issubclass(TagViewSet, ApiModelViewSet)

    def test_queryset_model_is_tag(self) -> None:
        assert TagViewSet.queryset.model == Tag

    def test_serializer_class_is_tag_serializer(self) -> None:
        assert TagViewSet.serializer_class == TagSerializer

    def test_queryset_has_prefetch_related_translations(self) -> None:
        queryset = TagViewSet().get_queryset()
        lookups = queryset._prefetch_related_lookups

        lookup_names = [lookup.prefetch_through if hasattr(lookup, "prefetch_through") else lookup for lookup in lookups]

        assert "translations" in lookup_names


# ---------------------------------------------------------------------------
# N+1 guard - translations
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetPrefetch(TestCase):
    """Ensure tag list stays bounded in queries with translations present."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")
        self.lang_en = LanguageFactory(code="en", name="English")

        for idx in range(6):
            tag = TagFactory(type="genre")
            TagTranslationFactory(tag=tag, language=self.lang_nl, name=f"NL {idx}")
            TagTranslationFactory(tag=tag, language=self.lang_en, name=f"EN {idx}")

    def test_list_prefetches_translations_bounded_queries(self) -> None:
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/v1/tags/?ordering=id", **pub_headers())

        assert response.status_code == 200
        assert len(results_list(response)) >= 6
        assert len(ctx) <= 3


# ---------------------------------------------------------------------------
# GET /api/v1/tags/  - list
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetList(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Tag.objects.all().delete()
        self.tag_a = TagFactory.create(type="genre")
        self.tag_b = TagFactory.create(type="theme")

    def test_list_with_public_key_returns_200(self) -> None:
        response = self.client.get("/api/v1/tags/", **pub_headers())
        assert response.status_code == 200

    def test_list_with_internal_key_also_returns_200(self) -> None:
        response = self.client.get("/api/v1/tags/", **int_headers())
        assert response.status_code == 200

    def test_list_returns_all_tags_with_public_key(self) -> None:
        response = self.client.get("/api/v1/tags/", **pub_headers())
        results = response.data.get("results", response.data)
        ids = [item["id"] for item in results]
        assert self.tag_a.id in ids
        assert self.tag_b.id in ids

    def test_list_returns_all_tags_with_internal_key(self) -> None:
        response = self.client.get("/api/v1/tags/", **int_headers())
        results = response.data.get("results", response.data)
        ids = [item["id"] for item in results]
        assert self.tag_a.id in ids
        assert self.tag_b.id in ids

    def test_list_response_has_correct_fields(self) -> None:
        response = self.client.get("/api/v1/tags/", **pub_headers())
        results = response.data.get("results", response.data)
        item = results[0]
        for field in (
            "id",
            "url",
            "source",
            "type",
            "is_enabled",
            "name",
            "short_description",
            "url_title",
        ):
            assert field in item

    def test_list_without_auth_returns_401(self) -> None:
        response = self.client.get("/api/v1/tags/")
        assert response.status_code == 401

    def test_list_with_wrong_key_returns_401(self) -> None:
        response = self.client.get("/api/v1/tags/", **wrong_headers())
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/tags/<id>/  - retrieve
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetRetrieve(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.tag = TagFactory.create(type="genre")

    def test_retrieve_with_public_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/tags/{self.tag.id}/", **pub_headers())
        assert response.status_code == 200

    def test_retrieve_with_internal_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/tags/{self.tag.id}/", **int_headers())
        assert response.status_code == 200

    def test_retrieve_returns_correct_tag(self) -> None:
        response = self.client.get(f"/api/v1/tags/{self.tag.id}/", **pub_headers())
        assert str(response.data["id"]) == str(self.tag.id)

    def test_retrieve_without_auth_returns_401(self) -> None:
        response = self.client.get(f"/api/v1/tags/{self.tag.id}/")
        assert response.status_code == 401

    def test_retrieve_with_wrong_key_returns_401(self) -> None:
        response = self.client.get(f"/api/v1/tags/{self.tag.id}/", **wrong_headers())
        assert response.status_code == 401

    def test_retrieve_nonexistent_returns_404(self) -> None:
        response = self.client.get("/api/v1/tags/00000000-0000-0000-0000-000000000000/", **int_headers())
        assert response.status_code == 404

    def test_retrieve_includes_translations(self) -> None:
        lang = LanguageFactory.create(code="nl", name="Dutch")
        TagTranslationFactory.create(
            tag=self.tag,
            language=lang,
            name="Genre",
            url_title="genre",
        )
        response = self.client.get(f"/api/v1/tags/{self.tag.id}/", **pub_headers())
        assert isinstance(response.data["name"], dict)
        assert "nl" in response.data["name"]


# ---------------------------------------------------------------------------
# POST /api/v1/tags/  - create
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetCreate(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.payload = {
            "type": "mood",
            "source": "manual",
            "is_enabled": True,
        }

    def test_create_with_internal_key_returns_201(self) -> None:
        response = self.client.post("/api/v1/tags/", self.payload, format="json", **int_headers())
        assert response.status_code == 201

    def test_create_with_internal_key_persists_to_db(self) -> None:
        self.client.post("/api/v1/tags/", self.payload, format="json", **int_headers())
        assert Tag.objects.filter(type="mood").exists()

    def test_create_with_public_key_returns_403(self) -> None:
        response = self.client.post("/api/v1/tags/", self.payload, format="json", **pub_headers())
        assert response.status_code == 403

    def test_create_without_auth_returns_401(self) -> None:
        response = self.client.post("/api/v1/tags/", self.payload, format="json")
        assert response.status_code == 401

    def test_create_with_wrong_key_returns_401(self) -> None:
        response = self.client.post("/api/v1/tags/", self.payload, format="json", **wrong_headers())
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/v1/tags/<id>/  - full update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetUpdate(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.tag = TagFactory.create(type="genre")
        self.payload = {
            "type": "updated-genre",
            "source": "system",
            "is_enabled": True,
        }

    def test_put_with_internal_key_returns_200(self) -> None:
        response = self.client.put(f"/api/v1/tags/{self.tag.id}/", self.payload, format="json", **int_headers())
        assert response.status_code == 200

    def test_put_with_internal_key_updates_db(self) -> None:
        self.client.put(f"/api/v1/tags/{self.tag.id}/", self.payload, format="json", **int_headers())
        self.tag.refresh_from_db()
        assert self.tag.type == "updated-genre"

    def test_put_with_public_key_returns_403(self) -> None:
        response = self.client.put(f"/api/v1/tags/{self.tag.id}/", self.payload, format="json", **pub_headers())
        assert response.status_code == 403

    def test_put_without_auth_returns_401(self) -> None:
        response = self.client.put(f"/api/v1/tags/{self.tag.id}/", self.payload, format="json")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/v1/tags/<id>/  - partial update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetPartialUpdate(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.tag = TagFactory.create(type="genre", is_enabled=True)

    def test_patch_with_internal_key_returns_200(self) -> None:
        response = self.client.patch(
            f"/api/v1/tags/{self.tag.id}/",
            {"is_enabled": False},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 200

    def test_patch_with_internal_key_updates_field(self) -> None:
        self.client.patch(
            f"/api/v1/tags/{self.tag.id}/",
            {"is_enabled": False},
            format="json",
            **int_headers(),
        )
        self.tag.refresh_from_db()
        assert not self.tag.is_enabled

    def test_patch_with_public_key_returns_403(self) -> None:
        response = self.client.patch(
            f"/api/v1/tags/{self.tag.id}/",
            {"is_enabled": False},
            format="json",
            **pub_headers(),
        )
        assert response.status_code == 403

    def test_patch_without_auth_returns_401(self) -> None:
        response = self.client.patch(f"/api/v1/tags/{self.tag.id}/", {"is_enabled": False}, format="json")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/v1/tags/<id>/  - destroy
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSetDelete(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_delete_with_internal_key_returns_204(self) -> None:
        tag = TagFactory.create(type="genre")
        response = self.client.delete(f"/api/v1/tags/{tag.id}/", **int_headers())
        assert response.status_code == 204

    def test_delete_with_internal_key_removes_from_db(self) -> None:
        tag = TagFactory.create(type="genre")
        self.client.delete(f"/api/v1/tags/{tag.id}/", **int_headers())
        assert not Tag.objects.filter(id=tag.id).exists()

    def test_delete_with_public_key_returns_403(self) -> None:
        tag = TagFactory.create(type="genre")
        response = self.client.delete(f"/api/v1/tags/{tag.id}/", **pub_headers())
        assert response.status_code == 403

    def test_delete_without_auth_returns_401(self) -> None:
        tag = TagFactory.create(type="genre")
        response = self.client.delete(f"/api/v1/tags/{tag.id}/")
        assert response.status_code == 401

    def test_delete_with_wrong_key_returns_401(self) -> None:
        tag = TagFactory.create(type="genre")
        response = self.client.delete(f"/api/v1/tags/{tag.id}/", **wrong_headers())
        assert response.status_code == 401
