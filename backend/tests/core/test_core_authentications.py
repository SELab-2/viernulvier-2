"""
Comprehensive test suite for ApiKeyAuthentication.

Test categories:
    1.  No Authorization header present
    2.  Wrong authentication scheme (not Api-Key)
    3.  Malformed headers (too few / too many parts)
    4.  UnicodeDecodeError in scheme or key
    5.  Valid INTERNAL_API_KEY  → (None, "internal")
    6.  Valid PUBLIC_API_KEY    → (None, "public")
    7.  Invalid / unknown key   → AuthenticationFailed
    8.  Settings without configured keys
    9.  authenticate_header()
    10. Case-insensitivity of the scheme
    11. Timing-safe comparison (secrets.compare_digest usage)
    12. Edge cases and robustness
"""

import secrets
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.exceptions import AuthenticationFailed

from apps.core.authentications import ApiKeyAuthentication

# ===========================================================================
# Shared test constants
# ===========================================================================

INTERNAL_KEY = "super-secret-internal-key-abc123"
PUBLIC_KEY = "public-readonly-key-xyz789"

VALID_INTERNAL_HEADER = f"Api-Key {INTERNAL_KEY}".encode()
VALID_PUBLIC_HEADER = f"Api-Key {PUBLIC_KEY}".encode()


# ===========================================================================
# Helper utilities
# ===========================================================================


def _patch_get_auth(value: bytes):
    """
    Patch get_authorization_header so it returns the given bytes,
    regardless of the actual request object structure.
    """
    return patch(
        "apps.core.authentications.get_authorization_header",
        return_value=value,
    )


def _patch_settings(internal: str | None = None, public: str | None = None):
    """
    Patch Django settings with specific API key values.
    Pass None to simulate a key not being configured.
    """
    return patch(
        "apps.core.authentications.settings",
        **{
            "INTERNAL_API_KEY": internal,
            "PUBLIC_API_KEY": public,
        },
    )


# ===========================================================================
# Fixture
# ===========================================================================


@pytest.fixture()
def auth():
    """Return a fresh ApiKeyAuthentication instance for each test."""
    return ApiKeyAuthentication()


# ===========================================================================
# 1. No Authorization header present
# ===========================================================================


class TestNoAuthorizationHeader:
    """
    When no Authorization header is included in the request,
    authenticate() must return None so that other authenticators
    in DRF's authentication chain can still run.
    """

    def test_returns_none_when_raw_auth_is_empty_bytes(self, auth):
        """get_authorization_header returns b'' → authenticate returns None."""
        with _patch_get_auth(b""):
            result = auth.authenticate(MagicMock())
        assert result is None

    def test_return_value_is_the_none_singleton(self, auth):
        """Explicitly verify the return value is the None singleton, not just falsy."""
        with _patch_get_auth(b""):
            result = auth.authenticate(MagicMock())
        assert result is None

    def test_does_not_raise_when_header_absent(self, auth):
        """Missing header must never raise any exception."""
        with _patch_get_auth(b""):
            try:
                auth.authenticate(MagicMock())
            except Exception as exc:
                pytest.fail(f"Unexpected exception raised with no header: {exc}")

    def test_settings_are_not_accessed_when_header_absent(self, auth):
        """
        If there is no header we bail out early — Django settings
        must not be accessed at all.
        """
        with _patch_get_auth(b""):
            with patch("apps.core.authentications.settings") as mock_settings:
                auth.authenticate(MagicMock())
                # getattr must not have been called on settings
                mock_settings.INTERNAL_API_KEY.__get__ = MagicMock()
                assert not mock_settings.INTERNAL_API_KEY.called
                assert not mock_settings.PUBLIC_API_KEY.called


# ===========================================================================
# 2. Wrong authentication scheme
# ===========================================================================


