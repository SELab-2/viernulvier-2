"""
ViewSets for the Media app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from apps.core.cache_mixin import cache_read_actions
from apps.core.views import ApiModelViewSet

from .filters import MediaGalleryFilter, MediaItemFilter
from .models import MediaGallery, MediaItem
from .schemas import extend_schema, media_gallery_schema, media_item_schema
from .serializers import MediaGallerySerializer, MediaItemSerializer

_TAG = "Media"


@cache_read_actions()
@extend_schema(tags=[_TAG])
@media_gallery_schema
class MediaGalleryViewSet(ApiModelViewSet):
    """
    CRUD endpoints for MediaGallery objects.

    A gallery is a named collection of media items. The response includes
    all nested media items (with their localised metadata and crop variants)
    in a single call, so no separate item lookups are needed for rendering.

    Filtering
    ---------
    ``?name=season``
        Substring match on the gallery name.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=name`` / ``?ordering=-name``
        Alphabetical by gallery name (default ascending).
    ``?ordering=id`` / ``?ordering=-id``
        By creation order.

    Search
    ------
    ``?search=season``
        Full-text search across ``name``.
    """

    serializer_class = MediaGallerySerializer
    queryset = MediaGallery.objects.prefetch_related(
        "media_items",
        "media_items__translations__language",
        "media_items__crops",
    ).order_by("name")

    filterset_class = MediaGalleryFilter
    ordering_fields = ["id", "name"]
    ordering = ["name"]
    search_fields = ["name"]


@cache_read_actions()
@extend_schema(tags=[_TAG])
@media_item_schema
class MediaItemViewSet(ApiModelViewSet):
    """
    CRUD endpoints for MediaItem objects.

    A media item is a single image, video, or audio asset within a gallery.
    The response includes localised metadata and all pre-rendered crop variants.

    Filtering
    ---------
    ``?gallery=5``
        Items belonging to a specific gallery.
    ``?type=foto``
        Exact media type. Accepted values: ``foto``, ``video``,
        ``audio``, ``other``.
    ``?format=jpg``
        Substring match on the file format or extension.
    ``?original_filename=poster``
        Substring match on the original filename.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=position`` / ``?ordering=-position``
        By display position within the gallery (default ascending).
    ``?ordering=type`` / ``?ordering=-type``
        Group by media type.
    ``?ordering=gallery`` / ``?ordering=-gallery``
        Group by parent gallery FK.

    Search
    ------
    ``?search=poster``
        Full-text search across ``original_filename`` and translated
        ``title`` and ``description`` fields.
    """

    serializer_class = MediaItemSerializer
    queryset = (
        MediaItem.objects.select_related("gallery")
        .prefetch_related(
            "translations__language",
            "crops",
        )
        .order_by("position")
    )

    filterset_class = MediaItemFilter
    ordering_fields = ["id", "position", "type", "gallery"]
    ordering = ["position"]
    search_fields = ["original_filename", "translations__title", "translations__description"]
