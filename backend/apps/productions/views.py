"""
ViewSets for the Productions app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.

Productions are the core catalogue entity. Each production may have one
or more events and carries translatable metadata.

Translation Format
------------------
Metadata fields (title, description, etc.) are returned as dictionaries
containing all available translations (e.g., {"nl": "...", "en": "..."}).
The 'Accept-Language' header is not used for filtering these fields,
allowing consumers to access all languages in a single request.
"""

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema

from apps.core.views import ApiModelViewSet

from .filters import ProductionFilter
from .models import Production, ProductionGenre
from .schemas import production_schema
from .serializers import ProductionSerializer

_TAG = "Productions"


@extend_schema(tags=[_TAG])
@production_schema
class ProductionViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Production objects.

    A production is the central catalogue record - it groups events and
    carries all translated metadata (title, artist name, description, etc.).

    Translated fields are returned as language-code dictionaries via
    ``TranslatableSerializerMixin``.

    Filtering
    ---------
    ``?attendance_mode=offline``
        Filter by attendance mode. Accepted values: ``offline``, ``online``.
    ``?performer_type=solo``
        Filter by performer type. Accepted values: ``group``, ``solo``.
    ``?uit_database_theme=3``
        Productions belonging to a specific UIT Database theme.
    ``?uit_database_type=7``
        Productions belonging to a specific UIT Database type.
    ``?genre=2``
        Productions that have a specific genre attached.
    ``?tag=5``
        Productions that have a specific tag attached.
    ``?has_media=true``
        Only productions with (``true``) or without (``false``) a media
        gallery.
    ``?title=hamlet``
        Substring match across all translated titles.
    ``?artist_name=toneelschuur``
        Substring match across all translated artist names.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=-id``
        Most recently created first (default).
    ``?ordering=attendance_mode``
        Group by attendance mode.
    ``?ordering=performer_type``
        Group by performer type.

    Search
    ------
    ``?search=hamlet``
        Full-text search across translated ``title``, ``artist_name``,
        and ``tagline`` fields.

    Queryset strategy
    -----------------
    - ``select_related`` for single-row FK relations.
    - ``prefetch_related`` for translations, tags, and ordered genres to
      avoid N+1 queries on list responses.
    """

    serializer_class = ProductionSerializer
    queryset = Production.objects.select_related(
        "uit_database_theme",
        "uit_database_type",
        "media_gallery",
    ).prefetch_related(
        "translations__language",
        "tags",
        "tags__translations__language",
        Prefetch(
            "productiongenre_set",
            queryset=ProductionGenre.objects.select_related("genre").order_by("position"),
            to_attr="prefetched_production_genres",
        ),
    )

    filterset_class = ProductionFilter
    ordering_fields = ["id", "attendance_mode", "performer_type"]
    ordering = ["-id"]
    search_fields = [
        "translations__title",
        "translations__artist_name",
        "translations__tagline",
    ]
