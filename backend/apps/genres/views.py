"""
ViewSets for the Genre app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from apps.core.views import ApiModelViewSet

from .filters import GenreFilter, GenreUseAsFilter
from .models import Genre, GenreUseAs
from .schemas import extend_schema, genre_schema, genre_use_as_schema
from .serializers import GenreSerializer, GenreUseAsSerializer

_TAG = "Genres"


@extend_schema(tags=[_TAG])
@genre_use_as_schema
class GenreUseAsViewSet(ApiModelViewSet):
    """
    CRUD endpoints for GenreUseAs objects.

    A GenreUseAs defines the role a genre plays in the system,
    for example as a production classification or as a tag.

    Filtering
    ---------
    ``?name=tag``
        Substring match on the use-as label.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=name`` / ``?ordering=-name``
        Alphabetical by label.
    ``?ordering=id`` / ``?ordering=-id``
        By creation order (default ascending).

    Search
    ------
    ``?search=genre``
        Full-text search across ``name``.
    """

    queryset = GenreUseAs.objects.order_by("id")
    serializer_class = GenreUseAsSerializer

    filterset_class = GenreUseAsFilter
    ordering_fields = ["id", "name"]
    ordering = ["id"]
    search_fields = ["name"]


@extend_schema(tags=[_TAG])
@genre_schema
class GenreViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Genre objects.

    Genres categorise productions (e.g. Theater, Festival, Book Presentation).
    Each genre links to a usage context and supports multiple translations.

    Filtering
    ---------
    ``?use_as=1``
        Genres belonging to a specific usage context.
    ``?type=theater``
        Substring match on the internal type identifier.
    ``?vendor_id=abc-123``
        Substring match on the upstream vendor identifier.
    ``?name=festival``
        Substring match across translated genre names (all languages).
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=type`` / ``?ordering=-type``
        Alphabetical by internal type.
    ``?ordering=use_as`` / ``?ordering=-use_as``
        Group by usage context FK.
    ``?ordering=id`` / ``?ordering=-id``
        By creation order (default ascending).

    Search
    ------
    ``?search=theater``
        Full-text search across ``type`` and translated ``name`` fields.
    """

    queryset = (
        Genre.objects.select_related("use_as")
        .prefetch_related("translations__language")
        .order_by("id")
    )
    serializer_class = GenreSerializer

    filterset_class = GenreFilter
    ordering_fields = ["id", "type", "use_as"]
    ordering = ["id"]
    search_fields = ["type", "translations__name"]