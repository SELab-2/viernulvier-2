"""API key authentication for the core app.

``ApiKeyAuthentication`` is the sole authentication class used across the
entire project. It is registered as the global default in
``settings/base.py`` via ``REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]``
and does not need to be set per-viewset.

Header format
-------------
Every request must include the following header:

    X-API-Key: <KEY>

Two keys are supported, each granting a different level of access:

- ``INTERNAL_API_KEY`` - full CRUD access (``request.auth == "internal"``).
- ``PUBLIC_API_KEY``   - read-only access (``request.auth == "public"``).

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
from typing import Any

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ApiKeyUser:
    """Minimal user-like object so DRF treats API key requests as authenticated."""

    is_authenticated = True


class ApiKeyAuthentication(BaseAuthentication):
    """DRF authentication class that validates ``X-API-Key`` request headers.

    On success, returns ``(ApiKeyUser(), "internal")`` or ``(ApiKeyUser(), "public")``.
    The second element of the tuple becomes ``request.auth`` and is used
    by :class:`~apps.core.permissions.ApiKeyPermission` to determine what
    actions the caller is allowed to perform.

    On failure, raises :exc:`~rest_framework.exceptions.AuthenticationFailed`
    which DRF converts to an ``HTTP 401 Unauthorized`` response.

    When no ``X-API-Key`` header is present at all, returns ``None``
    so that DRF can fall through to any other configured authenticators.
    """

    header_name = "HTTP_X_API_KEY"
    www_authenticate_realm = "X-API-Key"

    def authenticate(self, request: Any) -> tuple[ApiKeyUser, str] | None:
        """Read the ``X-API-Key`` header and validate the API key.

        Steps
        -----
        1. Read the raw ``X-API-Key`` value from ``request.META``.
        2. Return ``None`` (unauthenticated, not an error) if the header is
           absent.
        3. Reject non-UTF-8 byte values with ``AuthenticationFailed``
           (-> HTTP 401).
        4. Compare the extracted key against ``INTERNAL_API_KEY`` and then
           ``PUBLIC_API_KEY`` using :func:`secrets.compare_digest`.
        5. Raise ``AuthenticationFailed`` if neither key matches.

        Returns:
            ``(None, "internal")`` for a valid internal key.
            ``(None, "public")`` for a valid public key.
            ``None`` if no ``X-API-Key`` header is present.

        Raises:
            :exc:`~rest_framework.exceptions.AuthenticationFailed`:
                On invalid header bytes or invalid keys (-> HTTP 401).
        """
        # Django exposes request headers through request.META using the
        # HTTP_<HEADER_NAME> convention.
        raw_key = request.META.get(self.header_name)

        # No API key header at all - let other authenticators run.
        if not raw_key:
            return None

        if isinstance(raw_key, bytes):
            try:
                raw_key.decode("utf-8")
            except UnicodeDecodeError as err:
                raise AuthenticationFailed("Invalid characters in API key.") from err
            key_bytes = raw_key
        else:
            key_bytes = str(raw_key).encode("utf-8")

        # Read configured keys from Django settings.
        internal_key = getattr(settings, "INTERNAL_API_KEY", None)
        public_key = getattr(settings, "PUBLIC_API_KEY", None)

        # Check against INTERNAL_API_KEY first (grants full access).
        if internal_key and secrets.compare_digest(key_bytes, internal_key.encode("utf-8")):
            return (ApiKeyUser(), "internal")

        # Check against PUBLIC_API_KEY (grants read-only access).
        if public_key and secrets.compare_digest(key_bytes, public_key.encode("utf-8")):
            return (ApiKeyUser(), "public")

        # No match - reject the request.
        raise AuthenticationFailed("Invalid API key.")

    def authenticate_header(self, _request: Any) -> str:
        """Return the value for the ``WWW-Authenticate`` response header.

        DRF uses this to construct a proper ``HTTP 401 Unauthorized``
        response when authentication fails. Without it, DRF would return
        ``HTTP 403 Forbidden`` instead.
        """
        return self.www_authenticate_realm
