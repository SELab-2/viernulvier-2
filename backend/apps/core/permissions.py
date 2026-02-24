import secrets
from django.conf import settings
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

class BaseApiKeyPermission(BasePermission):
    """
    Base class for API Key validation to keep code DRY.
    """
    def get_api_key(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise NotAuthenticated("Authentication credentials were not provided.")

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "api-key":
            raise AuthenticationFailed("Invalid header format. Use: Api-Key <KEY>")
        
        return parts[1]

class HasPublicApiKey(BaseApiKeyPermission):
    """
    Allows READ-ONLY access (GET, HEAD, OPTIONS) using the PUBLIC_API_KEY.
    """
    def has_permission(self, request, _):
        if request.method not in SAFE_METHODS:
            return False # Only allow safe methods

        key = self.get_api_key(request)
        expected_key = getattr(settings, "PUBLIC_API_KEY", None)

        if not expected_key:
            raise AuthenticationFailed("Public API key not configured on server.")

        if not secrets.compare_digest(key, expected_key):
            raise AuthenticationFailed("Invalid Public API key.")
        
        return True

class HasInternalApiKey(BaseApiKeyPermission):
    """
    Allows full CRUD access (POST, PUT, PATCH, DELETE, etc.) using the INTERNAL_API_KEY.
    Intended for sync services or internal CLI tools.
    """
    def has_permission(self, request, _):
        key = self.get_api_key(request)
        expected_key = getattr(settings, "INTERNAL_API_KEY", None)

        if not expected_key:
            raise AuthenticationFailed("Internal API key not configured on server.")

        if not secrets.compare_digest(key, expected_key):
            raise AuthenticationFailed("Invalid Internal API key.")
        
        return True