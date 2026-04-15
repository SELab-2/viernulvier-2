"""
Tests for apps/languages/views.py - LanguageViewSet

Covers:
- ViewSet inherits from ApiModelViewSet
- lookup_field is "code"
- GET  /api/v1/languages/          - public key ✓, internal key ✓ (OR logic)
- GET  /api/v1/languages/<code>/   - public key ✓, internal key ✓ (OR logic)
- POST /api/v1/languages/          - internal key ✓, public key ✗
- PUT  /api/v1/languages/<code>/   - internal key ✓, public key ✗
- PATCH /api/v1/languages/<code>/  - internal key ✓, public key ✗
- DELETE /api/v1/languages/<code>/ - internal key ✓, public key ✗
- All methods rejected without auth header
- All methods rejected with a completely wrong key
- Response structure / fields
"""

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.languages.models import Language
from apps.languages.serializers import LanguageSerializer
from apps.languages.views import LanguageViewSet
from tests.factories.language import LanguageFactory
from tests.helpers.api import internal_headers as int_headers
from tests.helpers.api import public_headers as pub_headers
from tests.helpers.api import wrong_headers

PUB_KEY = "pub-view-test-key"
INT_KEY = "int-view-test-key"


# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestLanguageViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        assert issubclass(LanguageViewSet, ApiModelViewSet)

    def test_lookup_field_is_code(self):
        assert LanguageViewSet.lookup_field == "code"

    def test_queryset_is_language(self):
        assert LanguageViewSet.queryset.model == Language

    def test_serializer_class_is_language_serializer(self):
        assert LanguageViewSet.serializer_class == LanguageSerializer


