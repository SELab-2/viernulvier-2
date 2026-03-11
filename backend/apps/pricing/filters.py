"""
Filters for the Pricing app.
"""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import Price, PriceRank


class PriceFilter(BaseModelFilter):
    """
    FilterSet for Price list queries.

    Supported query parameters
    --------------------------
    ``type``
        Case-insensitive substring match on the price type identifier
        (e.g. ``?type=student``).
    ``visibility``
        Exact match on the visibility value
        (e.g. ``?visibility=public``).
    ``membership``
        Case-insensitive substring match on the membership requirement
        (e.g. ``?membership=cineville``). Use ``?membership=`` for prices
        with no membership requirement.
    ``cineville_box``
        Boolean flag — ``?cineville_box=true`` returns only Cineville
        box prices.
    ``description``
        Case-insensitive substring match across translated descriptions
        (e.g. ``?description=student``).
    """

    type = django_filters.CharFilter(lookup_expr="icontains")
    membership = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(
        field_name="translations__description",
        lookup_expr="icontains",
        label="Translated description contains",
        distinct=True,
    )

    class Meta:
        model = Price
        fields = ["type", "visibility", "membership", "cineville_box", "external_id"]


class PriceRankFilter(BaseModelFilter):
    """
    FilterSet for PriceRank list queries.

    Supported query parameters
    --------------------------
    ``position``
        Exact match on the rank position (e.g. ``?position=1``).
    ``position_gte``
        Only ranks with a position greater than or equal to the given value.
    ``position_lte``
        Only ranks with a position less than or equal to the given value.
    ``description``
        Case-insensitive substring match across translated descriptions
        (e.g. ``?description=student``).
    """

    position = django_filters.NumberFilter(field_name="position", lookup_expr="exact")
    position_gte = django_filters.NumberFilter(field_name="position", lookup_expr="gte")
    position_lte = django_filters.NumberFilter(field_name="position", lookup_expr="lte")
    description = django_filters.CharFilter(
        field_name="translations__description",
        lookup_expr="icontains",
        label="Translated description contains",
        distinct=True,
    )

    class Meta:
        model = PriceRank
        fields = ["position", "external_id"]