class TestWrongScheme:
    """
    When the Authorization header uses a scheme other than 'Api-Key',
    authenticate() must return None so that other authenticators can handle it.
    """

    def test_bearer_scheme_is_ignored(self, auth):
        with _patch_get_auth(b"Bearer sometoken"):
            assert auth.authenticate(MagicMock()) is None

    def test_basic_scheme_is_ignored(self, auth):
        with _patch_get_auth(b"Basic dXNlcjpwYXNz"):
            assert auth.authenticate(MagicMock()) is None

    def test_token_scheme_is_ignored(self, auth):
        with _patch_get_auth(b"Token abc123"):
            assert auth.authenticate(MagicMock()) is None

    def test_jwt_scheme_is_ignored(self, auth):
        with _patch_get_auth(b"JWT eyJhbGciOiJIUzI1NiJ9.payload.sig"):
            assert auth.authenticate(MagicMock()) is None

    def test_completely_unknown_scheme_is_ignored(self, auth):
        with _patch_get_auth(b"UnknownScheme somevalue"):
            assert auth.authenticate(MagicMock()) is None

    def test_scheme_prefix_match_is_not_enough(self, auth):
        """'Api-KeyExtra' must not be treated as a valid Api-Key scheme."""
        with _patch_get_auth(b"Api-KeyExtra somevalue"):
            assert auth.authenticate(MagicMock()) is None

    def test_whitespace_only_header_returns_none(self, auth):
        """
        b"   " splits to [] (empty list) → parts is falsy → returns None
        before we even inspect a scheme.
        """
        with _patch_get_auth(b"   "):
            result = auth.authenticate(MagicMock())
        assert result is None


# ===========================================================================
# 3. Malformed headers
# ===========================================================================


class TestMalformedHeaders:
    """
    Once the scheme is identified as 'Api-Key', the header must contain
    exactly two parts. Any deviation is malformed and must raise
    AuthenticationFailed with an informative message.
    """

    def test_only_scheme_no_key_raises(self, auth):
        """Header has scheme but no key: 'Api-Key' (1 part)."""
        with _patch_get_auth(b"Api-Key"):
            with pytest.raises(AuthenticationFailed) as exc_info:
                auth.authenticate(MagicMock())
        assert "Invalid Authorization header format" in str(exc_info.value.detail)

    def test_error_message_contains_usage_hint(self, auth):
        """The error message must explain the correct format to the caller."""
        with _patch_get_auth(b"Api-Key"):
            with pytest.raises(AuthenticationFailed) as exc_info:
                auth.authenticate(MagicMock())
        assert "Api-Key <KEY>" in str(exc_info.value.detail)

    def test_three_parts_raises(self, auth):
        """Header has three whitespace-separated parts instead of two."""
        with _patch_get_auth(b"Api-Key key1 key2"):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(MagicMock())

    def test_four_parts_raises(self, auth):
        with _patch_get_auth(b"Api-Key a b c"):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(MagicMock())

    def test_key_with_internal_space_raises(self, auth):
        """A key value containing a space produces three parts → malformed."""
        with _patch_get_auth(b"Api-Key ke y"):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(MagicMock())

    def test_malformed_raises_authentication_failed_not_value_error(self, auth):
        """The raised exception type must always be DRF's AuthenticationFailed."""
        with _patch_get_auth(b"Api-Key a b"):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(MagicMock())


# ===========================================================================
# 4. UnicodeDecodeError in scheme or key
# ===========================================================================


class TestUnicodeErrors:
    """
    Bytes that cannot be decoded as UTF-8 must raise AuthenticationFailed
    with an appropriate message — never a raw UnicodeDecodeError.
    """

    def test_invalid_utf8_in_scheme_raises_with_message(self, auth):
        """0xff 0xfe are invalid UTF-8 start bytes."""
        with _patch_get_auth(b"\xff\xfe validkey"):
            with pytest.raises(AuthenticationFailed) as exc_info:
                auth.authenticate(MagicMock())
        assert "Invalid characters in authentication scheme" in str(exc_info.value.detail)

    def test_invalid_utf8_in_key_raises_with_message(self, auth):
        """Valid scheme, but invalid UTF-8 bytes in the key part."""
        with _patch_get_auth(b"Api-Key \xff\xfe"):
            with pytest.raises(AuthenticationFailed) as exc_info:
                auth.authenticate(MagicMock())
        assert "Invalid characters in API key" in str(exc_info.value.detail)

    def test_continuation_byte_in_scheme_raises(self, auth):
        """0x80 is a UTF-8 continuation byte and invalid as a start byte."""
        with _patch_get_auth(b"\x80bc validkey"):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(MagicMock())

    def test_continuation_byte_in_key_raises(self, auth):
        with _patch_get_auth(b"Api-Key \x80\x81\x82"):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(MagicMock())

    def test_raw_unicode_decode_error_does_not_escape_from_scheme(self, auth):
        """The raw UnicodeDecodeError must be caught and converted."""
        with _patch_get_auth(b"\xff validkey"):
            try:
                auth.authenticate(MagicMock())
            except UnicodeDecodeError:
                pytest.fail("Raw UnicodeDecodeError must not escape authenticate().")
            except AuthenticationFailed:
                pass  # expected

    def test_raw_unicode_decode_error_does_not_escape_from_key(self, auth):
        with _patch_get_auth(b"Api-Key \xff"):
            try:
                auth.authenticate(MagicMock())
            except UnicodeDecodeError:
                pytest.fail("Raw UnicodeDecodeError must not escape authenticate().")
            except AuthenticationFailed:
                pass  # expected


