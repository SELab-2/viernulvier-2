from rest_framework.permissions import BasePermission, SAFE_METHODS


class ApiKeyPermission(BasePermission):
    """
    Uses request.auth to determine access level.
    """

    def has_permission(self, request, _):
        if request.auth == "internal": # Acces to everything
            return True
        return request.auth == "public" and request.method in SAFE_METHODS # Only GET, ... no changes allowed