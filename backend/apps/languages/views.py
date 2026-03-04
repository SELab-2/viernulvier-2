from apps.core.views import ApiModelViewSet

from .models import Language
from .serializers import LanguageSerializer


class LanguageViewSet(ApiModelViewSet):
    """
    API endpoint for managing languages.

    Access rules:
        - Public API key -> read-only
        - Internal API key -> full CRUD

    Lookup is based on ISO code instead of numeric ID.
    """

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    lookup_field = "code"