"""
API key authentication for the core app.

``ApiKeyAuthentication`` is the sole authentication class used across the
entire project. It is registered as the global default in
``settings/base.py`` via ``REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]``
and does not need to be set per-viewset.

Header format
-------------
Every request must include an ``Authorization`` header in the following
format (the scheme is case-insensitive):

    Authorization: Api-Key <KEY>

Two keys are supported, each granting a different level of access:

- ``INTERNAL_API_KEY`` — full CRUD access (``request.auth == "internal"``).
- ``PUBLIC_API_KEY``   — read-only access (``request.auth == "public"``).

The resulting ``request.auth`` value is consumed by
:class:`~apps.core.permissions.ApiKeyPermission` to enforce per-action
access control.

Security
--------
Key comparisons use :func:`secrets.compare_digest` to prevent timing
attacks that could otherwise be used to infer a valid key character by
character.
"""

import secrets
from typing import Optional, Tuple

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed


class ApiKeyAuthentication(BaseAuthentication):
    """
    DRF authentication class that validates ``Api-Key`` request headers.

    On success, returns ``(None, "internal")`` or ``(None, "public")``.
    The second element of the tuple becomes ``request.auth`` and is used
    by :class:`~apps.core.permissions.ApiKeyPermission` to determine what
    actions the caller is allowed to perform.

    On failure, raises :exc:`~rest_framework.exceptions.AuthenticationFailed`
    which DRF converts to an ``HTTP 401 Unauthorized`` response.

    When no ``Authorization`` header is present at all, returns ``None``
    so that DRF can fall through to any other configured authenticators.

    Attributes:
        keyword: The expected authentication scheme (``"api-key"``).
                 Compared case-insensitively against the header scheme.
    """

    keyword = "api-key"

    def authenticate(self, request) -> Optional[Tuple[None, str]]:
        """
        Parse the ``Authorization`` header and validate the API key.

        Steps
        -----
        1. Read the raw ``Authorization`` header bytes via DRF's helper.
        2. Return ``None`` (unauthenticated, not an error) if the header is
           absent or does not use the ``Api-Key`` scheme — this allows other
           authenticators in the chain to run.
        3. Reject malformed headers (wrong number of parts, non-UTF-8 bytes)
           with ``AuthenticationFailed`` (→ HTTP 401).
        4. Compare the extracted key against ``INTERNAL_API_KEY`` and then
           ``PUBLIC_API_KEY`` using :func:`secrets.compare_digest`.
        5. Raise ``AuthenticationFailed`` if neither key matches.

        Returns:
            ``(None, "internal")`` for a valid internal key.
            ``(None, "public")`` for a valid public key.
            ``None`` if no ``Api-Key`` scheme is present.

        Raises:
            :exc:`~rest_framework.exceptions.AuthenticationFailed`:
                On malformed headers or invalid keys (→ HTTP 401).
        """

        # Retrieve the raw Authorization header as bytes.
        # DRF returns it as bytes for consistent low-level handling.
        raw_auth = get_authorization_header(request)

        # No Authorization header at all — let other authenticators run.
        if not raw_auth:
            return None

        # Split into [scheme, key] parts (e.g. b"Api-Key abc123").
        parts = raw_auth.split()

        if not parts:
            return None

        # Decode the authentication scheme; reject non-UTF-8 bytes.
        try:
            scheme = parts[0].decode("utf-8")
        except UnicodeDecodeError:
            raise AuthenticationFailed("Invalid characters in authentication scheme.")

        # Ignore schemes other than "Api-Key" so other authenticators can run.
        if scheme.lower() != self.keyword:
            return None

        # The header must be exactly two parts: scheme + key.
        if len(parts) != 2:
            raise AuthenticationFailed(
                "Invalid Authorization header format. Use: Api-Key <KEY>"
            )

        # Decode the key; reject non-UTF-8 byte sequences.
        try:
            key = parts[1].decode("utf-8")
        except UnicodeDecodeError:
            raise AuthenticationFailed("Invalid characters in API key.")

        # Read configured keys from Django settings.
        internal_key = getattr(settings, "INTERNAL_API_KEY", None)
        public_key = getattr(settings, "PUBLIC_API_KEY", None)

        # Encode the incoming key for timing-safe comparison.
        # secrets.compare_digest requires both operands to have the same type.
        key_bytes = key.encode("utf-8")

        # Check against INTERNAL_API_KEY first (grants full access).
        if internal_key and secrets.compare_digest(
            key_bytes, internal_key.encode("utf-8")
        ):
            return (None, "internal")

        # Check against PUBLIC_API_KEY (grants read-only access).
        if public_key and secrets.compare_digest(
            key_bytes, public_key.encode("utf-8")
        ):
            return (None, "public")

        # No match — reject the request.
        raise AuthenticationFailed("Invalid API key.")

    def authenticate_header(self, request) -> str:
        """
        Return the value for the ``WWW-Authenticate`` response header.

        DRF uses this to construct a proper ``HTTP 401 Unauthorized``
        response when authentication fails. Without it, DRF would return
        ``HTTP 403 Forbidden`` instead.
        """
        return "Api-Key"