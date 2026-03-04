"""
ViewSets for the Events app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.

An event is a scheduled occurrence of a production in a specific hall.
Each event carries a set of ``EventPrice`` entries that define ticket
capacity and amount per price rank.
"""

from django.db.models import Prefetch

from drf_spectacular.utils import extend_schema

from apps.core.views import ApiModelViewSet

from apps.productions.models import ProductionTranslation
from apps.locations.models import HallTranslation
from apps.pricing.models import PriceRankTranslation

from .models import Event, EventPrice
from .schemas import event_schema
from .serializers import EventSerializer

_TAG = "Events"  # Reusable tag for all event-related endpoints in the OpenAPI docs


@extend_schema(tags=[_TAG])
@event_schema
class EventViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Event objects.

    An event is a scheduled performance of a production inside a hall.
    It carries a ``starts_at`` / ``ends_at`` window (both enforced by a
    DB-level check constraint) and an optional ``ticketing_url``.

    Prices are nested read-only via the ``prices`` relation; they must be
    managed through the dedicated **Event Price** endpoints.

    Queryset strategy
    -----------------
    - ``select_related`` covers the single-row FK chain from event to hall
      and further up to space and location.
    - ``prefetch_related`` with explicit ``Prefetch`` objects is used for
      all one-to-many relations to avoid N+1 queries:

        * ``prices`` — ``EventPrice`` rows with their ``price_rank`` joined
          in a single query.
        * ``production__translations`` — needed by the serialiser to resolve
          localised production metadata.
        * ``hall__translations`` — needed to resolve localised hall names.
        * ``prices__price_rank__translations`` — needed to resolve localised
          price rank descriptions when the API consumer expands that data.
    """

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
