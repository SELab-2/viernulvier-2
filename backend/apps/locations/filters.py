"""
Filters for the Locations app.
"""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import Hall, Location, Space


class LocationFilter(BaseModelFilter):
    """
    FilterSet for Location list queries.

    Supported query parameters
    --------------------------
    ``city``
        Case-insensitive substring match on the city name
        (e.g. ``?city=gent``).
    ``country``
        Case-insensitive exact match on the country code
        (e.g. ``?country=BE``).
    ``postal_code``
        Exact match on the postal code (e.g. ``?postal_code=9000``).
    ``is_own_location``
        Boolean flag - ``?is_own_location=true`` returns only venues
        owned or operated by the organisation.
    ``name``
        Case-insensitive substring match across translated location names
        (e.g. ``?name=stadsschouwburg``).
    """

    city = django_filters.CharFilter(lookup_expr="icontains")
    country = django_filters.CharFilter(lookup_expr="iexact")
    postal_code = django_filters.CharFilter(lookup_expr="exact")
    name = django_filters.CharFilter(
        field_name="translations__name",
        lookup_expr="icontains",
        label="Translated name contains",
        distinct=True,
    )

    class Meta:
        model = Location
        fields = ["city", "country", "postal_code", "is_own_location", "external_id"]


class SpaceFilter(BaseModelFilter):
    """
    FilterSet for Space list queries.

    Supported query parameters
    --------------------------
    ``location``
        Exact match on the parent location ID (e.g. ``?location=3``).
    ``name``
        Case-insensitive substring match across translated space names
        (e.g. ``?name=foyer``).
    """

    name = django_filters.CharFilter(
        field_name="translations__name",
        lookup_expr="icontains",
        label="Translated name contains",
        distinct=True,
    )

    class Meta:
        model = Space
        fields = ["location", "external_id"]


class HallFilter(BaseModelFilter):
    """
    FilterSet for Hall list queries.

    Supported query parameters
    --------------------------
    ``space``
        Exact match on the parent space ID (e.g. ``?space=2``).
    ``location``
        Exact match on the grandparent location ID via the space -> location
        chain (e.g. ``?location=1``).
    ``seat_selection``
        Boolean flag - ``?seat_selection=true`` returns halls that allow
        visitors to choose a specific seat.
    ``open_seating``
        Boolean flag - ``?open_seating=true`` returns halls with
        general-admission seating.
    ``name``
        Case-insensitive substring match across translated hall names
        (e.g. ``?name=grote+zaal``).
    """

    location = django_filters.NumberFilter(
        field_name="space__location__id",
        label="Location ID",
    )
    name = django_filters.CharFilter(
        field_name="translations__name",
        lookup_expr="icontains",
        label="Translated name contains",
        distinct=True,
    )

    class Meta:
        model = Hall
        fields = ["space", "seat_selection", "open_seating", "external_id"]
