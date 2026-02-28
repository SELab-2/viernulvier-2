from django.db.models import Prefetch
from apps.core.views import ApiModelViewSet
from apps.events.models import Event, EventPrice
from apps.events.serializers import EventSerializer
from apps.productions.models import ProductionTranslation
from apps.locations.models import HallTranslation
from apps.pricing.models import PriceRankTranslation


class EventViewSet(ApiModelViewSet):
    """Events endpoint."""
    serializer_class = EventSerializer
    queryset = (
        Event.objects
        .select_related(
            "production",
            "hall",
            "hall__space",
            "hall__space__location",
        )
        .prefetch_related(
            Prefetch(
                "prices",
                queryset=EventPrice.objects.select_related("price_rank"),
            ),
            Prefetch(
                "production__translations",
                queryset=ProductionTranslation.objects.select_related("language"),
            ),
            Prefetch(
                "hall__translations",
                queryset=HallTranslation.objects.select_related("language"),
            ),
            Prefetch(
                "prices__price_rank__translations",
                queryset=PriceRankTranslation.objects.select_related("language"),
            ),
        )
        .order_by("starts_at", "id")
    )