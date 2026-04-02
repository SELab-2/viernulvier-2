"""Filters for the Genre app."""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import Genre, GenreUseAs


class GenreUseAsFilter(BaseModelFilter):
    """FilterSet for GenreUseAs list queries.

    Supported query parameters
    --------------------------
    ``name``
        Case-insensitive substring match on the use-as label
        (e.g. ``?name=tag``).
    """

    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = GenreUseAs
        fields = ["name", "external_id"]


class GenreFilter(BaseModelFilter):
    """FilterSet for Genre list queries.

    Supported query parameters
    --------------------------
    ``use_as``
        Exact match on the ``GenreUseAs`` ID (e.g. ``?use_as=1``).
    ``type``
        Case-insensitive substring match on the internal type identifier
        (e.g. ``?type=theater``).
    ``vendor_id``
        Case-insensitive substring match on the upstream vendor identifier
        (e.g. ``?vendor_id=abc-123``).
    ``name``
        Case-insensitive substring match across translated genre names
        (e.g. ``?name=festival``).
    """

    type = django_filters.CharFilter(lookup_expr="icontains")
    vendor_id = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(
        field_name="translations__name",
        lookup_expr="icontains",
        label="Translated name contains",
        distinct=True,
    )

    class Meta:
        model = Genre
        fields = ["use_as", "type", "vendor_id", "external_id"]
