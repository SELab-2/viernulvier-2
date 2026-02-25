from apps.core.views import ApiModelViewSet
from apps.core.permissions import HasPublicApiKey, HasInternalApiKey
from .models import Tag
from .serializers import TagSerializer


class TagViewSet(ApiModelViewSet):
    """
    Tag API endpoint.

    - Public key -> read-only
    - Internal key -> full CRUD
    """

    queryset = Tag.objects.prefetch_related("translations")
    serializer_class = TagSerializer