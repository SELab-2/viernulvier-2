"""
ViewSets for the Productions app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.

Productions are the core catalogue entity. Each production may have one
or more events and carries translatable metadata resolved per request via
the ``Accept-Language`` header.
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
    carries all translatable metadata (title, artist name, description, etc.).
    Translatable fields are resolved from the ``Accept-Language`` header via
    ``TranslatableSerializerMixin``.

    Queryset strategy
    -----------------
    - ``select_related`` is used for single-row FK relations
      (``uit_database_theme``, ``uit_database_type``).
    - ``prefetch_related`` with explicit ``Prefetch`` objects is used for
      one-to-many and many-to-many relations to avoid N+1 queries:

        * ``translations__language`` — localised production metadata.
        * ``tags`` + ``tags__translations__language`` — tag objects with their
          own localised fields, needed by ``TagSerializer``.
        * ``productiongenre_set`` — fetched into ``prefetched_production_genres``
          so the serializer can return genres in the correct ``position`` order
          without issuing an extra query per production.
    """

    serializer_class = ProductionSerializer

    queryset = (
        Production.objects
        .select_related(
            "uit_database_theme",
            "uit_database_type",
        )
        .prefetch_related(
            "translations__language",
            "tags",
            "tags__translations__language",
            Prefetch(
                "productiongenre_set",
                queryset=ProductionGenre.objects
                    .select_related("genre")
                    .order_by("position"),
                to_attr="prefetched_production_genres",
            ),
        )
    )