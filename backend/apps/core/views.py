from rest_framework.viewsets import ModelViewSet
from .authentications import ApiKeyAuthentication
from .permissions import ApiKeyPermission
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

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

class ApiReadOnlyViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    Base ViewSet for read-only operations.
    
    This class specifically excludes write actions (create, update, destroy)
    at the architectural level by only including List and Retrieve mixins.
    
    Ideal for monitoring logs, statistics, or reference data that should
    never be modified via the API, regardless of the API key's scope.
    """
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [ApiKeyPermission]