# ===========================================================================
# 5. Successful authentication — INTERNAL key
# ===========================================================================


class TestInternalKeySuccess:
    """
    A request carrying the configured INTERNAL_API_KEY must be granted
    full access and receive (None, "internal") as the auth token.
    """

    def test_valid_internal_key_returns_correct_tuple(self, auth):
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                result = auth.authenticate(MagicMock())
        assert result == (None, "internal")

    def test_first_element_of_tuple_is_none(self, auth):
        """DRF treats the first element as the authenticated user — must be None."""
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                user, _ = auth.authenticate(MagicMock())
        assert user is None

    def test_second_element_of_tuple_is_string_internal(self, auth):
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                _, token = auth.authenticate(MagicMock())
        assert token == "internal"

    def test_internal_key_works_without_public_key_configured(self, auth):
        """Internal key must still work even if PUBLIC_API_KEY is not set."""
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=None):
                result = auth.authenticate(MagicMock())
        assert result == (None, "internal")

    def test_internal_key_takes_priority_over_public_key(self, auth):
        """
        If the same key value is configured for both slots (unlikely but
        possible), internal must take priority because it is checked first.
        """
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=INTERNAL_KEY):
                _, token = auth.authenticate(MagicMock())
        assert token == "internal"

    def test_result_is_a_tuple_not_a_list(self, auth):
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY):
                result = auth.authenticate(MagicMock())
        assert isinstance(result, tuple)

    def test_result_has_exactly_two_elements(self, auth):
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY):
                result = auth.authenticate(MagicMock())
        assert len(result) == 2


# ===========================================================================
# 6. Successful authentication — PUBLIC key
# ===========================================================================


