"""
Focused test suite for ApiKeyAuthentication.

The project authenticates requests via the ``X-API-Key`` header and maps
matching keys to either ``internal`` or ``public`` access.
"""

import secrets
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.core.authentications import ApiKeyAuthentication

INTERNAL_KEY = "super-secret-internal-key-abc123"
PUBLIC_KEY = "public-readonly-key-xyz789"


def _make_request(api_key: str | bytes | None = None):
    request = MagicMock()
    request.META = {}
    if api_key is not None:
        request.META["HTTP_X_API_KEY"] = api_key
    return request


def _patch_settings(internal: str | None = None, public: str | None = None):
    return patch(
        "apps.core.authentications.settings",
        **{
            "INTERNAL_API_KEY": internal,
            "PUBLIC_API_KEY": public,
        },
    )


@pytest.fixture()
def auth():
    return ApiKeyAuthentication()


class TestMissingHeader:
    def test_returns_none_when_header_is_absent(self, auth):
        assert auth.authenticate(_make_request()) is None

    def test_returns_none_when_header_is_empty_string(self, auth):
        assert auth.authenticate(_make_request("")) is None

    def test_returns_none_when_header_is_empty_bytes(self, auth):
        assert auth.authenticate(_make_request(b"")) is None


class TestSuccessfulAuthentication:
    def test_valid_internal_key_returns_internal_scope(self, auth):
        with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
            result = auth.authenticate(_make_request(INTERNAL_KEY))
        assert result == (None, "internal")

    def test_valid_public_key_returns_public_scope(self, auth):
        with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
            result = auth.authenticate(_make_request(PUBLIC_KEY))
        assert result == (None, "public")

    def test_internal_key_takes_priority_when_both_match(self, auth):
        with _patch_settings(internal=INTERNAL_KEY, public=INTERNAL_KEY):
            result = auth.authenticate(_make_request(INTERNAL_KEY))
        assert result == (None, "internal")

    def test_bytes_header_is_accepted_when_utf8(self, auth):
        with _patch_settings(internal=INTERNAL_KEY):
            result = auth.authenticate(_make_request(INTERNAL_KEY.encode("utf-8")))
        assert result == (None, "internal")


class TestInvalidAuthentication:
    def test_wrong_key_raises_authentication_failed(self, auth):
        with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
            with pytest.raises(AuthenticationFailed) as exc_info:
                auth.authenticate(_make_request("totallywrongkey"))
        assert "Invalid API key" in str(exc_info.value.detail)

    def test_invalid_utf8_bytes_raise_authentication_failed(self, auth):
        with _patch_settings(internal=INTERNAL_KEY):
            with pytest.raises(AuthenticationFailed) as exc_info:
                auth.authenticate(_make_request(b"\xff\xfe"))
        assert "Invalid characters in API key" in str(exc_info.value.detail)

    def test_unknown_key_is_rejected_when_only_internal_exists(self, auth):
        with _patch_settings(internal=INTERNAL_KEY, public=None):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(_make_request("unknownkey"))

    def test_unknown_key_is_rejected_when_only_public_exists(self, auth):
        with _patch_settings(internal=None, public=PUBLIC_KEY):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(_make_request("unknownkey"))

    def test_no_key_matches_when_settings_are_empty(self, auth):
        with _patch_settings(internal="", public=""):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(_make_request("somekey"))


class TestAuthenticateHeader:
    def test_returns_x_api_key_realm(self, auth):
        assert auth.authenticate_header(MagicMock()) == "X-API-Key"

    def test_return_type_is_string(self, auth):
        assert isinstance(auth.authenticate_header(MagicMock()), str)


class TestComparisonBehavior:
    def test_key_matching_is_case_sensitive(self, auth):
        with _patch_settings(internal=INTERNAL_KEY):
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(_make_request(INTERNAL_KEY.upper()))

    def test_compare_digest_is_used(self, auth):
        with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
            with patch(
                "apps.core.authentications.secrets.compare_digest",
                wraps=secrets.compare_digest,
            ) as mock_compare_digest:
                auth.authenticate(_make_request(PUBLIC_KEY))
        assert mock_compare_digest.called
        assert mock_compare_digest.call_count == 2

    def test_compare_digest_receives_bytes(self, auth):
        with _patch_settings(internal=INTERNAL_KEY):
            with patch(
                "apps.core.authentications.secrets.compare_digest",
                wraps=secrets.compare_digest,
            ) as mock_compare_digest:
                auth.authenticate(_make_request(INTERNAL_KEY))
        args, _ = mock_compare_digest.call_args
        assert all(isinstance(arg, bytes) for arg in args)


class TestGeneralRobustness:
    def test_supports_special_ascii_keys(self, auth):
        special_key = "k3y-w1th-$pec!@l_ch@r$"
        with _patch_settings(internal=special_key):
            result = auth.authenticate(_make_request(special_key))
        assert result == (None, "internal")

    def test_supports_unicode_keys(self, auth):
        unicode_key = "kéy-wïth-ünícödé"
        with _patch_settings(internal=unicode_key):
            result = auth.authenticate(_make_request(unicode_key))
        assert result == (None, "internal")

    def test_authentication_class_inherits_from_base_authentication(self):
        assert issubclass(ApiKeyAuthentication, BaseAuthentication)

    def test_authentication_is_stateless_across_calls(self, auth):
        with _patch_settings(internal=INTERNAL_KEY, public=PUBLIC_KEY):
            first = auth.authenticate(_make_request(INTERNAL_KEY))
            second = auth.authenticate(_make_request(PUBLIC_KEY))
            third = auth.authenticate(_make_request())
        assert first == (None, "internal")
        assert second == (None, "public")
        assert third is None
