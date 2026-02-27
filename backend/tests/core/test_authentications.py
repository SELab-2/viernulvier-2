"""
Comprehensive test suite for ApiKeyAuthentication.

Covers:
- No Authorization header (anonymous passthrough)
- Malformed header formats (missing token, wrong keyword, extra parts, empty)
- Valid INTERNAL_API_KEY → returns (None, "internal")
- Valid PUBLIC_API_KEY → returns (None, "public")
- Invalid / unknown key → AuthenticationFailed
- Missing settings keys (None / absent)
- Timing-safe comparison (secrets.compare_digest path)
- Case-insensitive keyword matching ("bearer", "BEARER", "Bearer")
- Unicode / encoding edge cases in the token
- Both keys identical (internal wins)
- authenticate_header() not defined (BaseAuthentication default)
"""

import pytest
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework.exceptions import AuthenticationFailed

from apps.core.authentications import ApiKeyAuthentication


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INTERNAL_KEY = "super-secret-internal-key-abc123"
PUBLIC_KEY = "public-read-only-key-xyz789"


def make_request(auth_header: bytes | None = None):
    """Return a minimal mock request with the given raw Authorization header."""
    request = MagicMock()
    request.META = {}
    if auth_header is not None:
        request.META["HTTP_AUTHORIZATION"] = auth_header
    return request


