"""
Tests for apps/genres/views.py - Genre viewsets

Covers:
- ViewSet inheritance from ApiModelViewSet
- Endpoints for Genre
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
from apps.genres.models import Genre
from apps.genres.views import GenreViewSet
from tests.factories.genre import (
    GenreFactory,
    GenreTranslationFactory,
)
from tests.factories.language import LanguageFactory
from tests.helpers.api import INTERNAL_API_KEY, PUBLIC_API_KEY, BaseViewSetTestCase, paginated_results

# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestGenreViewSetClass(TestCase):
    """Class-level checks for GenreViewSet."""

    def test_inherits_from_api_model_viewset(self) -> None:
        assert issubclass(GenreViewSet, ApiModelViewSet)

    def test_queryset_model(self) -> None:
        assert GenreViewSet.queryset.model == Genre


# ---------------------------------------------------------------------------
# N+1 guard - translations are prefetched
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUBLIC_API_KEY, INTERNAL_API_KEY=INTERNAL_API_KEY)
class TestGenreViewSetPrefetch(TestCase):
    """Ensure genre list stays bounded in queries with translations present."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")
        self.lang_en = LanguageFactory(code="en", name="English")

        for idx in range(5):
            genre = GenreFactory(type=f"genre-{idx}")
            GenreTranslationFactory(genre=genre, language=self.lang_nl, name=f"NL {idx}")
            GenreTranslationFactory(genre=genre, language=self.lang_en, name=f"EN {idx}")

    def test_list_prefetches_translations_bounded_queries(self) -> None:
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/v1/genres/?ordering=id", **self.pub_headers())

        assert response.status_code == 200
        assert len(paginated_results(response)) >= 5
        assert len(ctx) == 4

    def pub_headers(self):
        """Return public API key headers for this standalone TestCase."""
        return {"HTTP_X_API_KEY": PUBLIC_API_KEY}


# ---------------------------------------------------------------------------
# Genre endpoints
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUBLIC_API_KEY, INTERNAL_API_KEY=INTERNAL_API_KEY)
class TestGenreViewSet(BaseViewSetTestCase):
    """CRUD tests for Genre endpoints."""

    def setUp(self) -> None:
        super().setUp()
        Genre.objects.all().delete()
        self.genre = GenreFactory(type="Theater")

    # list
    def test_list_public_key(self) -> None:
        response = self.client.get("/api/v1/genres/?ordering=id", **self.pub_headers())
        assert response.status_code == 200

    def test_list_internal_key(self) -> None:
        response = self.client.get("/api/v1/genres/?ordering=id", **self.int_headers())
        assert response.status_code == 200

    def test_list_response_fields(self) -> None:
        response = self.client.get("/api/v1/genres/?ordering=id", **self.pub_headers())
        results = paginated_results(response)
        item = results[0]
        assert "id" in item
        assert "type" in item

    def test_list_without_auth(self) -> None:
        response = self.client.get("/api/v1/genres/")
        assert response.status_code == 401

    # retrieve
    def test_retrieve_public_key(self) -> None:
        response = self.client.get(f"/api/v1/genres/{self.genre.id}/", **self.pub_headers())
        assert response.status_code == 200
        assert response.data["type"] == "Theater"

    def test_retrieve_internal_key(self) -> None:
        response = self.client.get(f"/api/v1/genres/{self.genre.id}/", **self.int_headers())
        assert response.status_code == 200

    def test_retrieve_with_wrong_key(self) -> None:
        response = self.client.get(f"/api/v1/genres/{self.genre.id}/", **self.wrong_headers())
        assert response.status_code == 401

    # create
    def test_create_internal_key(self) -> None:
        response = self.client.post(
            "/api/v1/genres/",
            {"type": "Festival"},
            format="json",
            **self.int_headers(),
        )
        assert response.status_code == 201
        assert Genre.objects.filter(type="Festival").exists()

    def test_create_public_key_denied(self) -> None:
        response = self.client.post(
            "/api/v1/genres/",
            {"type": "Festival"},
            format="json",
            **self.pub_headers(),
        )
        assert response.status_code == 403

    def test_create_without_auth_denied(self) -> None:
        response = self.client.post(
            "/api/v1/genres/",
            {"type": "Festival"},
            format="json",
        )
        assert response.status_code == 401

    # update
    def test_put_internal_key(self) -> None:
        response = self.client.put(
            f"/api/v1/genres/{self.genre.id}/",
            {"type": "Concert"},
            format="json",
            **self.int_headers(),
        )
        assert response.status_code == 200
        self.genre.refresh_from_db()
        assert self.genre.type == "Concert"

    def test_patch_internal_key(self) -> None:
        response = self.client.patch(
            f"/api/v1/genres/{self.genre.id}/",
            {"type": "Opera"},
            format="json",
            **self.int_headers(),
        )
        assert response.status_code == 200
        self.genre.refresh_from_db()
        assert self.genre.type == "Opera"

    def test_put_public_key_denied(self) -> None:
        response = self.client.put(
            f"/api/v1/genres/{self.genre.id}/",
            {"type": "Opera"},
            format="json",
            **self.pub_headers(),
        )
        assert response.status_code == 403

    def test_put_without_auth_denied(self) -> None:
        response = self.client.put(
            f"/api/v1/genres/{self.genre.id}/",
            {"type": "Opera"},
            format="json",
        )
        assert response.status_code == 401

    # delete
    def test_delete_internal_key(self) -> None:
        response = self.client.delete(f"/api/v1/genres/{self.genre.id}/", **self.int_headers())
        assert response.status_code == 204
        assert not Genre.objects.filter(id=self.genre.id).exists()

    def test_delete_public_key_denied(self) -> None:
        response = self.client.delete(f"/api/v1/genres/{self.genre.id}/", **self.pub_headers())
        assert response.status_code == 403

    def test_delete_without_auth_denied(self) -> None:
        response = self.client.delete(f"/api/v1/genres/{self.genre.id}/")
        assert response.status_code == 401