# ---------------------------------------------------------------------------
# GET /api/v1/languages/  - list
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLanguageViewSetList(TestCase):
    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()
        LanguageFactory(code="nl", name="Dutch", is_active=True)
        LanguageFactory(code="en", name="English", is_active=True)

    def test_list_with_public_key_returns_200(self):
        response = self.client.get("/api/v1/languages/", **pub_headers())
        assert response.status_code == 200

    def test_list_with_internal_key_also_returns_200(self):
        """Internal key is valid for read after the OR-composition change."""
        response = self.client.get("/api/v1/languages/", **int_headers())
        assert response.status_code == 200

    def test_list_returns_all_languages_with_public_key(self):
        response = self.client.get("/api/v1/languages/", **pub_headers())
        results = response.data.get("results", response.data)
        codes = [item["code"] for item in results]
        assert "nl" in codes
        assert "en" in codes

    def test_list_returns_all_languages_with_internal_key(self):
        response = self.client.get("/api/v1/languages/", **int_headers())
        results = response.data.get("results", response.data)
        codes = [item["code"] for item in results]
        assert "nl" in codes
        assert "en" in codes

    def test_list_response_has_correct_fields(self):
        response = self.client.get("/api/v1/languages/", **pub_headers())
        results = response.data.get("results", response.data)
        item = results[0]
        assert "code" in item
        assert "name" in item
        assert "is_active" in item

    def test_list_without_auth_returns_401(self):
        response = self.client.get("/api/v1/languages/")
        assert response.status_code == 401

    def test_list_with_wrong_key_returns_401(self):
        response = self.client.get("/api/v1/languages/", **wrong_headers())
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/languages/<code>/  - retrieve
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLanguageViewSetRetrieve(TestCase):
    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()
        LanguageFactory(code="nl", name="Dutch", is_active=True)

    def test_retrieve_with_public_key_returns_200(self):
        response = self.client.get("/api/v1/languages/nl/", **pub_headers())
        assert response.status_code == 200

    def test_retrieve_with_internal_key_also_returns_200(self):
        """Internal key is valid for read after the OR-composition change."""
        response = self.client.get("/api/v1/languages/nl/", **int_headers())
        assert response.status_code == 200

    def test_retrieve_returns_correct_language(self):
        response = self.client.get("/api/v1/languages/nl/", **pub_headers())
        assert response.data["code"] == "nl"
        assert response.data["name"] == "Dutch"

    def test_retrieve_nonexistent_returns_404(self):
        response = self.client.get("/api/v1/languages/xx/", **pub_headers())
        assert response.status_code == 404

    def test_retrieve_nonexistent_with_internal_key_returns_404(self):
        response = self.client.get("/api/v1/languages/xx/", **int_headers())
        assert response.status_code == 404

    def test_retrieve_without_auth_returns_401(self):
        response = self.client.get("/api/v1/languages/nl/")
        assert response.status_code == 401

    def test_retrieve_with_wrong_key_returns_401(self):
        response = self.client.get("/api/v1/languages/nl/", **wrong_headers())
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/languages/  - create
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLanguageViewSetCreate(TestCase):
    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()

    def test_create_with_internal_key_returns_201(self):
        response = self.client.post(
            "/api/v1/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 201

    def test_create_adds_language_to_db(self):
        self.client.post(
            "/api/v1/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
            **int_headers(),
        )
        assert Language.objects.filter(code="de").exists()

    def test_create_response_has_correct_fields(self):
        response = self.client.post(
            "/api/v1/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
            **int_headers(),
        )
        assert "code" in response.data
        assert response.data["code"] == "de"

    def test_create_with_public_key_returns_403(self):
        """Public key is not accepted for write methods."""
        response = self.client.post(
            "/api/v1/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
            **pub_headers(),
        )
        assert response.status_code == 403

    def test_create_without_auth_returns_401(self):
        response = self.client.post(
            "/api/v1/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
        )
        assert response.status_code == 401

    def test_create_with_wrong_key_returns_401(self):
        response = self.client.post(
            "/api/v1/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
            **wrong_headers(),
        )
        assert response.status_code == 401

    def test_create_duplicate_code_returns_422(self):
        LanguageFactory(code="nl", name="Dutch", is_active=True)
        response = self.client.post(
            "/api/v1/languages/",
            {"code": "nl", "name": "Dutch Duplicate", "is_active": True},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 422

    def test_create_missing_required_field_returns_422(self):
        response = self.client.post(
            "/api/v1/languages/",
            {"code": "de"},  # missing name
            format="json",
            **int_headers(),
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/v1/languages/<code>/  - full update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLanguageViewSetUpdate(TestCase):
    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()
        LanguageFactory(code="nl", name="Dutch", is_active=True)

    def test_put_with_internal_key_returns_200(self):
        response = self.client.put(
            "/api/v1/languages/nl/",
            {"code": "nl", "name": "Nederlands", "is_active": False},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 200

    def test_put_updates_language_in_db(self):
        self.client.put(
            "/api/v1/languages/nl/",
            {"code": "nl", "name": "Nederlands", "is_active": False},
            format="json",
            **int_headers(),
        )
        lang = Language.objects.get(code="nl")
        assert lang.name == "Nederlands"
        assert not lang.is_active

    def test_put_with_public_key_returns_403(self):
        """Public key is not accepted for write methods."""
        response = self.client.put(
            "/api/v1/languages/nl/",
            {"code": "nl", "name": "Nederlands", "is_active": True},
            format="json",
            **pub_headers(),
        )
        assert response.status_code == 403

    def test_put_without_auth_returns_401(self):
        response = self.client.put(
            "/api/v1/languages/nl/",
            {"code": "nl", "name": "Nederlands", "is_active": True},
            format="json",
        )
        assert response.status_code == 401

    def test_put_nonexistent_returns_404(self):
        response = self.client.put(
            "/api/v1/languages/xx/",
            {"code": "xx", "name": "Unknown", "is_active": True},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/v1/languages/<code>/  - partial update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLanguageViewSetPartialUpdate(TestCase):
    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()
        LanguageFactory(code="nl", name="Dutch", is_active=True)

    def test_patch_with_internal_key_returns_200(self):
        response = self.client.patch(
            "/api/v1/languages/nl/",
            {"is_active": False},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 200

    def test_patch_only_updates_specified_fields(self):
        self.client.patch(
            "/api/v1/languages/nl/",
            {"is_active": False},
            format="json",
            **int_headers(),
        )
        lang = Language.objects.get(code="nl")
        assert not lang.is_active
        assert lang.name == "Dutch"  # unchanged

    def test_patch_with_public_key_returns_403(self):
        """Public key is not accepted for write methods."""
        response = self.client.patch(
            "/api/v1/languages/nl/",
            {"is_active": False},
            format="json",
            **pub_headers(),
        )
        assert response.status_code == 403

    def test_patch_without_auth_returns_401(self):
        response = self.client.patch(
            "/api/v1/languages/nl/",
            {"is_active": False},
            format="json",
        )
        assert response.status_code == 401

    def test_patch_with_wrong_key_returns_401(self):
        response = self.client.patch(
            "/api/v1/languages/nl/",
            {"is_active": False},
            format="json",
            **wrong_headers(),
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/v1/languages/<code>/  - destroy
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLanguageViewSetDelete(TestCase):
    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()
        LanguageFactory(code="nl", name="Dutch", is_active=True)

    def test_delete_with_internal_key_returns_204(self):
        response = self.client.delete("/api/v1/languages/nl/", **int_headers())
        assert response.status_code == 204

    def test_delete_removes_language_from_db(self):
        self.client.delete("/api/v1/languages/nl/", **int_headers())
        assert not Language.objects.filter(code="nl").exists()

    def test_delete_with_public_key_returns_403(self):
        """Public key is not accepted for write methods."""
        response = self.client.delete("/api/v1/languages/nl/", **pub_headers())
        assert response.status_code == 403

    def test_delete_without_auth_returns_401(self):
        response = self.client.delete("/api/v1/languages/nl/")
        assert response.status_code == 401

    def test_delete_nonexistent_returns_404(self):
        response = self.client.delete("/api/v1/languages/xx/", **int_headers())
        assert response.status_code == 404

    def test_delete_with_wrong_key_returns_401(self):
        response = self.client.delete("/api/v1/languages/nl/", **wrong_headers())
        assert response.status_code == 401
