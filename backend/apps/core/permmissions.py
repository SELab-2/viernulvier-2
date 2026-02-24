import secrets
from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

class HasStaticApiKey(BasePermission):
    """
    Statically validates an API key provided in the Authorization header.
    Expected format: Authorization: Api-Key <KEY>
    """

    def has_permission(self, request, view):
        # 1. Extract the Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            # Raising NotAuthenticated triggers a 401 instead of a generic 403
            raise NotAuthenticated("Authentication credentials were not provided.")

        # 2. Split and validate the header format
        parts = auth_header.split()

        if len(parts) != 2:
            raise AuthenticationFailed(
                "Invalid token header. No credentials provided."
            )
            
        prefix, key = parts

        # 3. Check if the prefix is correct
        if prefix.lower() != "api-key":
            raise AuthenticationFailed(
                "Invalid token header. Prefix must be 'Api-Key'."
            )

        # 4. Safely retrieve the key from settings
        # Using getattr prevents the app from crashing if the setting is missing
        expected_key = getattr(settings, "PUBLIC_API_KEY", None)

        if not expected_key:
            # If the server is not configured with a key, deny all access for safety
            raise AuthenticationFailed("API key is not configured on the server.")

        # 5. Prevent timing attacks
        if not secrets.compare_digest(key, expected_key):
            raise AuthenticationFailed("Invalid API key.")
        
        return True