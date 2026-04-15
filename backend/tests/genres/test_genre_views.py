"""
Tests for apps/genres/views.py - Genre viewsets

Covers:
- ViewSet inheritance from ApiModelViewSet
- Endpoints for GenreUseAs, Genre
- GET list/retrieve with public or internal key
- POST/PUT/PATCH/DELETE only with internal key
- Rejects missing/wrong auth
- Basic response fields
"""

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.genres.models import Genre, GenreUseAs
from apps.genres.views import GenreUseAsViewSet, GenreViewSet
from tests.factories.genre import (
    GenreFactory,
    GenreTranslationFactory,
    GenreUseAsFactory,
)
from tests.factories.language import LanguageFactory
from tests.helpers.api import internal_headers as int_headers
from tests.helpers.api import paginated_results as results_list
from tests.helpers.api import public_headers as pub_headers
from tests.helpers.api import wrong_headers

PUB_KEY = "pub-view-test-key"
INT_KEY = "int-view-test-key"


# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestGenreUseAsViewSetClass(TestCase):
    """Class-level checks for GenreUseAsViewSet."""

    def test_inherits_from_api_model_viewset(self):
        assert issubclass(GenreUseAsViewSet, ApiModelViewSet)

    def test_queryset_model(self):
        assert GenreUseAsViewSet.queryset.model == GenreUseAs


class TestGenreViewSetClass(TestCase):
    """Class-level checks for GenreViewSet."""

    def test_inherits_from_api_model_viewset(self):
        assert issubclass(GenreViewSet, ApiModelViewSet)

    def test_queryset_model(self):
        assert GenreViewSet.queryset.model == Genre


