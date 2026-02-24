"""
Tests for apps/core/permissions.py

Covers:
- BaseApiKeyPermission.get_api_key()
- HasPublicApiKey.has_permission()
- HasInternalApiKey.has_permission()
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

from apps.core.permissions import (
    BaseApiKeyPermission,
    HasInternalApiKey,
    HasPublicApiKey,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(method="GET", auth_header=None):
    """Return a minimal mock request."""
    request = MagicMock()
    request.method = method
    request.headers = {}
    if auth_header is not None:
        request.headers["Authorization"] = auth_header
    return request


# ---------------------------------------------------------------------------
# BaseApiKeyPermission
# ---------------------------------------------------------------------------

class TestGetApiKey(TestCase):
    """Unit-tests for BaseApiKeyPermission.get_api_key()."""

    def setUp(self):
        self.permission = BaseApiKeyPermission()

    # -- Missing header -------------------------------------------------------

    def test_raises_not_authenticated_when_no_header(self):
        request = make_request()
        with self.assertRaises(NotAuthenticated) as ctx:
            self.permission.get_api_key(request)
        self.assertIn("credentials were not provided", str(ctx.exception.detail))

    # -- Malformed header -----------------------------------------------------

    def test_raises_auth_failed_when_only_one_part(self):
        request = make_request(auth_header="somekey")
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.permission.get_api_key(request)
        self.assertIn("Invalid header format", str(ctx.exception.detail))

    def test_raises_auth_failed_when_three_parts(self):
        request = make_request(auth_header="Api-Key token extra")
        with self.assertRaises(AuthenticationFailed):
            self.permission.get_api_key(request)

    def test_raises_auth_failed_when_wrong_scheme(self):
        request = make_request(auth_header="Bearer mytoken")
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.permission.get_api_key(request)
        self.assertIn("Invalid header format", str(ctx.exception.detail))

    def test_raises_auth_failed_when_scheme_is_token(self):
        request = make_request(auth_header="Token mykey")
        with self.assertRaises(AuthenticationFailed):
            self.permission.get_api_key(request)

    # -- Valid header ---------------------------------------------------------

    def test_returns_key_for_valid_header(self):
        request = make_request(auth_header="Api-Key mysecretkey")
        result = self.permission.get_api_key(request)
        self.assertEqual(result, "mysecretkey")

    def test_scheme_is_case_insensitive(self):
        """Header scheme matching must be case-insensitive (api-key vs API-KEY)."""
        for scheme in ("api-key", "API-KEY", "Api-Key", "aPi-KeY"):
            request = make_request(auth_header=f"{scheme} mykey")
            result = self.permission.get_api_key(request)
            self.assertEqual(result, "mykey")

    def test_returns_key_with_special_characters(self):
        key = "abc123!@#$%^&*()-_=+"
        request = make_request(auth_header=f"Api-Key {key}")
        self.assertEqual(self.permission.get_api_key(request), key)


# ---------------------------------------------------------------------------
# HasPublicApiKey
# ---------------------------------------------------------------------------

class TestHasPublicApiKey(TestCase):
    """Unit-tests for HasPublicApiKey.has_permission()."""

    VALID_KEY = "public-test-key-abc"

    def setUp(self):
        self.permission = HasPublicApiKey()
        self.view = MagicMock()

    def _make(self, method="GET", key=None):
        header = f"Api-Key {key or self.VALID_KEY}"
        return make_request(method=method, auth_header=header)

    # -- Non-safe methods are always rejected ---------------------------------

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_rejects_post_even_with_valid_key(self):
        result = self.permission.has_permission(self._make(method="POST"), self.view)
        self.assertFalse(result)

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_rejects_put_even_with_valid_key(self):
        result = self.permission.has_permission(self._make(method="PUT"), self.view)
        self.assertFalse(result)

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_rejects_patch_even_with_valid_key(self):
        result = self.permission.has_permission(self._make(method="PATCH"), self.view)
        self.assertFalse(result)

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_rejects_delete_even_with_valid_key(self):
        result = self.permission.has_permission(self._make(method="DELETE"), self.view)
        self.assertFalse(result)

    # -- Safe methods ---------------------------------------------------------

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_allows_get_with_correct_key(self):
        result = self.permission.has_permission(self._make(method="GET"), self.view)
        self.assertTrue(result)

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_allows_head_with_correct_key(self):
        result = self.permission.has_permission(self._make(method="HEAD"), self.view)
        self.assertTrue(result)

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_allows_options_with_correct_key(self):
        result = self.permission.has_permission(self._make(method="OPTIONS"), self.view)
        self.assertTrue(result)

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_rejects_get_with_wrong_key(self):
        request = make_request(method="GET", auth_header="Api-Key wrong-key")
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.permission.has_permission(request, self.view)
        self.assertIn("Invalid Public API key", str(ctx.exception.detail))

    # -- Misconfigured server -------------------------------------------------

    @override_settings(PUBLIC_API_KEY=None)
    def test_raises_if_key_not_configured(self):
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.permission.has_permission(self._make(), self.view)
        self.assertIn("not configured", str(ctx.exception.detail))

    def test_raises_if_key_setting_absent(self):
        """If PUBLIC_API_KEY is not set at all, should raise."""
        from django.conf import settings
        original = getattr(settings, "PUBLIC_API_KEY", "MISSING")
        try:
            if hasattr(settings, "PUBLIC_API_KEY"):
                delattr(settings, "PUBLIC_API_KEY")
            with self.assertRaises(AuthenticationFailed):
                self.permission.has_permission(self._make(), self.view)
        finally:
            if original != "MISSING":
                settings.PUBLIC_API_KEY = original

    # -- No auth header -------------------------------------------------------

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_raises_not_authenticated_when_no_header(self):
        request = make_request(method="GET")
        with self.assertRaises(NotAuthenticated):
            self.permission.has_permission(request, self.view)

    # -- Timing-safe comparison -----------------------------------------------

    @override_settings(PUBLIC_API_KEY=VALID_KEY)
    def test_uses_compare_digest(self):
        """Verify secrets.compare_digest is called (timing-safe)."""
        with patch("apps.core.permissions.secrets.compare_digest", return_value=True) as mock_cd:
            self.permission.has_permission(self._make(), self.view)
            mock_cd.assert_called_once_with(self.VALID_KEY, self.VALID_KEY)


# ---------------------------------------------------------------------------
# HasInternalApiKey
# ---------------------------------------------------------------------------

class TestHasInternalApiKey(TestCase):
    """Unit-tests for HasInternalApiKey.has_permission()."""

    VALID_KEY = "internal-test-key-xyz"

    def setUp(self):
        self.permission = HasInternalApiKey()
        self.view = MagicMock()

    def _make(self, method="POST", key=None):
        header = f"Api-Key {key or self.VALID_KEY}"
        return make_request(method=method, auth_header=header)

    # -- Write methods --------------------------------------------------------

    @override_settings(INTERNAL_API_KEY=VALID_KEY)
    def test_allows_post_with_correct_key(self):
        result = self.permission.has_permission(self._make(method="POST"), self.view)
        self.assertTrue(result)

    @override_settings(INTERNAL_API_KEY=VALID_KEY)
    def test_allows_put_with_correct_key(self):
        result = self.permission.has_permission(self._make(method="PUT"), self.view)
        self.assertTrue(result)

    @override_settings(INTERNAL_API_KEY=VALID_KEY)
    def test_allows_patch_with_correct_key(self):
        result = self.permission.has_permission(self._make(method="PATCH"), self.view)
        self.assertTrue(result)

    @override_settings(INTERNAL_API_KEY=VALID_KEY)
    def test_allows_delete_with_correct_key(self):
        result = self.permission.has_permission(self._make(method="DELETE"), self.view)
        self.assertTrue(result)

    # -- Safe methods are also allowed (no restriction on method) -------------

    @override_settings(INTERNAL_API_KEY=VALID_KEY)
    def test_allows_get_with_correct_key(self):
        """Internal key should also allow GET (full access)."""
        result = self.permission.has_permission(self._make(method="GET"), self.view)
        self.assertTrue(result)

    # -- Wrong key ------------------------------------------------------------

    @override_settings(INTERNAL_API_KEY=VALID_KEY)
    def test_rejects_wrong_key(self):
        request = make_request(method="POST", auth_header="Api-Key wrong-key")
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.permission.has_permission(request, self.view)
        self.assertIn("Invalid Internal API key", str(ctx.exception.detail))

    # -- Misconfigured server -------------------------------------------------

    @override_settings(INTERNAL_API_KEY=None)
    def test_raises_if_key_not_configured(self):
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.permission.has_permission(self._make(), self.view)
        self.assertIn("not configured", str(ctx.exception.detail))

    # -- No auth header -------------------------------------------------------

    @override_settings(INTERNAL_API_KEY=VALID_KEY)
    def test_raises_not_authenticated_when_no_header(self):
        request = make_request(method="POST")
        with self.assertRaises(NotAuthenticated):
            self.permission.has_permission(request, self.view)

    # -- Timing-safe comparison -----------------------------------------------

    @override_settings(INTERNAL_API_KEY=VALID_KEY)
    def test_uses_compare_digest(self):
        with patch("apps.core.permissions.secrets.compare_digest", return_value=True) as mock_cd:
            self.permission.has_permission(self._make(), self.view)
            mock_cd.assert_called_once_with(self.VALID_KEY, self.VALID_KEY)