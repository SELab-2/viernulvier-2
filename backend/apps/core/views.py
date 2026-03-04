from rest_framework.viewsets import ModelViewSet

from .authentications import ApiKeyAuthentication
from .permissions import ApiKeyPermission


class ApiModelViewSet(ModelViewSet):
    """
    Base API ViewSet.

    Authentication:
        - Validates the 'Api-Key' via the Authorization header.
        - Sets request.auth to "public" or "internal".

    Permissions:
        - "internal" has full CRUD access.
        - "public" has read-only access (GET, HEAD, OPTIONS).
        - No valid key results in a 401 (via Auth) or 403 (via Permission).
    """

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [ApiKeyPermission]
