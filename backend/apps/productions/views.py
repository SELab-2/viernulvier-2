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

from django.db.models import Max, Min, OuterRef, Prefetch, Q, QuerySet, Subquery
from django.db.models.functions import Coalesce, Lower
from django.http import HttpRequest
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.blogs.models import Blog
from apps.core.mixins import LanguageAwareMixin
from apps.core.views import ApiModelViewSet
from apps.events.models import Event, EventPrice
from apps.locations.models import HallTranslation, LocationTranslation, SpaceTranslation
from apps.media_library.models import MediaItem
from apps.pricing.models import PriceRankTranslation, PriceTranslation
from apps.tags.models import Tag, TagTranslation

from .filters import ProductionFilter
from .models import Production, ProductionGenre, ProductionTag
from .schemas import production_schema
from .serializers import (
    ProductionLandingStatsSerializer,
    ProductionSerializer,
    ProductionSeriesSerializer,
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
            "total production series, documented years, and published stories."
        ),
        responses={200: ProductionLandingStatsSerializer},
    )
    @action(detail=False, methods=["get"], url_path="landing-stats")
    def landing_stats(self, _request: Request) -> Response:
        """Return pre-aggregated counters used by the frontend homepage."""
        payload = {
            "productions": Production.objects.count(),
            "series": Tag.objects.filter(productions__isnull=False).distinct().count(),
            "years": self._get_documented_years_count(),
            "stories": Blog.objects.filter(published_at__isnull=False).count(),
        }

        serializer = ProductionLandingStatsSerializer(payload)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="series")
    def series(self, request: Request) -> Response:
        """Return production-tag series summaries in a single aggregated endpoint.

        Each result item contains:
        - the tag payload (`tag`)
        - first production start date across the bundle
        - last production end date across the bundle
        - image URL from the most recent production in the bundle
        """
        search_query = (request.query_params.get("search") or "").strip()

        latest_production_id = Subquery(
            Production.objects.filter(tags__id=OuterRef("pk"))
            .annotate(
                latest_end=Max("events__ends_at"),
                latest_start=Max("events__starts_at"),
                latest_timestamp=Coalesce("latest_end", "latest_start"),
            )
            .order_by("-latest_timestamp", "-id")
            .values("id")[:1]
        )

        queryset = (
            Tag.objects.filter(productions__isnull=False)
            .prefetch_related(
                Prefetch(
                    "translations",
                    queryset=TagTranslation.objects.select_related("language"),
                )
            )
            .annotate(
                first_production_start=Min("productions__events__starts_at"),
                last_production_end=Max("productions__events__ends_at"),
                last_production_id=latest_production_id,
            )
            .distinct()
            .order_by("id")
        )

        if search_query:
            queryset = queryset.filter(translations__name__icontains=search_query).distinct()

        page = self.paginate_queryset(queryset)
        series_items = page if page is not None else queryset

        production_ids = [item.last_production_id for item in series_items if item.last_production_id is not None]
        image_by_production_id: dict[int, str | None] = {}

        if production_ids:
            image_query = (
                Production.objects.filter(id__in=production_ids)
                .select_related("media_gallery")
                .prefetch_related(
                    Prefetch(
                        "media_gallery__media_items",
                        queryset=MediaItem.objects.prefetch_related("crops").order_by("position"),
                    )
                )
                .only("id", "media_gallery")
            )

            for production in image_query:
                image_url = None
                media_items = production.media_gallery.media_items.all() if production.media_gallery else []
                if media_items:
                    first_item = media_items[0]
                    first_crop = next(iter(first_item.crops.all()), None)
                    if first_crop and first_crop.image:
                        image_url = request.build_absolute_uri(first_crop.image.url)
                image_by_production_id[production.id] = image_url

        serializer = ProductionSeriesSerializer(
            series_items,
            many=True,
            context={
                **self.get_serializer_context(),
                "last_production_image_by_production_id": image_by_production_id,
            },
        )

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
