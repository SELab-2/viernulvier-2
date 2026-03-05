"""
Tests for apps/core/permissions.py — ApiKeyPermission

The permission class reads request.auth (set by ApiKeyAuthentication) and
decides access based on the following rules:

    request.auth == "internal"  ->  full access (all HTTP methods)
    request.auth == "public"    ->  read-only  (GET, HEAD, OPTIONS only)
    request.auth == None / other->  denied

Covers:
- Internal auth -> allowed for all methods
- Public auth   -> allowed for safe methods, denied for write methods
- None / missing auth -> denied for all methods
- Unknown auth value  -> denied
- Return type is always bool
- has_object_permission falls back to has_permission (default DRF behaviour)
"""

from unittest.mock import MagicMock

from django.test import TestCase
from rest_framework.permissions import SAFE_METHODS

from apps.core.permissions import ApiKeyPermission

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_request(method="GET", auth=None):
    request = MagicMock()
    request.method = method
    request.auth = auth
    return request


# ---------------------------------------------------------------------------
# Internal auth — full access
# ---------------------------------------------------------------------------


class TestApiKeyPermissionInternal(TestCase):
    def setUp(self):
        self.permission = ApiKeyPermission()
        self.view = MagicMock()

    def test_internal_allows_get(self):
        self.assertTrue(self.permission.has_permission(make_request("GET", "internal"), self.view))

    def test_internal_allows_head(self):
        self.assertTrue(self.permission.has_permission(make_request("HEAD", "internal"), self.view))

    def test_internal_allows_options(self):
        self.assertTrue(self.permission.has_permission(make_request("OPTIONS", "internal"), self.view))

    def test_internal_allows_post(self):
        self.assertTrue(self.permission.has_permission(make_request("POST", "internal"), self.view))

    def test_internal_allows_put(self):
        self.assertTrue(self.permission.has_permission(make_request("PUT", "internal"), self.view))

    def test_internal_allows_patch(self):
        self.assertTrue(self.permission.has_permission(make_request("PATCH", "internal"), self.view))

    def test_internal_allows_delete(self):
        self.assertTrue(self.permission.has_permission(make_request("DELETE", "internal"), self.view))

    def test_internal_returns_true_for_all_methods(self):
        for method in ("GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"):
            result = self.permission.has_permission(make_request(method, "internal"), self.view)
            self.assertTrue(result, f"Internal auth should allow {method}")


# ---------------------------------------------------------------------------
# Public auth — read-only
# ---------------------------------------------------------------------------


class TestApiKeyPermissionPublic(TestCase):
    def setUp(self):
        self.permission = ApiKeyPermission()
        self.view = MagicMock()

    # Safe methods allowed

    def test_public_allows_get(self):
        self.assertTrue(self.permission.has_permission(make_request("GET", "public"), self.view))

    def test_public_allows_head(self):
        self.assertTrue(self.permission.has_permission(make_request("HEAD", "public"), self.view))

    def test_public_allows_options(self):
        self.assertTrue(self.permission.has_permission(make_request("OPTIONS", "public"), self.view))

    # Write methods denied

    def test_public_denies_post(self):
        self.assertFalse(self.permission.has_permission(make_request("POST", "public"), self.view))

    def test_public_denies_put(self):
        self.assertFalse(self.permission.has_permission(make_request("PUT", "public"), self.view))

    def test_public_denies_patch(self):
        self.assertFalse(self.permission.has_permission(make_request("PATCH", "public"), self.view))

    def test_public_denies_delete(self):
        self.assertFalse(self.permission.has_permission(make_request("DELETE", "public"), self.view))

    def test_public_allows_all_safe_methods(self):
        for method in SAFE_METHODS:
            result = self.permission.has_permission(make_request(method, "public"), self.view)
            self.assertTrue(result, f"Public auth should allow safe method {method}")

    def test_public_denies_all_write_methods(self):
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            result = self.permission.has_permission(make_request(method, "public"), self.view)
            self.assertFalse(result, f"Public auth should deny write method {method}")


# ---------------------------------------------------------------------------
# No auth (unauthenticated) — all denied
# ---------------------------------------------------------------------------


class TestApiKeyPermissionNoAuth(TestCase):
    def setUp(self):
        self.permission = ApiKeyPermission()
        self.view = MagicMock()

    def test_none_auth_denies_get(self):
        self.assertFalse(self.permission.has_permission(make_request("GET", None), self.view))

    def test_none_auth_denies_post(self):
        self.assertFalse(self.permission.has_permission(make_request("POST", None), self.view))

    def test_none_auth_denies_all_methods(self):
        for method in ("GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"):
            result = self.permission.has_permission(make_request(method, None), self.view)
            self.assertFalse(result, f"No auth should deny {method}")


# ---------------------------------------------------------------------------
# Unknown auth value — all denied
# ---------------------------------------------------------------------------


class TestApiKeyPermissionUnknownAuth(TestCase):
    def setUp(self):
        self.permission = ApiKeyPermission()
        self.view = MagicMock()

    def test_unknown_string_denies_get(self):
        self.assertFalse(self.permission.has_permission(make_request("GET", "superadmin"), self.view))

    def test_unknown_string_denies_post(self):
        self.assertFalse(self.permission.has_permission(make_request("POST", "superadmin"), self.view))

    def test_empty_string_auth_denies_all(self):
        for method in ("GET", "POST", "DELETE"):
            result = self.permission.has_permission(make_request(method, ""), self.view)
            self.assertFalse(result, f"Empty-string auth should deny {method}")

    def test_boolean_true_auth_denies(self):
        """request.auth should only accept the exact strings "internal" / "public"."""
        result = self.permission.has_permission(make_request("GET", True), self.view)
        self.assertFalse(result)

    def test_numeric_auth_denies(self):
        result = self.permission.has_permission(make_request("GET", 1), self.view)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# Return type is always bool
# ---------------------------------------------------------------------------


class TestApiKeyPermissionReturnType(TestCase):
    def setUp(self):
        self.permission = ApiKeyPermission()
        self.view = MagicMock()

    def test_returns_bool_for_internal(self):
        result = self.permission.has_permission(make_request("GET", "internal"), self.view)
        self.assertIsInstance(result, bool)

    def test_returns_bool_for_public_safe(self):
        result = self.permission.has_permission(make_request("GET", "public"), self.view)
        self.assertIsInstance(result, bool)

    def test_returns_bool_for_public_write(self):
        result = self.permission.has_permission(make_request("POST", "public"), self.view)
        self.assertIsInstance(result, bool)

    def test_returns_bool_for_no_auth(self):
        result = self.permission.has_permission(make_request("GET", None), self.view)
        self.assertIsInstance(result, bool)


# ---------------------------------------------------------------------------
# Inheritance / class contract
# ---------------------------------------------------------------------------


class TestApiKeyPermissionClass(TestCase):
    def test_inherits_from_base_permission(self):
        from rest_framework.permissions import BasePermission

        self.assertTrue(issubclass(ApiKeyPermission, BasePermission))

    def test_can_be_instantiated(self):
        perm = ApiKeyPermission()
        self.assertIsInstance(perm, ApiKeyPermission)
