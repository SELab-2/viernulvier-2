"""
Tests for apps/core/views.py - ApiModelViewSet

The refactored ViewSet uses:
    authentication_classes = [ApiKeyAuthentication]
    permission_classes     = [ApiKeyPermission]

All access-control logic lives in those two classes (tested separately).
These tests verify that the ViewSet is wired correctly and produces the
expected HTTP responses end-to-end.

Unit tests  -> check class attributes (authentication_classes, permission_classes)
Integration -> full HTTP cycle via LanguageViewSet (the only concrete subclass)

HTTP access matrix
─────────────────────────────────────────────────────────────────────
Method          internal key    public key      wrong key   no header
─────────────────────────────────────────────────────────────────────
GET  (list)         200             200           403         401
GET  (retrieve)     200             200           403         401
POST                201             403           403         401
PUT                 200             403           403         401
PATCH               200             403           403         401
DELETE              204             403           403         401
─────────────────────────────────────────────────────────────────────
Note: "wrong key" triggers AuthenticationFailed -> 403 (DRF default when
      no WWW-Authenticate is set). "no header" -> auth returns None ->
      anonymous -> 401 (DRF sends WWW-Authenticate).
"""

from unittest.mock import MagicMock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.authentications import ApiKeyAuthentication
from apps.core.permissions import ApiKeyPermission
from apps.core.views import ApiModelViewSet
from tests.helpers.api import internal_headers, public_headers, wrong_headers

INT_KEY = "int-view-test-key"
PUB_KEY = "pub-view-test-key"



# ---------------------------------------------------------------------------
# Class-level / wiring tests
# ---------------------------------------------------------------------------


class TestApiModelViewSetClass(TestCase):
    def test_authentication_classes_contains_api_key_authentication(self):
        self.assertIn(ApiKeyAuthentication, ApiModelViewSet.authentication_classes)

    def test_permission_classes_contains_api_key_permission(self):
        self.assertIn(ApiKeyPermission, ApiModelViewSet.permission_classes)

    def test_has_exactly_one_authentication_class(self):
        self.assertEqual(len(ApiModelViewSet.authentication_classes), 1)

    def test_has_exactly_one_permission_class(self):
        self.assertEqual(len(ApiModelViewSet.permission_classes), 1)

    def test_inherits_from_model_viewset(self):
        from rest_framework.viewsets import ModelViewSet

        self.assertTrue(issubclass(ApiModelViewSet, ModelViewSet))

    def test_get_authenticators_returns_instances(self):
        vs = ApiModelViewSet()
        vs.request = MagicMock()
        vs.kwargs = {}
        vs.format_kwarg = None
        authenticators = vs.get_authenticators()
        self.assertEqual(len(authenticators), 1)
        self.assertIsInstance(authenticators[0], ApiKeyAuthentication)

    def test_get_permissions_returns_instances(self):
        vs = ApiModelViewSet()
        vs.request = MagicMock()
        vs.kwargs = {}
        vs.format_kwarg = None
        perms = vs.get_permissions()
        self.assertEqual(len(perms), 1)
        self.assertIsInstance(perms[0], ApiKeyPermission)


