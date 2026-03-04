"""
Tests for apps/core/authentications.py — ApiKeyAuthentication

Covers:
- No Authorization header -> returns None (unauthenticated, not an error)
- Malformed header (wrong scheme, too few/many parts) -> AuthenticationFailed
- Valid internal key -> returns (None, "internal")
- Valid public key  -> returns (None, "public")
- Unknown key       -> AuthenticationFailed
- Settings not configured (missing / None key)
- Timing-safe comparison (secrets.compare_digest)
- Keyword / scheme matching is case-insensitive
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework.exceptions import AuthenticationFailed

from apps.core.authentications import ApiKeyAuthentication

INTERNAL_KEY = "internal-secret-key"
PUBLIC_KEY = "public-secret-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(auth_header=None):
    request = MagicMock()
    request.headers = {}
    if auth_header is not None:
        request.headers["Authorization"] = auth_header
    return request


# ---------------------------------------------------------------------------
# No header
# ---------------------------------------------------------------------------

class TestApiKeyAuthenticationNoHeader(TestCase):

    def setUp(self):
        self.auth = ApiKeyAuthentication()

    def test_returns_none_when_no_header(self):
        """Missing header must return None so other authenticators can run."""
        request = make_request()
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_returns_none_not_raises(self):
        """Must NOT raise — returning None is the correct DRF contract."""
        request = make_request()
        try:
            _ = self.auth.authenticate(request)
        except Exception as exc:
            self.fail(f"authenticate() raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# Malformed headers
# ---------------------------------------------------------------------------

class TestApiKeyAuthenticationMalformedHeader(TestCase):

    def setUp(self):
        self.auth = ApiKeyAuthentication()

    def test_raises_when_only_one_part(self):
        request = make_request(auth_header="justonetoken")
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertIn("Invalid header format", str(ctx.exception.detail))

    def test_raises_when_three_parts(self):
        request = make_request(auth_header="Api-Key key extra")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_raises_when_wrong_scheme_bearer(self):
        request = make_request(auth_header="Bearer sometoken")
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertIn("Invalid header format", str(ctx.exception.detail))

    def test_raises_when_wrong_scheme_token(self):
        request = make_request(auth_header="Token sometoken")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_raises_when_empty_string_header(self):
        request = make_request(auth_header="")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_raises_when_only_whitespace(self):
        request = make_request(auth_header="   ")
        with self.assertRaises((AuthenticationFailed, Exception)):
            self.auth.authenticate(request)


# ---------------------------------------------------------------------------
# Scheme case-insensitivity
# ---------------------------------------------------------------------------

class TestApiKeyAuthenticationScheme(TestCase):

    def setUp(self):
        self.auth = ApiKeyAuthentication()

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_scheme_lowercase_accepted(self):
        request = make_request(auth_header=f"api-key {INTERNAL_KEY}")
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_scheme_uppercase_accepted(self):
        request = make_request(auth_header=f"API-KEY {INTERNAL_KEY}")
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_scheme_mixed_case_accepted(self):
        request = make_request(auth_header=f"Api-Key {INTERNAL_KEY}")
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_scheme_weird_case_accepted(self):
        request = make_request(auth_header=f"aPi-KeY {INTERNAL_KEY}")
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)


# ---------------------------------------------------------------------------
# Successful authentication
# ---------------------------------------------------------------------------

class TestApiKeyAuthenticationSuccess(TestCase):

    def setUp(self):
        self.auth = ApiKeyAuthentication()

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_internal_key_returns_tuple(self):
        request = make_request(auth_header=f"Api-Key {INTERNAL_KEY}")
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_internal_key_user_is_none(self):
        request = make_request(auth_header=f"Api-Key {INTERNAL_KEY}")
        user, _ = self.auth.authenticate(request)
        self.assertIsNone(user)

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_internal_key_auth_is_internal(self):
        request = make_request(auth_header=f"Api-Key {INTERNAL_KEY}")
        _, auth = self.auth.authenticate(request)
        self.assertEqual(auth, "internal")

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_public_key_returns_tuple(self):
        request = make_request(auth_header=f"Api-Key {PUBLIC_KEY}")
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, tuple)

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_public_key_user_is_none(self):
        request = make_request(auth_header=f"Api-Key {PUBLIC_KEY}")
        user, _ = self.auth.authenticate(request)
        self.assertIsNone(user)

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_public_key_auth_is_public(self):
        request = make_request(auth_header=f"Api-Key {PUBLIC_KEY}")
        _, auth = self.auth.authenticate(request)
        self.assertEqual(auth, "public")

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_internal_and_public_keys_are_distinct(self):
        """Internal and public keys must not be interchangeable."""
        req_internal = make_request(auth_header=f"Api-Key {INTERNAL_KEY}")
        req_public = make_request(auth_header=f"Api-Key {PUBLIC_KEY}")
        _, auth_i = self.auth.authenticate(req_internal)
        _, auth_p = self.auth.authenticate(req_public)
        self.assertNotEqual(auth_i, auth_p)


# ---------------------------------------------------------------------------
# Unknown / wrong key
# ---------------------------------------------------------------------------

class TestApiKeyAuthenticationFailure(TestCase):

    def setUp(self):
        self.auth = ApiKeyAuthentication()

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_wrong_key_raises_auth_failed(self):
        request = make_request(auth_header="Api-Key completely-wrong-key")
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertIn("Invalid API key", str(ctx.exception.detail))

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_partial_key_match_is_rejected(self):
        """A key that is a prefix of the real key must not authenticate."""
        request = make_request(auth_header=f"Api-Key {INTERNAL_KEY[:5]}")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_empty_key_value_raises(self):
        """Header present but key part is empty."""
        request = make_request(auth_header="Api-Key ")
        with self.assertRaises((AuthenticationFailed, Exception)):
            self.auth.authenticate(request)


# ---------------------------------------------------------------------------
# Missing / unconfigured settings
# ---------------------------------------------------------------------------

class TestApiKeyAuthenticationMissingSettings(TestCase):

    def setUp(self):
        self.auth = ApiKeyAuthentication()

    @override_settings(INTERNAL_API_KEY=None, PUBLIC_API_KEY=None)
    def test_both_keys_none_raises_auth_failed(self):
        request = make_request(auth_header="Api-Key anykey")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @override_settings(INTERNAL_API_KEY=None, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_internal_key_none_falls_through_to_public(self):
        """If INTERNAL_API_KEY is None it should skip and try PUBLIC_API_KEY."""
        request = make_request(auth_header=f"Api-Key {PUBLIC_KEY}")
        _, auth = self.auth.authenticate(request)
        self.assertEqual(auth, "public")

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=None)
    def test_public_key_none_still_accepts_internal(self):
        request = make_request(auth_header=f"Api-Key {INTERNAL_KEY}")
        _, auth = self.auth.authenticate(request)
        self.assertEqual(auth, "internal")

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=None)
    def test_public_key_none_rejects_unknown_key(self):
        request = make_request(auth_header="Api-Key unknownkey")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)


# ---------------------------------------------------------------------------
# Timing-safe comparison
# ---------------------------------------------------------------------------

class TestApiKeyAuthenticationTimingSafe(TestCase):

    def setUp(self):
        self.auth = ApiKeyAuthentication()

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_uses_compare_digest_for_internal_key(self):
        request = make_request(auth_header=f"Api-Key {INTERNAL_KEY}")
        with patch(
            "apps.core.authentications.secrets.compare_digest", return_value=True
            ) as mock_cd:
            self.auth.authenticate(request)
            # compare_digest must have been called at least once
            self.assertTrue(mock_cd.called)
            # The actual key must have been passed as one of the arguments
            calls_args = [call.args for call in mock_cd.call_args_list]
            self.assertTrue(
                any(INTERNAL_KEY in args for args in calls_args),
                "compare_digest was not called with the internal key",
            )

    @override_settings(INTERNAL_API_KEY=INTERNAL_KEY, PUBLIC_API_KEY=PUBLIC_KEY)
    def test_uses_compare_digest_for_public_key(self):
        request = make_request(auth_header=f"Api-Key {PUBLIC_KEY}")
        with patch(
            "apps.core.authentications.secrets.compare_digest", 
            side_effect=[False, True]
        ) as mock_cd:
            self.auth.authenticate(request)
            self.assertTrue(mock_cd.called)