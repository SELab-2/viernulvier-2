"""Filters for the Productions app."""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import Production


class ProductionFilter(BaseModelFilter):
    """FilterSet for Production list queries.

    Supported query parameters
    --------------------------
    ``attendance_mode``
        Exact match on the attendance mode
        (e.g. ``?attendance_mode=offline``).
        Accepted values: ``offline``, ``online``.
    ``performer_type``
        Exact match on the performer type
        (e.g. ``?performer_type=solo``).
        Accepted values: ``group``, ``solo``.
    ``uit_database_type``
        Exact match on the UIT Database type FK ID
        (e.g. ``?uit_database_type=7``).
    ``genre``
        Match on one or multiple genre IDs. Multiple values can be passed
        as repeated query params (``?genre=2&genre=9``) or comma-separated
        (``?genre=2,9``). Values are combined with AND semantics.
    ``tag``
        Match on one or multiple tag IDs. Multiple values can be passed
        as repeated query params (``?tag=5&tag=8``) or comma-separated
        (``?tag=5,8``). Values are combined with AND semantics.
    ``has_media``
        Boolean flag - ``?has_media=true`` returns only productions with
        a media gallery assigned.
    ``title``
        Case-insensitive substring match across all translated titles
        (e.g. ``?title=hamlet``).
    ``artist_name``
        Case-insensitive substring match across all translated artist names
        (e.g. ``?artist_name=toneelschuur``).
    """

    genre = django_filters.CharFilter(
        method="filter_genre",
        label="Genre ID(s)",
        distinct=True,
    )
    tag = django_filters.CharFilter(
        method="filter_tag",
        label="Tag ID(s)",
        distinct=True,
    )
    has_media = django_filters.BooleanFilter(
        field_name="media_gallery",
        method="filter_has_media",
        label="Has media gallery",
    )
    title = django_filters.CharFilter(
        field_name="translations__title",
        lookup_expr="icontains",
        label="Translated title contains",
        distinct=True,
    )
    artist_name = django_filters.CharFilter(
        field_name="translations__artist_name",
        lookup_expr="icontains",
        label="Translated artist name contains",
        distinct=True,
    )
    first_event_start_after = django_filters.IsoDateTimeFilter(
        field_name="events__starts_at",
        lookup_expr="gte",
        label="Has an event starting on or after (ISO 8601)",
        distinct=True,
    )
    first_event_start_before = django_filters.IsoDateTimeFilter(
        field_name="events__starts_at",
        lookup_expr="lte",
        label="Has an event starting on or before (ISO 8601)",
        distinct=True,
    )

    def filter_has_media(self, queryset: Production, _name: str, value: bool) -> Production:
        """Filter productions by whether they have a media gallery assigned."""
        if value:
            return queryset.exclude(media_gallery__isnull=True)
        return queryset.filter(media_gallery__isnull=True)

    def _extract_multi_id_values(self, name: str, value: str | None) -> list[int]:
        """Return deduplicated IDs from repeated and comma-separated query values."""
        raw_values: list[str] = []

        if self.request is not None:
            raw_values.extend(self.request.query_params.getlist(name))

        if hasattr(self.data, "getlist"):
            raw_values.extend(self.data.getlist(name))

        if value not in (None, ""):
            raw_values.append(value)

        parsed: list[int] = []
        for raw in raw_values:
            for part in str(raw).split(","):
                stripped = part.strip()
                if not stripped:
                    continue
                try:
                    parsed_value = int(stripped)
                except ValueError:
                    continue
                if parsed_value not in parsed:
                    parsed.append(parsed_value)

        return parsed

    def filter_genre(self, queryset: Production, name: str, value: str | None) -> Production:
        """Filter productions that contain all provided genre IDs."""
        genre_ids = self._extract_multi_id_values(name, value)
        if not genre_ids:
            return queryset

        filtered = queryset
        for genre_id in genre_ids:
            filtered = filtered.filter(genres__id=genre_id)
        return filtered.distinct()

    def filter_tag(self, queryset: Production, name: str, value: str | None) -> Production:
        """Filter productions that contain all provided tag IDs."""
        tag_ids = self._extract_multi_id_values(name, value)
        if not tag_ids:
            return queryset

        filtered = queryset
        for tag_id in tag_ids:
            filtered = filtered.filter(tags__id=tag_id)
        return filtered.distinct()

    class Meta:
        model = Production
        fields = [
            "attendance_mode",
            "performer_type",
            "uit_database_type",
            "genre",
            "tag",
            "has_media",
            "external_id",
            "first_event_start_after",
            "first_event_start_before",
        ]