# ---------------------------------------------------------------------------
# Integration - GET list
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestApiModelViewSetList(TestCase):
    def setUp(self):
        from apps.languages.models import Language

        self.client = APIClient()
        Language.objects.all().delete()
        Language.objects.create(code="nl", name="Dutch", is_active=True)

    def test_list_internal_key_returns_200(self):
        response = self.client.get("/api/v1/languages/", **internal_headers(INT_KEY))
        self.assertEqual(response.status_code, 200)

    def test_list_public_key_returns_200(self):
        response = self.client.get("/api/v1/languages/", **public_headers(PUB_KEY))
        self.assertEqual(response.status_code, 200)

    def test_list_wrong_key_returns_401(self):
        response = self.client.get("/api/v1/languages/", **wrong_headers())
        self.assertEqual(response.status_code, 401)

    def test_list_no_auth_returns_401(self):
        """No header -> authentication returns None -> DRF sends 401."""
        response = self.client.get("/api/v1/languages/")
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# Integration - GET retrieve
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestApiModelViewSetRetrieve(TestCase):
    def setUp(self):
        from apps.languages.models import Language

        self.client = APIClient()
        Language.objects.all().delete()
        Language.objects.create(code="nl", name="Dutch", is_active=True)

    def test_retrieve_internal_key_returns_200(self):
        response = self.client.get("/api/v1/languages/nl/", **internal_headers(INT_KEY))
        self.assertEqual(response.status_code, 200)

    def test_retrieve_public_key_returns_200(self):
        response = self.client.get("/api/v1/languages/nl/", **public_headers(PUB_KEY))
        self.assertEqual(response.status_code, 200)

    def test_retrieve_wrong_key_returns_401(self):
        response = self.client.get("/api/v1/languages/nl/", **wrong_headers())
        self.assertEqual(response.status_code, 401)

    def test_retrieve_no_auth_returns_401(self):
        response = self.client.get("/api/v1/languages/nl/")
        self.assertEqual(response.status_code, 401)

    def test_retrieve_nonexistent_with_internal_key_returns_404(self):
        response = self.client.get("/api/v1/languages/xx/", **internal_headers(INT_KEY))
        self.assertEqual(response.status_code, 404)

    def test_retrieve_nonexistent_with_public_key_returns_404(self):
        response = self.client.get("/api/v1/languages/xx/", **public_headers(PUB_KEY))
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# Integration - POST create
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestApiModelViewSetCreate(TestCase):
    def setUp(self):
        from apps.languages.models import Language

        self.client = APIClient()
        Language.objects.all().delete()

    def _payload(self):
        return {"code": "de", "name": "German", "is_active": True}

    def test_create_internal_key_returns_201(self):
        response = self.client.post(
            "/api/v1/languages/",
            self._payload(),
            format="json",
            **internal_headers(INT_KEY),
        )
        self.assertEqual(response.status_code, 201)

    def test_create_public_key_returns_403(self):
        response = self.client.post(
            "/api/v1/languages/",
            self._payload(),
            format="json",
            **public_headers(PUB_KEY),
        )
        self.assertEqual(response.status_code, 403)

    def test_create_wrong_key_returns_401(self):
        response = self.client.post("/api/v1/languages/", self._payload(), format="json", **wrong_headers())
        self.assertEqual(response.status_code, 401)

    def test_create_no_auth_returns_401(self):
        response = self.client.post("/api/v1/languages/", self._payload(), format="json")
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# Integration - PUT full update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestApiModelViewSetUpdate(TestCase):
    def setUp(self):
        from apps.languages.models import Language

        self.client = APIClient()
        Language.objects.all().delete()
        Language.objects.create(code="nl", name="Dutch", is_active=True)

    def _payload(self):
        return {"code": "nl", "name": "Nederlands", "is_active": False}

    def test_put_internal_key_returns_200(self):
        response = self.client.put(
            "/api/v1/languages/nl/",
            self._payload(),
            format="json",
            **internal_headers(INT_KEY),
        )
        self.assertEqual(response.status_code, 200)

    def test_put_public_key_returns_403(self):
        response = self.client.put(
            "/api/v1/languages/nl/",
            self._payload(),
            format="json",
            **public_headers(PUB_KEY),
        )
        self.assertEqual(response.status_code, 403)

    def test_put_wrong_key_returns_401(self):
        response = self.client.put("/api/v1/languages/nl/", self._payload(), format="json", **wrong_headers())
        self.assertEqual(response.status_code, 401)

    def test_put_no_auth_returns_401(self):
        response = self.client.put("/api/v1/languages/nl/", self._payload(), format="json")
        self.assertEqual(response.status_code, 401)

    def test_put_nonexistent_returns_404(self):
        response = self.client.put(
            "/api/v1/languages/xx/",
            {"code": "xx", "name": "X", "is_active": True},
            format="json",
            **internal_headers(INT_KEY),
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# Integration - PATCH partial update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestApiModelViewSetPartialUpdate(TestCase):
    def setUp(self):
        from apps.languages.models import Language

        self.client = APIClient()
        Language.objects.all().delete()
        Language.objects.create(code="nl", name="Dutch", is_active=True)

    def test_patch_internal_key_returns_200(self):
        response = self.client.patch(
            "/api/v1/languages/nl/",
            {"is_active": False},
            format="json",
            **internal_headers(INT_KEY),
        )
        self.assertEqual(response.status_code, 200)

    def test_patch_public_key_returns_403(self):
        response = self.client.patch(
            "/api/v1/languages/nl/",
            {"is_active": False},
            format="json",
            **public_headers(PUB_KEY),
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_wrong_key_returns_401(self):
        response = self.client.patch("/api/v1/languages/nl/", {"is_active": False}, format="json", **wrong_headers())
        self.assertEqual(response.status_code, 401)

    def test_patch_no_auth_returns_401(self):
        response = self.client.patch("/api/v1/languages/nl/", {"is_active": False}, format="json")
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# Integration - DELETE
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestApiModelViewSetDelete(TestCase):
    def setUp(self):
        from apps.languages.models import Language

        self.client = APIClient()
        Language.objects.all().delete()
        Language.objects.create(code="nl", name="Dutch", is_active=True)

    def test_delete_internal_key_returns_204(self):
        response = self.client.delete("/api/v1/languages/nl/", **internal_headers(INT_KEY))
        self.assertEqual(response.status_code, 204)

    def test_delete_public_key_returns_403(self):
        response = self.client.delete("/api/v1/languages/nl/", **public_headers(PUB_KEY))
        self.assertEqual(response.status_code, 403)

    def test_delete_wrong_key_returns_401(self):
        response = self.client.delete("/api/v1/languages/nl/", **wrong_headers())
        self.assertEqual(response.status_code, 401)

    def test_delete_no_auth_returns_401(self):
        response = self.client.delete("/api/v1/languages/nl/")
        self.assertEqual(response.status_code, 401)

    def test_delete_nonexistent_returns_404(self):
        response = self.client.delete("/api/v1/languages/xx/", **internal_headers(INT_KEY))
        self.assertEqual(response.status_code, 404)
