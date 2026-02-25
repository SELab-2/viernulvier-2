from rest_framework.viewsets import ModelViewSet
from .permissions import HasPublicApiKey, HasInternalApiKey
from rest_framework.permissions import SAFE_METHODS


class ApiModelViewSet(ModelViewSet):
    """
    Base API ViewSet with dynamic permission switching.
    - Read-only methods (GET/HEAD/OPTIONS) require a Public Key.
    - Write methods (POST/PUT/PATCH/DELETE) require an Internal Key.
    """

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method in SAFE_METHODS:
            return [HasPublicApiKey() | HasInternalApiKey()]
        
        # For all other methods (POST, PUT, DELETE, etc.)
        return [HasInternalApiKey()]