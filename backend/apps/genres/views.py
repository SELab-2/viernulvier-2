"""
ViewSets for the Genre app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from apps.core.views import ApiModelViewSet

from .models import Genre, GenreUseAs
from .schemas import extend_schema, genre_schema, genre_use_as_schema
from .serializers import GenreSerializer, GenreUseAsSerializer

_TAG = "Genres"  # Reusable tag for all genre-related endpoints in the OpenAPI docs


@extend_schema(tags=[_TAG])
@genre_use_as_schema
class GenreUseAsViewSet(ApiModelViewSet):
    """
    CRUD endpoints for GenreUseAs objects.

    A GenreUseAs defines the role a genre plays in the system,
    for example as a production classification or as a tag.
    """

    queryset = GenreUseAs.objects.all()
    serializer_class = GenreUseAsSerializer


@extend_schema(tags=[_TAG])
@genre_schema
class GenreViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Genre objects.

    Genres categorise productions (e.g. Theater, Festival, Book Presentation).
    Each genre links to a usage context and supports multiple translations.
    """

    queryset = (
        Genre.objects.select_related("use_as")
        .prefetch_related("translations__language")
        .all()
    )
    serializer_class = GenreSerializer
