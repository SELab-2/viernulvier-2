import secrets
from django.conf import settings
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom DRF authentication class for API Key validation.

    This authentication backend expects the following header format:

        Authorization: Api-Key <KEY>

    It supports two different API keys defined in Django settings:

        - INTERNAL_API_KEY -> full access (write + read)
        - PUBLIC_API_KEY   -> read-only access

    On successful authentication, it returns:
        (user, auth)

    Where:
        - user = None (no Django user model is used)
        - auth = "internal" or "public"

    The value stored in `request.auth` can later be used in
    permission classes to decide access level.

    Behavior:
        - No header -> returns None (authentication not attempted)
        - Invalid format -> raises AuthenticationFailed
        - Invalid key -> raises AuthenticationFailed
    """

    keyword = "api-key"

    def authenticate(self, request):
        """
        Attempts to authenticate the request using an API key.

        Returns:
            tuple: (user, auth_type) if successful
            None: if no authentication header is present

        Raises:
            AuthenticationFailed: if header format is invalid
                                  or key does not match.
        """
        auth_header = request.headers.get("Authorization")

        # Case 1: Header completely missing -> do nothing
        if auth_header is None:
            return None

        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != self.keyword:
            raise AuthenticationFailed(
                "Invalid header format. Use: Api-Key <KEY>"
            )

        key = parts[1]

        internal_key = getattr(settings, "INTERNAL_API_KEY", None)
        public_key = getattr(settings, "PUBLIC_API_KEY", None)

        if internal_key and secrets.compare_digest(key, internal_key):
            return (None, "internal")

        if public_key and secrets.compare_digest(key, public_key):
            return (None, "public")

        raise AuthenticationFailed("Invalid API key.")