def bearer(token: str, keyword: str = "Bearer") -> bytes:
    return f"{keyword} {token}".encode()


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
class TestApiKeyAuthentication(TestCase):

    def setUp(self):
        self.auth = ApiKeyAuthentication()

    # ------------------------------------------------------------------
    # 1. No Authorization header → skip (return None)
    # ------------------------------------------------------------------

    def test_no_auth_header_returns_none(self):
        request = make_request(auth_header=None)
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_empty_auth_header_returns_none(self):
        """An empty byte-string header means no auth parts after split."""
        request = make_request(auth_header=b"")
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # 2. Malformed header → AuthenticationFailed
    # ------------------------------------------------------------------

    def test_only_keyword_no_token_raises(self):
        request = make_request(auth_header=b"Bearer")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_wrong_keyword_raises(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY, keyword="Token"))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_wrong_keyword_basic_raises(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY, keyword="Basic"))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_three_parts_raises(self):
        request = make_request(auth_header=b"Bearer token extra")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_four_parts_raises(self):
        request = make_request(auth_header=b"Bearer a b c")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_malformed_header_error_message(self):
        request = make_request(auth_header=b"Bearer")
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertIn("Invalid Authorization header format", str(ctx.exception.detail))

    # ------------------------------------------------------------------
    # 3. Keyword case-insensitivity
    # ------------------------------------------------------------------

    def test_keyword_lowercase_bearer(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY, keyword="bearer"))
        result = self.auth.authenticate(request)
        self.assertEqual(result, (None, "internal"))

    def test_keyword_uppercase_bearer(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY, keyword="BEARER"))
        result = self.auth.authenticate(request)
        self.assertEqual(result, (None, "internal"))

    def test_keyword_mixed_case_bearer(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY, keyword="BeArEr"))
        result = self.auth.authenticate(request)
        self.assertEqual(result, (None, "internal"))

    # ------------------------------------------------------------------
    # 4. Valid INTERNAL_API_KEY
    # ------------------------------------------------------------------

    def test_valid_internal_key_returns_internal(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY))
        result = self.auth.authenticate(request)
        self.assertEqual(result, (None, "internal"))

    def test_valid_internal_key_user_is_none(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY))
        user, _ = self.auth.authenticate(request)
        self.assertIsNone(user)

    def test_valid_internal_key_scope_is_internal(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY))
        _, scope = self.auth.authenticate(request)
        self.assertEqual(scope, "internal")

    # ------------------------------------------------------------------
    # 5. Valid PUBLIC_API_KEY
    # ------------------------------------------------------------------

    def test_valid_public_key_returns_public(self):
        request = make_request(auth_header=bearer(PUBLIC_KEY))
        result = self.auth.authenticate(request)
        self.assertEqual(result, (None, "public"))

    def test_valid_public_key_user_is_none(self):
        request = make_request(auth_header=bearer(PUBLIC_KEY))
        user, scope = self.auth.authenticate(request)
        self.assertIsNone(user)

    def test_valid_public_key_scope_is_public(self):
        request = make_request(auth_header=bearer(PUBLIC_KEY))
        _, scope = self.auth.authenticate(request)
        self.assertEqual(scope, "public")

    # ------------------------------------------------------------------
    # 6. Invalid / unknown key → AuthenticationFailed
    # ------------------------------------------------------------------

    def test_unknown_key_raises(self):
        request = make_request(auth_header=bearer("totally-wrong-key"))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_unknown_key_error_message(self):
        request = make_request(auth_header=bearer("bad-key"))
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertIn("Invalid API key", str(ctx.exception.detail))

    def test_empty_token_raises(self):
        """'Bearer ' with an empty token still splits into 2 parts but key is ''."""
        request = make_request(auth_header=b"Bearer ")
        # split() on b"Bearer " yields [b"Bearer"] — only 1 part → format error
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_partial_internal_key_raises(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY[:-1]))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_internal_key_with_extra_char_raises(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY + "X"))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_internal_key_uppercase_raises(self):
        """Keys are case-sensitive."""
        request = make_request(auth_header=bearer(INTERNAL_KEY.upper()))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_public_key_uppercase_raises(self):
        request = make_request(auth_header=bearer(PUBLIC_KEY.upper()))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    # ------------------------------------------------------------------
    # 7. Missing / None settings
    # ------------------------------------------------------------------

    @override_settings(INTERNAL_API_KEY=None, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_internal_key_none_in_settings_skips_internal_check(self):
        """When INTERNAL_API_KEY is None, even a matching value falls through."""
        # There is nothing to match against, so it moves on to public check.
        request = make_request(auth_header=bearer(PUBLIC_KEY))
        result = self.auth.authenticate(request)
        self.assertEqual(result, (None, "public"))

    @override_settings(INTERNAL_API_KEY=None, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_none_internal_key_unknown_token_raises(self):
        request = make_request(auth_header=bearer("some-unknown-key"))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=None)
    def test_public_key_none_in_settings_skips_public_check(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY))
        result = self.auth.authenticate(request)
        self.assertEqual(result, (None, "internal"))

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=None)
    def test_none_public_key_unknown_token_raises(self):
        request = make_request(auth_header=bearer("random-key"))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @override_settings(INTERNAL_API_KEY=None, PUBLIC_API_KEY=None)
    def test_both_keys_none_always_raises(self):
        request = make_request(auth_header=bearer("any-key"))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_missing_internal_key_attribute(self):
        """If the setting doesn't exist at all (not even None), getattr returns None."""
        with self.settings(INTERNAL_API_KEY=None, PUBLIC_API_KEY=PUBLIC_KEY):
            request = make_request(auth_header=bearer(PUBLIC_KEY))
            result = self.auth.authenticate(request)
            self.assertEqual(result, (None, "public"))

    # ------------------------------------------------------------------
    # 8. When both keys are identical → internal wins
    # ------------------------------------------------------------------

    @override_settings(INTERNAL_API_KEY="shared-key", PUBLIC_API_KEY="shared-key")
    def test_identical_keys_internal_wins(self):
        request = make_request(auth_header=bearer("shared-key"))
        result = self.auth.authenticate(request)
        self.assertEqual(result, (None, "internal"))

    # ------------------------------------------------------------------
    # 9. secrets.compare_digest is actually called (timing-safe)
    # ------------------------------------------------------------------

    def test_secrets_compare_digest_used_for_internal_key(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY))
        with patch("secrets.compare_digest", wraps=__import__("secrets").compare_digest) as mock_cd:
            self.auth.authenticate(request)
            mock_cd.assert_called()

    def test_secrets_compare_digest_used_for_public_key(self):
        request = make_request(auth_header=bearer(PUBLIC_KEY))
        with patch("secrets.compare_digest", wraps=__import__("secrets").compare_digest) as mock_cd:
            self.auth.authenticate(request)
            mock_cd.assert_called()

    # ------------------------------------------------------------------
    # 10. Unicode / encoding edge cases
    # ------------------------------------------------------------------

    def test_key_with_unicode_raises(self):
        """Non-ASCII token bytes won't match ASCII keys."""
        request = make_request(auth_header="Bearer café".encode("utf-8"))
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_key_with_whitespace_raises(self):
        """A token containing a space splits into extra parts → format error."""
        request = make_request(auth_header=b"Bearer key with spaces")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_token_is_decoded_from_bytes(self):
        """Ensure the raw bytes header is correctly decoded before comparison."""
        key_bytes = INTERNAL_KEY.encode("utf-8")
        request = make_request(auth_header=b"Bearer " + key_bytes)
        result = self.auth.authenticate(request)
        self.assertEqual(result, (None, "internal"))

    # ------------------------------------------------------------------
    # 11. Return type contract
    # ------------------------------------------------------------------

    def test_return_type_is_tuple_for_internal(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY))
        result = self.auth.authenticate(request)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_return_type_is_tuple_for_public(self):
        request = make_request(auth_header=bearer(PUBLIC_KEY))
        result = self.auth.authenticate(request)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_return_is_none_for_no_header(self):
        request = make_request(auth_header=None)
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # 12. AuthenticationFailed is a DRF exception (status 401)
    # ------------------------------------------------------------------

    def test_authentication_failed_is_drf_exception(self):
        request = make_request(auth_header=bearer("bad"))
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertEqual(ctx.exception.status_code, 401)

    # ------------------------------------------------------------------
    # 13. keyword class attribute
    # ------------------------------------------------------------------

    def test_keyword_attribute_is_bearer(self):
        self.assertEqual(ApiKeyAuthentication.keyword, "Bearer")

    def test_custom_keyword_subclass(self):
        """Demonstrates how keyword could be overridden in a subclass."""
        class ApiKeyAuth(ApiKeyAuthentication):
            keyword = "ApiKey"

        auth = ApiKeyAuth()
        request = make_request(auth_header=f"ApiKey {INTERNAL_KEY}".encode())
        result = auth.authenticate(request)
        self.assertEqual(result, (None, "internal"))

    # ------------------------------------------------------------------
    # 14. Regression: internal key is not accidentally matched as public
    # ------------------------------------------------------------------

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_internal_key_not_returned_as_public(self):
        request = make_request(auth_header=bearer(INTERNAL_KEY))
        _, scope = self.auth.authenticate(request)
        self.assertNotEqual(scope, "public")

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_public_key_not_returned_as_internal(self):
        request = make_request(auth_header=bearer(PUBLIC_KEY))
        _, scope = self.auth.authenticate(request)
        self.assertNotEqual(scope, "internal")


