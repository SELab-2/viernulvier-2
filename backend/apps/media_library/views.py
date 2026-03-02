"""
ViewSets for the Media app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from apps.core.views import ApiModelViewSet

from .models import MediaGallery, MediaItem
from .schemas import extend_schema, media_gallery_schema, media_item_schema
from .serializers import MediaGallerySerializer, MediaItemSerializer

_TAG = "Media"  # Reusable tag for all media-related endpoints in the OpenAPI docs


@extend_schema(tags=[_TAG])
@media_gallery_schema
class MediaGalleryViewSet(ApiModelViewSet):
    """
    CRUD endpoints for MediaGallery objects.

    A gallery is a named collection of media items. The response includes
    all nested media items (with their localised metadata and crop variants)
    in a single call, so no separate item lookups are needed for rendering.

    Prefetches all nested relations to avoid N+1 queries.
    """

    serializer_class = MediaGallerySerializer
    queryset = (
        MediaGallery.objects
        .prefetch_related(
            "media_items",
            "media_items__translations__language",
            "media_items__crops",
        )
        .order_by("name")
    )


@extend_schema(tags=[_TAG])
@media_item_schema
class MediaItemViewSet(ApiModelViewSet):
    """
    CRUD endpoints for MediaItem objects.

    A media item is a single image, video, or audio asset within a gallery.
    The response includes localised metadata and all pre-rendered crop variants.

    Prefetches translations and crops, and selects the related gallery to
    avoid N+1 queries.
    """

    serializer_class = MediaItemSerializer
    queryset = (
        MediaItem.objects
        .select_related("gallery")
        .prefetch_related(
            "translations__language",
            "crops",
        )
        .order_by("position")
    )