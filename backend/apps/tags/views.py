from apps.core.views import ApiModelViewSet
from .models import Tag
from .serializers import TagSerializer


class TagViewSet(ApiModelViewSet):
    """
    API endpoint for managing Tags.

    Behavior:
        - Public API key  -> read-only
        - Internal API key -> full CRUD

    Optimized with prefetch_related to avoid N+1 queries
    when accessing translations.
    """

    queryset = Tag.objects.prefetch_related("translations")
    serializer_class = TagSerializer