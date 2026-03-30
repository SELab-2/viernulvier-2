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
    ``uit_database_theme``
        Exact match on the UIT Database theme FK ID
        (e.g. ``?uit_database_theme=3``).
    ``uit_database_type``
        Exact match on the UIT Database type FK ID
        (e.g. ``?uit_database_type=7``).
    ``genre``
        Exact match on a genre ID - returns all productions that have this
        genre attached (e.g. ``?genre=2``).
    ``tag``
        Exact match on a tag ID - returns all productions that have this
        tag attached (e.g. ``?tag=5``).
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

    genre = django_filters.NumberFilter(
        field_name="genres__id",
        label="Genre ID",
        distinct=True,
    )
    tag = django_filters.NumberFilter(
        field_name="tags__id",
        label="Tag ID",
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

    def filter_has_media(self, queryset: Production, _name: str, value: bool) -> Production:
        """Filter productions by whether they have a media gallery assigned."""
        if value:
            return queryset.exclude(media_gallery__isnull=True)
        return queryset.filter(media_gallery__isnull=True)

    class Meta:
        model = Production
        fields = [
            "attendance_mode",
            "performer_type",
            "uit_database_theme",
            "uit_database_type",
            "genre",
            "tag",
            "has_media",
            "external_id",
        ]
