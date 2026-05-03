"""ViewSets for the Productions app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.

Productions are the core catalogue entity. Each production may have one
or more events and carries translatable metadata.

Translation Format
------------------
Metadata fields (title, description, etc.) are returned as dictionaries
containing all available translations (e.g., {"nl": "...", "en": "..."}).
`Accept-Language` influences ordering/search preference only, while
responses still include all translations in a single payload.
"""

from django.db.models import Max, Min, Prefetch, Q, QuerySet
from django.db.models.functions import Coalesce, Lower
from django.http import HttpRequest
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.blogs.models import Blog
from apps.core.mixins import LanguageAwareMixin
from apps.core.views import ApiModelViewSet, cache_api_view
from apps.events.models import Event, EventPrice
from apps.locations.models import HallTranslation, LocationTranslation, SpaceTranslation
from apps.media_library.models import MediaItem
from apps.pricing.models import PriceRankTranslation, PriceTranslation
from apps.tags.models import Tag

from .filters import ProductionFilter
from .models import Production, ProductionGenre, ProductionTag
from .schemas import production_schema
from .serializers import (
    ProductionLandingStatsSerializer,
    ProductionSerializer,
)

_TAG = "Productions"


@extend_schema(tags=[_TAG])
@production_schema
class ProductionViewSet(LanguageAwareMixin, ApiModelViewSet):
    """CRUD endpoints for Production objects.

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
    ``?ordering=first_event_start`` / ``?ordering=-first_event_start``
        By the start date of the earliest linked event. Productions
        without any events are always sorted last, regardless of direction.
    ``?ordering=last_event_end`` / ``?ordering=-last_event_end``
        By the end date of the latest linked event. Productions without
        any events are always sorted last, regardless of direction.
    ``?ordering=title_sort`` / ``?ordering=-title_sort``
        Alphabetical by title in the preferred request language, with
        fallback to any available translation. Productions without any
        translation are always sorted last, regardless of direction.

    Search
    ------
    ``?search=hamlet``
        Full-text search across preferred-language ``title``,
        ``artist_name``, and ``tagline`` values, with fallback to any
        available translation.

    Queryset strategy
    -----------------
    - ``select_related`` for single-row FK relations.
    - ``prefetch_related`` for translations, tags, and ordered genres to
      avoid N+1 queries on list responses.
    """

    serializer_class = ProductionSerializer
    queryset = (
        Production.objects.select_related(
            "uit_database_type",
            "media_gallery",
        )
        .prefetch_related(
            "translations__language",
            Prefetch(
                "productiongenre_set",
                queryset=ProductionGenre.objects.select_related("genre").order_by("position"),
                to_attr="prefetched_production_genres",
            ),
            Prefetch(
                "productiontag_set",
                queryset=ProductionTag.objects.select_related("tag")
                .prefetch_related(
                    "translations__language",
                    "tag__translations__language",
                )
                .order_by("tag__type", "id"),
                to_attr="prefetched_production_tags",
            ),
            Prefetch(
                "media_gallery__media_items",
                queryset=MediaItem.objects.prefetch_related(
                    "translations__language",
                    "crops",
                ).order_by("position"),
            ),
        )
        .annotate(
            # Computed once at the queryset level — not language-dependent.
            first_event_start=Min("events__starts_at"),
            last_event_end=Max("events__ends_at"),
        )
    )

    filterset_class = ProductionFilter
    ordering_fields = [
        "id",
        "attendance_mode",
        "performer_type",
        "first_event_start",
        "last_event_end",
        "title_sort",
    ]
    ordering = ["-id"]
    search_fields = [
        "title_sort",
        "artist_name_search",
        "tagline_search",
    ]

    def get_queryset(self) -> QuerySet[Production]:
        """Annotate language-aware title and search fields for ordering and search.

        ``title_sort`` is a single annotation reused for both alphabetical
        ordering (``?ordering=title_sort``) and full-text search
        (``?search=...``). It resolves to the title in the preferred request
        language and falls back to any available translation when none exists
        for that language.

        ``artist_name_search`` and ``tagline_search`` follow the same
        language-preference logic and are used only for full-text search.

        Items without any translation at all resolve to NULL and are placed
        last by :class:`~apps.core.ordering.NullsLastOrderingFilter`.
        """
        language_code = self._get_request_language_code()
        queryset = super().get_queryset()

        return queryset.annotate(
            title_sort=Lower(
                Coalesce(
                    Min(
                        "translations__title",
                        filter=Q(translations__language__code=language_code) & ~Q(translations__title=""),
                    ),
                    Min("translations__title", filter=~Q(translations__title="")),
                )
            ),
            artist_name_search=Lower(
                Coalesce(
                    Min(
                        "translations__artist_name",
                        filter=Q(translations__language__code=language_code) & ~Q(translations__artist_name=""),
                    ),
                    Min("translations__artist_name", filter=~Q(translations__artist_name="")),
                )
            ),
            tagline_search=Lower(
                Coalesce(
                    Min(
                        "translations__tagline",
                        filter=Q(translations__language__code=language_code) & ~Q(translations__tagline=""),
                    ),
                    Min("translations__tagline", filter=~Q(translations__tagline="")),
                )
            ),
        )

    @property
    def includes(self) -> set[str]:
        """Parse the 'include' query parameter into a set of related fields to include."""
        return set(self.request.query_params.get("include", "").split(","))

    def get_serializer(self, *args: tuple, **kwargs: dict) -> ProductionSerializer:
        """Pass the 'include' query parameter to the serializer context for dynamic field inclusion."""
        kwargs.setdefault("context", self.get_serializer_context())
        kwargs["context"]["include"] = self.includes
        return super().get_serializer(*args, **kwargs)

    def retrieve(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> HttpRequest:
        """Retrieve a production by its ID, with optional inclusion of related events.

        When events are included, the queryset is extended with additional
        prefetches for prices, hall, space, and location translations to
        avoid N+1 queries on the detail response.
        """
        if "events" in self.includes:
            self.queryset = self.queryset.prefetch_related(
                Prefetch(
                    "events",
                    queryset=Event.objects.prefetch_related(
                        Prefetch(
                            "prices",
                            queryset=EventPrice.objects.select_related("price_rank", "price"),
                        ),
                        Prefetch(
                            "prices__price_rank__translations",
                            queryset=PriceRankTranslation.objects.select_related("language"),
                        ),
                        Prefetch(
                            "prices__price__translations",
                            queryset=PriceTranslation.objects.select_related("language"),
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
                    ).select_related("hall__space__location"),
                ),
            )

        return super().retrieve(request, *args, **kwargs)

    @staticmethod
    def _get_documented_years_count() -> int:
        """Count unique years covered by event start/end timestamps."""
        start_years = {value.year for value in Event.objects.exclude(starts_at__isnull=True).dates("starts_at", "year")}
        end_years = {value.year for value in Event.objects.exclude(ends_at__isnull=True).dates("ends_at", "year")}
        return len(start_years | end_years)

    @extend_schema(
        summary="Retrieve landing archive stats",
        description=(
            "Returns compact counters for the homepage stats bar: total productions, "
            "total production series, documented years, and published blogs."
        ),
        responses={200: ProductionLandingStatsSerializer},
    )
    @method_decorator(cache_api_view())
    @action(detail=False, methods=["get"], url_path="landing-stats")
    def landing_stats(self, _request: Request) -> Response:
        """Return pre-aggregated counters used by the frontend homepage."""
        payload = {
            "productions": Production.objects.count(),
            "series": Tag.objects.filter(productions__isnull=False).distinct().count(),
            "years": self._get_documented_years_count(),
            "blogs": Blog.objects.filter(published_at__isnull=False).count(),
        }

        serializer = ProductionLandingStatsSerializer(payload)
        return Response(serializer.data)

