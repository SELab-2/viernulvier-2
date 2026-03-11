"""
Filters for the Events app.
"""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import Event
from django.db.models import Q

class EventFilter(BaseModelFilter):
    """
    FilterSet for Event list queries.

    Supported query parameters
    --------------------------
    ``production``
        Exact match on the production ID (e.g. ``?production=12``).
    ``hall``
        Exact match on the hall ID (e.g. ``?hall=3``).
    ``location``
        Exact match on the location ID via the hall -> space -> location
        chain (e.g. ``?location=1``).
    ``starts_at_after``
        Only events starting on or after the given datetime
        (e.g. ``?starts_at_after=2024-06-01T00:00:00Z``).
    ``starts_at_before``
        Only events starting on or before the given datetime
        (e.g. ``?starts_at_before=2024-12-31T23:59:59Z``).
    ``ends_at_after``
        Only events ending on or after the given datetime.
    ``ends_at_before``
        Only events ending on or before the given datetime.
    """

    production = django_filters.NumberFilter(field_name="production__id")
    hall = django_filters.NumberFilter(field_name="hall__id")
    location = django_filters.NumberFilter(field_name="hall__space__location__id")

    starts_at_after = django_filters.IsoDateTimeFilter(
        field_name="starts_at", lookup_expr="gte"
    )
    starts_at_before = django_filters.IsoDateTimeFilter(
        field_name="starts_at", lookup_expr="lte"
    )
    ends_at_after = django_filters.IsoDateTimeFilter(
        field_name="ends_at", lookup_expr="gte"
    )
    ends_at_before = django_filters.IsoDateTimeFilter(
        field_name="ends_at", lookup_expr="lte"
    )

    class Meta:
        model = Event
        fields = [
            "production",
            "hall",
            "location",
            "starts_at_after",
            "starts_at_before",
            "ends_at_after",
            "ends_at_before",
            "external_id",
        ]