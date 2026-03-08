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

from .models import Production, ProductionGenre
from .schemas import production_schema
from .serializers import ProductionSerializer

_TAG = "Productions"  # Reusable tag for all production-related endpoints in the OpenAPI docs


@extend_schema(tags=[_TAG])
@production_schema
class ProductionViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Production objects.

    A production is the central catalogue record — it groups events and
    carries all translated metadata (title, artist name, description, etc.).

    Translated fields are returned as language-code dictionaries via
    ``TranslatableSerializerMixin``.

    Queryset strategy
    -----------------
    - ``select_related`` for FK relations
    - ``prefetch_related`` for translations, tags, and ordered genres
    """

    serializer_class = ProductionSerializer

    queryset = Production.objects.select_related(
        "uit_database_theme",
        "uit_database_type",
    ).prefetch_related(
        "translations__language",
        "tags",
        "tags__translations__language",
        Prefetch(
            "productiongenre_set",
            queryset=ProductionGenre.objects.select_related("genre").order_by(
                "position"
            ),
            to_attr="prefetched_production_genres",
        ),
    )
