from django.db.models import Prefetch
from rest_framework import mixins
from rest_framework.viewsets import ReadOnlyModelViewSet
from apps.core.views import ApiModelViewSet
from apps.pricing.models import (
    Price,
    PriceTranslation,
    PriceRank,
    PriceRankTranslation,
)
from apps.pricing.serializers import (
    PriceSerializer,
    PriceTranslationSerializer,
    PriceRankSerializer,
    PriceRankTranslationSerializer
)


class PriceViewSet(ApiModelViewSet):
    """Prices endpoint."""
    serializer_class = PriceSerializer
    queryset = (
        Price.objects
        .prefetch_related(
            Prefetch(
                "translations",
                queryset=PriceTranslation.objects.select_related("language"),
            )
        )
        .order_by("sort_order", "id")
    )


class PriceTranslationViewSet(ApiModelViewSet):
    """PriceTranslations endpoint."""
    serializer_class = PriceTranslationSerializer
    queryset = (
        PriceTranslation.objects.all()
        .select_related("price", "language")
        .order_by("price_id", "language_id", "id")
    )


class PriceRankViewSet(ApiModelViewSet):
    """PriceRanks endpoint."""
    serializer_class = PriceRankSerializer
    queryset = (
        PriceRank.objects
        .prefetch_related(
            Prefetch(
                "translations",
                queryset=PriceRankTranslation.objects.select_related("language"),
            )
        )
        .order_by("position", "id")
    )


class PriceRankTranslationViewSet(ApiModelViewSet):
    """PriceRankTranslations endpoint."""
    serializer_class = PriceRankTranslationSerializer
    queryset = (
        PriceRankTranslation.objects.all()
        .select_related("price_rank", "language")
        .order_by("price_rank_id", "language_id", "id")
    )