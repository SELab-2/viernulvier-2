"""
API key permission enforcement for the core app.

``ApiKeyPermission`` works in tandem with
:class:`~apps.core.authentications.ApiKeyAuthentication`. The authenticator
populates ``request.auth`` with ``"internal"`` or ``"public"``; this
permission class decides what each auth level is allowed to do.

Access matrix
-------------
+------------------+------------------------------------------+
| ``request.auth`` | Allowed methods                          |
+==================+==========================================+
| ``"internal"``   | All methods (GET, POST, PUT, PATCH,      |
|                  | DELETE, HEAD, OPTIONS)                   |
+------------------+------------------------------------------+
| ``"public"``     | Safe methods only (GET, HEAD, OPTIONS)   |
+------------------+------------------------------------------+
| anything else    | Denied (→ HTTP 403)                      |
+------------------+------------------------------------------+

If the request was not authenticated at all (``request.auth`` is ``None``),
:class:`~apps.core.authentications.ApiKeyAuthentication` will already have
returned ``None``, causing DRF to issue ``HTTP 401 Unauthorized`` before
this permission class is even called.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class ApiKeyPermission(BasePermission):
    """
    DRF permission class that gates access based on the API key scope.

    Reads ``request.auth`` — set by
    :class:`~apps.core.authentications.ApiKeyAuthentication` — and allows
    or denies the request according to the access matrix above.

    This class is registered as the global default in
    ``settings/base.py`` via
    ``REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"]`` and does not need
    to be set per-viewset unless a specific override is required.

    Safe methods
    ------------
    DRF's :data:`~rest_framework.permissions.SAFE_METHODS` constant covers
    ``GET``, ``HEAD``, and ``OPTIONS`` — all of which are read-only by the
    HTTP specification and therefore permitted for public keys.
    """

    def has_permission(self, request, view) -> bool:
        """
        Return ``True`` if the request should be permitted.

        - Internal keys are granted unconditional access.
        - Public keys may only perform safe (read-only) operations.
        - Any other value for ``request.auth`` is denied.
        """
        if request.auth == "internal":
            # Full access — all HTTP methods are allowed.
            return True

        if request.auth == "public":
            # Read-only access — only safe methods (GET, HEAD, OPTIONS).
            return request.method in SAFE_METHODS

        # request.auth is None or an unrecognised value — deny access.
        return False