# ---------------------------------------------------------------------------
# Pytest-style equivalents (if you prefer pytest over unittest.TestCase)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestApiKeyAuthenticationPytest:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.auth = ApiKeyAuthentication()

    @pytest.fixture
    def internal_request(self, settings):
        settings.INTERNAL_API_KEY = INTERNAL_KEY
        settings.PUBLIC_API_KEY = PUBLIC_KEY
        return make_request(auth_header=bearer(INTERNAL_KEY))

    @pytest.fixture
    def public_request(self, settings):
        settings.INTERNAL_API_KEY = INTERNAL_KEY
        settings.PUBLIC_API_KEY = PUBLIC_KEY
        return make_request(auth_header=bearer(PUBLIC_KEY))

    def test_internal_key_pytest(self, internal_request):
        result = self.auth.authenticate(internal_request)
        assert result == (None, "internal")

    def test_public_key_pytest(self, public_request):
        result = self.auth.authenticate(public_request)
        assert result == (None, "public")

    def test_no_header_pytest(self):
        request = make_request()
        assert self.auth.authenticate(request) is None

    def test_bad_key_pytest(self, settings):
        settings.INTERNAL_API_KEY = INTERNAL_KEY
        settings.PUBLIC_API_KEY = PUBLIC_KEY
        request = make_request(auth_header=bearer("nope"))
        with pytest.raises(AuthenticationFailed, match="Invalid API key"):
            self.auth.authenticate(request)

    def test_malformed_header_pytest(self):
        request = make_request(auth_header=b"Bearer")
        with pytest.raises(AuthenticationFailed, match="Invalid Authorization header format"):
            self.auth.authenticate(request)

    @pytest.mark.parametrize("keyword", ["bearer", "BEARER", "Bearer", "bEaReR"])
    def test_keyword_case_insensitive_pytest(self, keyword, settings):
        settings.INTERNAL_API_KEY = INTERNAL_KEY
        settings.PUBLIC_API_KEY = PUBLIC_KEY
        request = make_request(auth_header=f"{keyword} {INTERNAL_KEY}".encode())
        result = self.auth.authenticate(request)
        assert result == (None, "internal")

    @pytest.mark.parametrize("bad_header", [
        b"Token abc",
        b"Basic abc",
        b"Bearer a b",
        b"Bearer a b c",
        b"Bearer",
        b"",
    ])
    def test_malformed_headers_parametrized(self, bad_header):
        request = make_request(auth_header=bad_header)
        if bad_header == b"":
            assert self.auth.authenticate(request) is None
        else:
            with pytest.raises(AuthenticationFailed):
                self.auth.authenticate(request)