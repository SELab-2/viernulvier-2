"""
ViewSets for the Pricing app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from django.db.models import Prefetch

from apps.core.cache_mixin import cache_read_actions
from apps.core.views import ApiModelViewSet

from .filters import PriceFilter, PriceRankFilter
from .models import Price, PriceRank, PriceRankTranslation, PriceTranslation
from .schemas import extend_schema, price_rank_schema, price_schema
from .serializers import PriceRankSerializer, PriceSerializer

_TAG = "Pricing"


@cache_read_actions()
@extend_schema(tags=[_TAG])
@price_schema
class PriceViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Price objects.

    A price defines a ticket category (e.g. full price, student, Cineville).

    Filtering
    ---------
    ``?type=student``
        Substring match on the internal type identifier.
    ``?visibility=public``
        Exact match on the visibility value.
    ``?membership=cineville``
        Substring match on the membership requirement.
    ``?cineville_box=true``
        Only Cineville box prices.
    ``?description=student``
        Substring match across all translated descriptions.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=sort_order`` / ``?ordering=-sort_order``
        By display order (default ascending).
    ``?ordering=type`` / ``?ordering=-type``
        Alphabetical by type identifier.

    Search
    ------
    ``?search=student``
        Full-text search across ``type``, ``visibility``, and
        translated descriptions.
    """

    serializer_class = PriceSerializer
    queryset = Price.objects.prefetch_related(
        Prefetch(
            "translations",
            queryset=PriceTranslation.objects.select_related("language"),
        )
    ).order_by("sort_order", "id")

    filterset_class = PriceFilter
    ordering_fields = ["id", "sort_order", "type", "visibility"]
    ordering = ["sort_order", "id"]
    search_fields = ["type", "visibility", "translations__description"]


@cache_read_actions()
@extend_schema(tags=[_TAG])
@price_rank_schema
class PriceRankViewSet(ApiModelViewSet):
    """
    CRUD endpoints for PriceRank objects.

    A price rank defines an ordered availability tier that controls when a
    price level is considered sold out.

    Filtering
    ---------
    ``?position=1``
        Exact match on the rank position.
    ``?position_gte=2``
        Ranks at or above the given position.
    ``?position_lte=5``
        Ranks at or below the given position.
    ``?description=student``
        Substring match across all translated descriptions.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=position`` / ``?ordering=-position``
        By rank position (default ascending).

    Search
    ------
    ``?search=student``
        Full-text search across translated descriptions.
    """

    serializer_class = PriceRankSerializer
    queryset = PriceRank.objects.prefetch_related(
        Prefetch(
            "translations",
            queryset=PriceRankTranslation.objects.select_related("language"),
        )
    ).order_by("position", "id")

    filterset_class = PriceRankFilter
    ordering_fields = ["id", "position"]
    ordering = ["position", "id"]
    search_fields = ["translations__description"]
