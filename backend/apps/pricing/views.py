"""
ViewSets for the Pricing app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from django.db.models import Prefetch

from apps.core.views import ApiModelViewSet

from .models import Price, PriceRank, PriceRankTranslation, PriceTranslation
from .schemas import extend_schema, price_rank_schema, price_schema
from .serializers import PriceRankSerializer, PriceSerializer

_TAG = "Pricing"  # Reusable tag for all pricing-related endpoints in the OpenAPI docs


@extend_schema(tags=[_TAG])
@price_schema
class PriceViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Price objects.

    A price defines a ticket category (e.g. full price, student, Cineville).
    Variable pricing is supported via the `minimum`, `maximum`, and `step`
    fields.

    The `description` field returns all available translations as a
    language-code dictionary.

    Uses an explicit `Prefetch` to eagerly load translations with their related
    language in a single query.
    """

    serializer_class = PriceSerializer
    queryset = Price.objects.prefetch_related(
        Prefetch(
            "translations",
            queryset=PriceTranslation.objects.select_related("language"),
        )
    ).order_by("sort_order", "id")


@extend_schema(tags=[_TAG])
@price_rank_schema
class PriceRankViewSet(ApiModelViewSet):
    """
    CRUD endpoints for PriceRank objects.

    A price rank defines an ordered availability tier that controls when a
    price level is considered sold out.

    The `description` field returns all available translations as a
    language-code dictionary.

    Uses an explicit `Prefetch` to eagerly load translations with their related
    language in a single query.
    """

    serializer_class = PriceRankSerializer
    queryset = PriceRank.objects.prefetch_related(
        Prefetch(
            "translations",
            queryset=PriceRankTranslation.objects.select_related("language"),
        )
    ).order_by("position", "id")
