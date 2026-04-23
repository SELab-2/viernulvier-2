"""ViewSets for the Genre app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from apps.core.views import ApiModelViewSet

from .filters import GenreFilter
from .models import Genre
from .schemas import extend_schema, genre_schema
from .serializers import GenreSerializer

_TAG = "Genres"


@extend_schema(tags=[_TAG])
@genre_schema
class GenreViewSet(ApiModelViewSet):
    """CRUD endpoints for Genre objects.

    Genres categorise productions (e.g. Theater, Festival, Book Presentation)
    and support multiple translations.

    Filtering
    ---------
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
    ``?ordering=id`` / ``?ordering=-id``
        By creation order (default ascending).

    Search
    ------
    ``?search=theater``
        Full-text search across ``type`` and translated ``name`` fields.
    """

    queryset = Genre.objects.prefetch_related("translations__language").order_by("id")
    serializer_class = GenreSerializer

    filterset_class = GenreFilter
    ordering_fields = ["id", "type"]
    ordering = ["id"]
    search_fields = ["type", "translations__name"]
