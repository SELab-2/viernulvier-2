import secrets
from typing import Optional, Tuple

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed


class ApiKeyAuthentication(BaseAuthentication):
    """
    API Key authentication for Django REST Framework.

    Expected header format:

        Authorization: Api-Key <KEY>

    Supported settings:
        - INTERNAL_API_KEY -> full access
        - PUBLIC_API_KEY   -> read-only access

    On success:
        Returns (None, "internal") or (None, "public")

    On failure:
        Raises AuthenticationFailed (HTTP 401)

    If no Authorization header is present:
        Returns None (allows other authenticators to run)
    """

    # The expected authentication scheme (case-insensitive)
    keyword = "api-key"

    def authenticate(self, request) -> Optional[Tuple[None, str]]:
        """
        Attempt to authenticate the request using an API key.

        Returns:
            (None, "internal") or (None, "public") if successful.
            None if no relevant authentication header is provided.

        Raises:
            AuthenticationFailed if the header is malformed
            or if the API key is invalid.
        """

        # Retrieve the raw Authorization header as bytes.
        # DRF returns it as bytes for consistent low-level handling.
        raw_auth = get_authorization_header(request)

        # If no Authorization header is present, skip authentication.
        # This allows other authentication classes to run.
        if not raw_auth:
            return None

        # Split the header into parts (e.g., b"Api-Key abc123" -> [b"Api-Key", b"abc123"])
        parts = raw_auth.split()

        # If header exists but is empty or malformed, treat it as no authentication.
        if not parts:
            return None

        # Decode the authentication scheme safely from bytes to string.
        try:
            scheme = parts[0].decode("utf-8")
        except UnicodeDecodeError:
            # If scheme cannot be decoded, the header is invalid.
            raise AuthenticationFailed("Invalid characters in authentication scheme.")

        # If the scheme does not match "Api-Key", ignore it.
        # Returning None allows other authentication mechanisms (e.g., JWT, SessionAuth).
        if scheme.lower() != self.keyword:
            return None

        # Ensure the header has exactly two parts: scheme + key
        if len(parts) != 2:
            raise AuthenticationFailed(
                "Invalid Authorization header format. Use: Api-Key <KEY>"
            )

        # Decode the API key safely from bytes to string.
        try:
            key = parts[1].decode("utf-8")
        except UnicodeDecodeError:
            # Reject keys containing invalid byte sequences.
            raise AuthenticationFailed("Invalid characters in API key.")

        # Retrieve configured API keys from Django settings.
        internal_key = getattr(settings, "INTERNAL_API_KEY", None)
        public_key = getattr(settings, "PUBLIC_API_KEY", None)

        # Convert incoming key to bytes for timing-safe comparison.
        # compare_digest requires both arguments to be of the same type.
        key_bytes = key.encode("utf-8")

        # Check against INTERNAL_API_KEY first (full access).
        if internal_key and secrets.compare_digest(
            key_bytes, internal_key.encode("utf-8")
        ):
            return (None, "internal")

        # Check against PUBLIC_API_KEY (read-only access).
        if public_key and secrets.compare_digest(
            key_bytes, public_key.encode("utf-8")
        ):
            return (None, "public")

        # If no key matches, authentication fails.
        raise AuthenticationFailed("Invalid API key.")

    def authenticate_header(self, request) -> str:
        """
        Return the value for the WWW-Authenticate response header.

        This ensures DRF returns a proper 401 Unauthorized response
        when authentication fails.
        """
        return "Api-Key"