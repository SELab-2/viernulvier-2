"""
Tests for apps/core/views.py

Covers:
- ApiModelViewSet.get_permissions() — dynamic permission switching
"""

from unittest.mock import MagicMock

from django.test import TestCase, override_settings

from apps.core.views import ApiModelViewSet
from apps.core.permissions import HasPublicApiKey, HasInternalApiKey


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PUBLIC_KEY = "pub-key-123"
INTERNAL_KEY = "int-key-456"


def make_viewset(method: str) -> ApiModelViewSet:
    """Instantiate ApiModelViewSet with a fake request for the given method."""
    request = MagicMock()
    request.method = method

    vs = ApiModelViewSet()
    vs.request = request
    vs.kwargs = {}
    vs.format_kwarg = None
    return vs


# ---------------------------------------------------------------------------
# get_permissions()
# ---------------------------------------------------------------------------

class TestApiModelViewSetGetPermissions(TestCase):
    """Tests for dynamic permission selection in ApiModelViewSet."""

    # -- Safe methods → HasPublicApiKey ---------------------------------------

    def test_get_returns_public_permission(self):
        vs = make_viewset("GET")
        perms = vs.get_permissions()
        self.assertEqual(len(perms), 1)
        self.assertIsInstance(perms[0], HasPublicApiKey)

    def test_head_returns_public_permission(self):
        vs = make_viewset("HEAD")
        perms = vs.get_permissions()
        self.assertIsInstance(perms[0], HasPublicApiKey)

    def test_options_returns_public_permission(self):
        vs = make_viewset("OPTIONS")
        perms = vs.get_permissions()
        self.assertIsInstance(perms[0], HasPublicApiKey)

    # -- Write methods → HasInternalApiKey ------------------------------------

    def test_post_returns_internal_permission(self):
        vs = make_viewset("POST")
        perms = vs.get_permissions()
        self.assertEqual(len(perms), 1)
        self.assertIsInstance(perms[0], HasInternalApiKey)

    def test_put_returns_internal_permission(self):
        vs = make_viewset("PUT")
        perms = vs.get_permissions()
        self.assertIsInstance(perms[0], HasInternalApiKey)

    def test_patch_returns_internal_permission(self):
        vs = make_viewset("PATCH")
        perms = vs.get_permissions()
        self.assertIsInstance(perms[0], HasInternalApiKey)

    def test_delete_returns_internal_permission(self):
        vs = make_viewset("DELETE")
        perms = vs.get_permissions()
        self.assertIsInstance(perms[0], HasInternalApiKey)

    # -- Returned list should always have exactly one permission --------------

    def test_get_permissions_returns_list(self):
        for method in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
            vs = make_viewset(method)
            perms = vs.get_permissions()
            self.assertIsInstance(perms, list, f"Expected list for method {method}")
            self.assertEqual(len(perms), 1, f"Expected 1 permission for method {method}")

    # -- Returned instances are freshly created each time --------------------

    def test_permissions_are_new_instances_each_call(self):
        """Each call to get_permissions() should return fresh permission instances."""
        vs = make_viewset("GET")
        perms_a = vs.get_permissions()
        perms_b = vs.get_permissions()
        self.assertIsNot(perms_a[0], perms_b[0])


# ---------------------------------------------------------------------------
# Integration: full HTTP-level access via DRF test client
# ---------------------------------------------------------------------------

class TestApiModelViewSetIntegration(TestCase):
    """
    Integration tests that exercise get_permissions() via a real DRF request.
    We mount LanguageViewSet (a concrete subclass) on a temporary router.
    """

    def setUp(self):
        from rest_framework.test import APIClient
        from apps.languages.models import Language

        self.client = APIClient()
        self.pub_key = "pub-key-integration"
        self.int_key = "int-key-integration"

        # Create a Language object for GET tests
        Language.objects.all().delete()
        Language.objects.create(code="nl", name="Dutch", is_active=True)

    def _auth(self, key):
        return {"HTTP_AUTHORIZATION": f"Api-Key {key}"}

    @override_settings(PUBLIC_API_KEY="pub-key-integration", INTERNAL_API_KEY="int-key-integration")
    def test_get_with_public_key_returns_200(self):
        response = self.client.get("/api/languages/", **self._auth(self.pub_key))
        self.assertEqual(response.status_code, 200)

    @override_settings(PUBLIC_API_KEY="pub-key-integration", INTERNAL_API_KEY="int-key-integration")
    def test_get_with_internal_key_returns_403_or_401(self):
        """Internal key should NOT grant access to public endpoints (key mismatch)."""
        response = self.client.get("/api/languages/", **self._auth(self.int_key))
        self.assertIn(response.status_code, [401, 403])

    @override_settings(PUBLIC_API_KEY="pub-key-integration", INTERNAL_API_KEY="int-key-integration")
    def test_post_with_public_key_returns_403_or_401(self):
        """Public key cannot write."""
        response = self.client.post(
            "/api/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
            **self._auth(self.pub_key),
        )
        self.assertIn(response.status_code, [401, 403])

    @override_settings(PUBLIC_API_KEY="pub-key-integration", INTERNAL_API_KEY="int-key-integration")
    def test_post_with_internal_key_returns_201(self):
        response = self.client.post(
            "/api/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
            **self._auth(self.int_key),
        )
        self.assertEqual(response.status_code, 201)

    @override_settings(PUBLIC_API_KEY="pub-key-integration", INTERNAL_API_KEY="int-key-integration")
    def test_no_auth_header_returns_403(self): # TODO maybe 401?
        response = self.client.get("/api/languages/")
        self.assertEqual(response.status_code, 403)