# ---------------------------------------------------------------------------
# N+1 guard - translations are prefetched
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestGenreViewSetPrefetch(TestCase):
    """Ensure genre list stays bounded in queries with translations present."""

    def setUp(self):
        self.client = APIClient()
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")
        self.lang_en = LanguageFactory(code="en", name="English")

        for idx in range(5):
            genre = GenreFactory(type=f"genre-{idx}")
            GenreTranslationFactory(genre=genre, language=self.lang_nl, name=f"NL {idx}")
            GenreTranslationFactory(genre=genre, language=self.lang_en, name=f"EN {idx}")

    def test_list_prefetches_translations_bounded_queries(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/v1/genres/?ordering=id", **pub_headers())

        assert response.status_code == 200
        assert len(results_list(response)) >= 5
        assert len(ctx) == 4


# ---------------------------------------------------------------------------
# GenreUseAs endpoints
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestGenreUseAsViewSet(TestCase):
    """CRUD tests for GenreUseAs endpoints."""

    def setUp(self):
        self.client = APIClient()
        GenreUseAs.objects.all().delete()
        self.use_as = GenreUseAsFactory(name="genre")

    # list
    def test_list_public_key(self):
        response = self.client.get("/api/v1/genre-use-as/?ordering=id", **pub_headers())
        assert response.status_code == 200

    def test_list_internal_key(self):
        response = self.client.get("/api/v1/genre-use-as/?ordering=id", **int_headers())
        assert response.status_code == 200

    def test_list_without_auth(self):
        response = self.client.get("/api/v1/genre-use-as/")
        assert response.status_code == 401

    # retrieve
    def test_retrieve_public_key(self):
        response = self.client.get(f"/api/v1/genre-use-as/{self.use_as.id}/", **pub_headers())
        assert response.status_code == 200
        assert response.data["name"] == "genre"

    def test_retrieve_internal_key(self):
        response = self.client.get(f"/api/v1/genre-use-as/{self.use_as.id}/", **int_headers())
        assert response.status_code == 200

    def test_retrieve_wrong_key(self):
        response = self.client.get(f"/api/v1/genre-use-as/{self.use_as.id}/", **wrong_headers())
        assert response.status_code == 401

    # create
    def test_create_internal_key(self):
        response = self.client.post(
            "/api/v1/genre-use-as/",
            {"name": "tag"},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 201
        assert GenreUseAs.objects.filter(name="tag").exists()

    def test_create_public_key_denied(self):
        response = self.client.post(
            "/api/v1/genre-use-as/",
            {"name": "tag"},
            format="json",
            **pub_headers(),
        )
        assert response.status_code == 403

    def test_create_without_auth_denied(self):
        response = self.client.post(
            "/api/v1/genre-use-as/",
            {"name": "tag"},
            format="json",
        )
        assert response.status_code == 401

    # update
    def test_put_internal_key(self):
        response = self.client.put(
            f"/api/v1/genre-use-as/{self.use_as.id}/",
            {"name": "genre-updated"},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 200
        self.use_as.refresh_from_db()
        assert self.use_as.name == "genre-updated"

    def test_patch_internal_key(self):
        response = self.client.patch(
            f"/api/v1/genre-use-as/{self.use_as.id}/",
            {"name": "genre-patched"},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 200
        self.use_as.refresh_from_db()
        assert self.use_as.name == "genre-patched"

    def test_put_public_key_denied(self):
        response = self.client.put(
            f"/api/v1/genre-use-as/{self.use_as.id}/",
            {"name": "genre-updated"},
            format="json",
            **pub_headers(),
        )
        assert response.status_code == 403

    def test_delete_internal_key(self):
        response = self.client.delete(f"/api/v1/genre-use-as/{self.use_as.id}/", **int_headers())
        assert response.status_code == 204
        assert not GenreUseAs.objects.filter(id=self.use_as.id).exists()

    def test_delete_public_key_denied(self):
        response = self.client.delete(f"/api/v1/genre-use-as/{self.use_as.id}/", **pub_headers())
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Genre endpoints
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestGenreViewSet(TestCase):
    """CRUD tests for Genre endpoints."""

    def setUp(self):
        self.client = APIClient()
        Genre.objects.all().delete()
        GenreUseAs.objects.all().delete()
        self.use_as = GenreUseAsFactory(name="genre")
        self.genre = GenreFactory(type="Theater", use_as=self.use_as)

    # list
    def test_list_public_key(self):
        response = self.client.get("/api/v1/genres/?ordering=id", **pub_headers())
        assert response.status_code == 200

    def test_list_internal_key(self):
        response = self.client.get("/api/v1/genres/?ordering=id", **int_headers())
        assert response.status_code == 200

    def test_list_response_fields(self):
        response = self.client.get("/api/v1/genres/?ordering=id", **pub_headers())
        results = response.data.get("results", response.data)
        item = results[0]
        assert "id" in item
        assert "type" in item
        assert "use_as" in item

    def test_list_without_auth(self):
        response = self.client.get("/api/v1/genres/")
        assert response.status_code == 401

    # retrieve
    def test_retrieve_public_key(self):
        response = self.client.get(f"/api/v1/genres/{self.genre.id}/", **pub_headers())
        assert response.status_code == 200
        assert response.data["type"] == "Theater"

    def test_retrieve_internal_key(self):
        response = self.client.get(f"/api/v1/genres/{self.genre.id}/", **int_headers())
        assert response.status_code == 200

    def test_retrieve_with_wrong_key(self):
        response = self.client.get(f"/api/v1/genres/{self.genre.id}/", **wrong_headers())
        assert response.status_code == 401

    # create
    def test_create_internal_key(self):
        response = self.client.post(
            "/api/v1/genres/",
            {"type": "Festival", "use_as_id": self.use_as.id},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 201
        assert Genre.objects.filter(type="Festival").exists()

    def test_create_public_key_denied(self):
        response = self.client.post(
            "/api/v1/genres/",
            {"type": "Festival", "use_as_id": self.use_as.id},
            format="json",
            **pub_headers(),
        )
        assert response.status_code == 403

    def test_create_without_auth_denied(self):
        response = self.client.post(
            "/api/v1/genres/",
            {"type": "Festival", "use_as": self.use_as.id},
            format="json",
        )
        assert response.status_code == 401

    # update
    def test_put_internal_key(self):
        response = self.client.put(
            f"/api/v1/genres/{self.genre.id}/",
            {"type": "Concert", "use_as_id": self.use_as.id},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 200
        self.genre.refresh_from_db()
        assert self.genre.type == "Concert"

    def test_patch_internal_key(self):
        response = self.client.patch(
            f"/api/v1/genres/{self.genre.id}/",
            {"type": "Opera"},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 200
        self.genre.refresh_from_db()
        assert self.genre.type == "Opera"

    def test_put_public_key_denied(self):
        response = self.client.put(
            f"/api/v1/genres/{self.genre.id}/",
            {"type": "Opera", "use_as": self.use_as.id},
            format="json",
            **pub_headers(),
        )
        assert response.status_code == 403

    def test_put_without_auth_denied(self):
        response = self.client.put(
            f"/api/v1/genres/{self.genre.id}/",
            {"type": "Opera", "use_as": self.use_as.id},
            format="json",
        )
        assert response.status_code == 401

    # delete
    def test_delete_internal_key(self):
        response = self.client.delete(f"/api/v1/genres/{self.genre.id}/", **int_headers())
        assert response.status_code == 204
        assert not Genre.objects.filter(id=self.genre.id).exists()

    def test_delete_public_key_denied(self):
        response = self.client.delete(f"/api/v1/genres/{self.genre.id}/", **pub_headers())
        assert response.status_code == 403

    def test_delete_without_auth_denied(self):
        response = self.client.delete(f"/api/v1/genres/{self.genre.id}/")
        assert response.status_code == 401
