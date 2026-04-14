"""ViewSets for the Events app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.

An event is a scheduled occurrence of a production in a specific hall.
Each event carries a set of ``EventPrice`` entries that define ticket
capacity and amount per price rank.
"""

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema

from apps.core.views import ApiModelViewSet
from apps.locations.models import HallTranslation, LocationTranslation, SpaceTranslation
from apps.media_library.models import MediaItem
from apps.pricing.models import PriceRankTranslation, PriceTranslation
from apps.productions.models import ProductionGenre, ProductionTranslation

from .filters import EventFilter
from .models import Event, EventPrice
from .schemas import event_schema
from .serializers import EventSerializer

_TAG = "Events"


@extend_schema(tags=[_TAG])
@event_schema
class EventViewSet(ApiModelViewSet):
    """CRUD endpoints for Event objects.

    An event is a scheduled performance of a production inside a hall.
    It carries a ``starts_at`` / ``ends_at`` window (both enforced by a
    DB-level check constraint).

    Prices are nested read-only via the ``prices`` relation; they must be
    managed through the dedicated **Event Price** endpoints.

    Access rules
    ------------
    - **Public key**   -> read-only (``list``, ``retrieve``).
    - **Internal key** -> full CRUD.

    Filtering
    ---------
    ``?production=12``
        Events belonging to a specific production.
    ``?hall=3``
        Events scheduled in a specific hall.
    ``?location=1``
        Events in any hall belonging to a specific location.
    ``?starts_at_after=2024-06-01T00:00:00Z``
        Events starting on or after the given datetime (ISO 8601).
    ``?starts_at_before=2024-12-31T23:59:59Z``
        Events starting on or before the given datetime (ISO 8601).
    ``?ends_at_after=2024-06-01T00:00:00Z``
        Events ending on or after the given datetime (ISO 8601).
    ``?ends_at_before=2024-12-31T23:59:59Z``
        Events ending on or before the given datetime (ISO 8601).
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=starts_at`` / ``?ordering=-starts_at``
        Chronological by start time (default ascending).
    ``?ordering=ends_at`` / ``?ordering=-ends_at``
        Chronological by end time.
    ``?ordering=production`` / ``?ordering=hall``
        Group by related FK ID.

    Search
    ------
    ``?search=hamlet``
        Full-text search across the production's translated titles and
        the hall's translated names.

    Queryset strategy
    -----------------
    - ``select_related`` covers the single-row FK chain from event -> hall
      -> space -> location.
    - ``prefetch_related`` with explicit ``Prefetch`` objects covers all
      one-to-many relations to avoid N+1 queries on list responses.
    """

    serializer_class = EventSerializer

    queryset = (
        Event.objects.select_related(
            "production",
            "production__uit_database_type",
            "hall",
            "hall__space",
            "hall__space__location",
        )
        .prefetch_related(
            Prefetch(
                "prices",
                queryset=EventPrice.objects.select_related("price_rank", "price"),
            ),
            Prefetch(
                "production__translations",
                queryset=ProductionTranslation.objects.select_related("language"),
            ),
            "production__tags",
            "production__tags__translations__language",
            Prefetch(
                "production__productiongenre_set",
                queryset=(
                    ProductionGenre.objects.select_related("genre", "genre__use_as")
                    .prefetch_related("genre__translations__language")
                    .order_by("position")
                ),
                to_attr="prefetched_production_genres",
            ),
            Prefetch(
                "hall__translations",
                queryset=HallTranslation.objects.select_related("language"),
            ),
            Prefetch(
                "hall__space__translations",
                queryset=SpaceTranslation.objects.select_related("language"),
            ),
            Prefetch(
                "hall__space__location__translations",
                queryset=LocationTranslation.objects.select_related("language"),
            ),
            Prefetch(
                "production__media_gallery__media_items",
                queryset=MediaItem.objects.prefetch_related(
                    "translations__language",
                    "crops",
                ).order_by("position"),
            ),
            Prefetch(
                "prices__price_rank__translations",
                queryset=PriceRankTranslation.objects.select_related("language"),
            ),
            Prefetch(
                "prices__price__translations",
                queryset=PriceTranslation.objects.select_related("language"),
            ),
        )
        .order_by("starts_at", "id")
    )

    filterset_class = EventFilter
    ordering_fields = ["starts_at", "ends_at", "production", "hall"]
    ordering = ["starts_at", "id"]
    search_fields = [
        "production__translations__title",
        "hall__translations__name",
    ]
