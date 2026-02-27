import secrets
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed


class ApiKeyAuthentication(BaseAuthentication):
    """
    Production-ready API Key authentication using:

        Authorization: Bearer <API_KEY>

    Supports:
        - INTERNAL_API_KEY (full access)
        - PUBLIC_API_KEY (read-only)

    Returns:
        (None, "internal") or (None, "public")
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        # No header -> skip authentication
        if not auth:
            return None

        # Must be: Bearer <token>
        if len(auth) != 2 or auth[0].decode().lower() != self.keyword.lower():
            raise AuthenticationFailed("Invalid Authorization header format.")

        try:
            key = auth[1].decode('utf-8')
        except UnicodeDecodeError:
            raise AuthenticationFailed("Invalid characters in API key.")

        internal_key = getattr(settings, "INTERNAL_API_KEY", None)
        public_key = getattr(settings, "PUBLIC_API_KEY", None)

        if internal_key and secrets.compare_digest(key.encode('utf-8'), internal_key.encode('utf-8')):
            return (None, "internal")

        if public_key and secrets.compare_digest(key.encode('utf-8'), public_key.encode('utf-8')):
            return (None, "public")

        raise AuthenticationFailed("Invalid API key.")