from apps.core.views import ApiModelViewSet
from .models import MediaGallery, MediaItem
from .serializers import MediaGallerySerializer, MediaItemSerializer


class MediaGalleryViewSet(ApiModelViewSet):
    """
    API endpoint for managing MediaGalleries.

    Behavior:
        - Public API key  -> read-only
        - Internal API key -> full CRUD

    Fully optimized to prevent N+1 queries.
    Prefetches nested media items with their
    translations, crops, and related language objects.
    """

    serializer_class = MediaGallerySerializer

    queryset = (
        MediaGallery.objects
        .prefetch_related(
            "media_items",
            "media_items__translations__language",
            "media_items__crops",
        )
    )


class MediaItemViewSet(ApiModelViewSet):
    """
    API endpoint for managing MediaItems.

    Behavior:
        - Public API key  -> read-only
        - Internal API key -> full CRUD

    Fully optimized to prevent N+1 queries.
    """

    serializer_class = MediaItemSerializer

    queryset = (
        MediaItem.objects
        .select_related(
            "gallery",
        )
        .prefetch_related(
            "translations__language",
            "crops",
        )
        .order_by("position")
    )