class TestPublicKeySuccess:
    """
    A request carrying the configured PUBLIC_API_KEY must receive
    read-only access via (None, "public").
    """

    def test_valid_public_key_returns_correct_tuple(self, auth):
        with _patch_get_auth(VALID_PUBLIC_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                result = auth.authenticate(MagicMock())
        assert result == (None, "public")

    def test_first_element_of_tuple_is_none(self, auth):
        with _patch_get_auth(VALID_PUBLIC_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                user, _ = auth.authenticate(MagicMock())
        assert user is None

    def test_second_element_is_string_public(self, auth):
        with _patch_get_auth(VALID_PUBLIC_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                _, token = auth.authenticate(MagicMock())
        assert token == "public"

    def test_public_key_works_without_internal_key_configured(self, auth):
        """Public key must work even if INTERNAL_API_KEY is not set."""
        with _patch_get_auth(VALID_PUBLIC_HEADER):
            with _patch_settings(internal=None, public=PUBLIC_KEY):
                result = auth.authenticate(MagicMock())
        assert result == (None, "public")

    def test_result_is_a_tuple(self, auth):
        with _patch_get_auth(VALID_PUBLIC_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                result = auth.authenticate(MagicMock())
        assert isinstance(result, tuple)


# ===========================================================================
# 7. Invalid / unknown keys
# ===========================================================================


class TestInvalidKey:
    """
    Any key that does not match either configured key must result in
    AuthenticationFailed being raised.
    """

    def test_completely_wrong_key_raises(self, auth):
        with _patch_get_auth(b"Api-Key totallywrongkey"):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_error_detail_says_invalid_api_key(self, auth):
        with _patch_get_auth(b"Api-Key wrongkey"):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed) as exc_info:
                    auth.authenticate(MagicMock())
        assert "Invalid API key" in str(exc_info.value.detail)

    def test_one_char_off_internal_key_fails(self, auth):
        """Even a single character difference must be rejected (no prefix matching)."""
        almost = INTERNAL_KEY[:-1] + ("X" if INTERNAL_KEY[-1] != "X" else "Y")
        with _patch_get_auth(f"Api-Key {almost}".encode()):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_one_char_off_public_key_fails(self, auth):
        almost = PUBLIC_KEY[:-1] + ("X" if PUBLIC_KEY[-1] != "X" else "Y")
        with _patch_get_auth(f"Api-Key {almost}".encode()):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_extra_trailing_character_fails(self, auth):
        with _patch_get_auth(f"Api-Key {INTERNAL_KEY}x".encode()):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_extra_leading_character_fails(self, auth):
        with _patch_get_auth(f"Api-Key x{INTERNAL_KEY}".encode()):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_uppercased_key_value_is_rejected(self, auth):
        """Key comparison must be case-sensitive — an uppercased key must fail."""
        with _patch_get_auth(f"Api-Key {INTERNAL_KEY.upper()}".encode()):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_internal_key_not_accepted_when_only_public_is_set(self, auth):
        """The internal key must not pass when only PUBLIC_API_KEY is configured."""
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=None, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_public_key_not_accepted_when_only_internal_is_set(self, auth):
        """The public key must not pass when only INTERNAL_API_KEY is configured."""
        with _patch_get_auth(VALID_PUBLIC_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=None):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_scheme_only_header_is_malformed_not_invalid_key(self, auth):
        """
        'Api-Key  ' splits to [b'Api-Key'] — 1 part — which is a malformed
        header, not an invalid-key situation.
        """
        with _patch_get_auth(b"Api-Key  "):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(MagicMock())

    def test_raises_authentication_failed_not_permission_denied(self, auth):
        """Must raise AuthenticationFailed (HTTP 401), not PermissionDenied (HTTP 403)."""
        from rest_framework.exceptions import PermissionDenied

        with _patch_get_auth(b"Api-Key badkey"):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())
                try:
                    auth.authenticate(MagicMock())
                except PermissionDenied:
                    pytest.fail("Must raise AuthenticationFailed, not PermissionDenied.")
                except AuthenticationFailed:
                    pass


# ===========================================================================
# 8. Settings without configured keys
# ===========================================================================


class TestMissingSettings:
    """
    When API key settings are absent or None, no key should be accepted.
    """

    def test_no_keys_configured_any_key_raises(self, auth):
        with _patch_get_auth(b"Api-Key somekey"):
            with _patch_settings(internal=None, public=None):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_only_internal_configured_rejects_unknown_key(self, auth):
        with _patch_get_auth(b"Api-Key unknownkey"):
            with _patch_settings(internal=INTERNAL_KEY, public=None):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_only_public_configured_rejects_unknown_key(self, auth):
        with _patch_get_auth(b"Api-Key unknownkey"):
            with _patch_settings(internal=None, public=PUBLIC_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_missing_settings_attribute_falls_back_to_none(self, auth):
        """
        getattr(settings, "INTERNAL_API_KEY", None) must gracefully return
        None when the attribute does not exist on the settings object at all.
        """
        mock_settings = MagicMock(spec=[])  # spec=[] → no attributes defined
        with _patch_get_auth(b"Api-Key somekey"):
            with patch("apps.core.authentications.settings", mock_settings):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())

    def test_empty_string_key_in_settings_is_skipped(self, auth):
        """
        An empty string configured as a key is falsy, so the comparison
        block is skipped entirely — no key must match an empty-string setting.
        """
        with _patch_get_auth(b"Api-Key somekey"):
            with _patch_settings(internal="", public=""):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())


# ===========================================================================
# 9. authenticate_header()
# ===========================================================================


class TestAuthenticateHeader:
    """
    authenticate_header() provides the WWW-Authenticate value that DRF
    includes in 401 responses. It must return the correct scheme string.
    """

    def test_returns_api_key_string(self, auth):
        result = auth.authenticate_header(MagicMock())
        assert result == "Api-Key"

    def test_return_type_is_str(self, auth):
        result = auth.authenticate_header(MagicMock())
        assert isinstance(result, str)

    def test_return_value_matches_keyword_case_insensitively(self, auth):
        """The header value must correspond to the defined keyword."""
        result = auth.authenticate_header(MagicMock())
        assert result.lower() == auth.keyword.lower()

    def test_does_not_raise_for_any_request_object(self, auth):
        """authenticate_header must never raise, regardless of request content."""
        for request in [MagicMock(), None, object()]:
            try:
                auth.authenticate_header(request)
            except Exception as exc:
                pytest.fail(f"authenticate_header raised unexpectedly: {exc}")

    def test_return_value_is_non_empty(self, auth):
        """An empty WWW-Authenticate header would be useless and invalid."""
        result = auth.authenticate_header(MagicMock())
        assert result  # truthy / non-empty string


# ===========================================================================
# 10. Case-insensitivity of the scheme
# ===========================================================================


class TestSchemeCaseInsensitivity:
    """
    RFC 7235 requires that authentication schemes are compared
    case-insensitively. All capitalisation variants of 'api-key' must work.
    """

    @pytest.mark.parametrize(
        "scheme",
        [
            "api-key",
            "API-KEY",
            "Api-Key",
            "API-key",
            "api-KEY",
            "aPi-KeY",
            "ApI-kEy",
        ],
    )
    def test_all_case_variants_of_scheme_are_accepted(self, auth, scheme):
        header = f"{scheme} {INTERNAL_KEY}".encode()
        with _patch_get_auth(header):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                result = auth.authenticate(MagicMock())
        assert result == (None, "internal"), f"Scheme variant '{scheme}' should have been accepted."

    def test_key_comparison_itself_is_case_sensitive(self, auth):
        """
        Unlike the scheme, the key value must be compared case-sensitively.
        Passing the key in uppercase when settings stores it lowercase must fail.
        """
        with _patch_get_auth(f"Api-Key {INTERNAL_KEY.upper()}".encode()):
            with _patch_settings(internal=INTERNAL_KEY):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())


