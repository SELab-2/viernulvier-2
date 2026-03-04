from rest_framework.permissions import SAFE_METHODS, BasePermission


class ApiKeyPermission(BasePermission):
    """
    Uses request.auth to determine access level.
    """

    def has_permission(self, request, _):
        if request.auth == "internal":  # Access to everything
            return True
        # Only GET, ... no changes allowed
        return request.auth == "public" and request.method in SAFE_METHODS