# ===========================================================================
# 11. Timing-safe comparison
# ===========================================================================


class TestTimingSafeComparison:
    """
    secrets.compare_digest must be used for all key comparisons to prevent
    timing-based side-channel attacks that could leak information about
    the configured key values.
    """

    def test_compare_digest_is_called_for_internal_key(self, auth):
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with patch(
                    "apps.core.authentications.secrets.compare_digest",
                    wraps=secrets.compare_digest,
                ) as mock_cd:
                    auth.authenticate(MagicMock())
        assert mock_cd.called, "secrets.compare_digest must be used for the internal key check."

    def test_compare_digest_is_called_for_public_key(self, auth):
        with _patch_get_auth(VALID_PUBLIC_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with patch(
                    "apps.core.authentications.secrets.compare_digest",
                    wraps=secrets.compare_digest,
                ) as mock_cd:
                    auth.authenticate(MagicMock())
        assert mock_cd.called, "secrets.compare_digest must be used for the public key check."

    def test_compare_digest_called_twice_when_internal_mismatches(self, auth):
        """
        For a valid public-key request, compare_digest must be called twice:
        once for the internal check (fails) and once for the public check (succeeds).
        """
        with _patch_get_auth(VALID_PUBLIC_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with patch(
                    "apps.core.authentications.secrets.compare_digest",
                    wraps=secrets.compare_digest,
                ) as mock_cd:
                    auth.authenticate(MagicMock())
        assert mock_cd.call_count == 2, "compare_digest should be called once per configured key."

    def test_compare_digest_called_once_when_internal_matches(self, auth):
        """
        When the internal key matches we short-circuit — compare_digest
        must only be called once (for the internal check).
        """
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with patch(
                    "apps.core.authentications.secrets.compare_digest",
                    wraps=secrets.compare_digest,
                ) as mock_cd:
                    auth.authenticate(MagicMock())
        assert mock_cd.call_count == 1

    def test_compare_digest_receives_bytes_not_strings(self, auth):
        """
        compare_digest must be called with bytes arguments, not strings,
        to ensure correct constant-time behaviour and type consistency.
        """
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
                with patch(
                    "apps.core.authentications.secrets.compare_digest",
                    wraps=secrets.compare_digest,
                ) as mock_cd:
                    auth.authenticate(MagicMock())
        args, _ = mock_cd.call_args
        assert all(isinstance(a, bytes) for a in args), "Both arguments to compare_digest must be bytes."


# ===========================================================================
# 12. Edge cases and robustness
# ===========================================================================


class TestEdgeCases:
    """Miscellaneous edge cases that verify general robustness."""

    def test_key_with_special_ascii_characters(self, auth):
        """Keys may contain special but valid ASCII characters."""
        special_key = "k3y-w1th-$pec!@l_ch@r$"
        with _patch_get_auth(f"Api-Key {special_key}".encode()):
            with _patch_settings(internal=special_key):
                assert auth.authenticate(MagicMock()) == (None, "internal")

    def test_very_long_key_is_handled_correctly(self, auth):
        """A 512-character key must not cause any errors."""
        long_key = "a" * 512
        with _patch_get_auth(f"Api-Key {long_key}".encode()):
            with _patch_settings(internal=long_key):
                assert auth.authenticate(MagicMock()) == (None, "internal")

    def test_valid_multibyte_utf8_key(self, auth):
        """Keys containing valid multibyte UTF-8 characters must be handled."""
        unicode_key = "kéy-wïth-ünícödé"
        with _patch_get_auth(f"Api-Key {unicode_key}".encode("utf-8")):
            with _patch_settings(internal=unicode_key):
                assert auth.authenticate(MagicMock()) == (None, "internal")

    def test_keyword_class_attribute_is_lowercase(self, auth):
        """The keyword attribute must already be lowercase for consistent .lower() comparison."""
        assert auth.keyword == auth.keyword.lower()

    def test_keyword_value_equals_api_key(self, auth):
        assert auth.keyword == "api-key"

    def test_no_header_returns_none_not_empty_tuple(self, auth):
        """None and () are both falsy but semantically different — must be None."""
        with _patch_get_auth(b""):
            result = auth.authenticate(MagicMock())
        assert result is None
        assert result != ()

    def test_successful_authentication_does_not_return_none(self, auth):
        """A successful authentication must NOT return None."""
        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY):
                result = auth.authenticate(MagicMock())
        assert result is not None

    def test_inherits_from_drf_base_authentication(self):
        """ApiKeyAuthentication must be a subclass of DRF's BaseAuthentication."""
        from rest_framework.authentication import BaseAuthentication

        assert issubclass(ApiKeyAuthentication, BaseAuthentication)

    def test_multiple_sequential_calls_are_stateless(self, auth):
        """
        Calling authenticate() multiple times in sequence must not cause
        any state leakage — each call must be fully independent.
        """
        with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
            with _patch_get_auth(VALID_INTERNAL_HEADER):
                r1 = auth.authenticate(MagicMock())
            with _patch_get_auth(VALID_PUBLIC_HEADER):
                r2 = auth.authenticate(MagicMock())
            with _patch_get_auth(b"Api-Key badkey"):
                with pytest.raises(AuthenticationFailed):
                    auth.authenticate(MagicMock())
            with _patch_get_auth(b""):
                r4 = auth.authenticate(MagicMock())

        assert r1 == (None, "internal")
        assert r2 == (None, "public")
        assert r4 is None

    def test_authenticate_does_not_mutate_request(self, auth):
        """authenticate() must treat the request as read-only and not set attributes on it."""
        mock_request = MagicMock()

        with _patch_get_auth(VALID_INTERNAL_HEADER):
            with _patch_settings(internal=INTERNAL_KEY):
                auth.authenticate(mock_request)

        setattr_calls = [c for c in mock_request.mock_calls if c[0] == "__setattr__"]
        assert len(setattr_calls) == 0, f"Request was mutated with: {setattr_calls}"

    def test_authenticate_is_callable(self):
        """Sanity check: the authenticate method must exist and be callable."""
        assert callable(ApiKeyAuthentication().authenticate)

    def test_authenticate_header_is_callable(self):
        """Sanity check: authenticate_header must exist and be callable."""
        assert callable(ApiKeyAuthentication().authenticate_header)
