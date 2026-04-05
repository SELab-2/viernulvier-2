"""Filters for the Imports app."""

from django.db.models import Q, QuerySet
import django_filters

from apps.core.filters import BaseModelFilter

from .models import ImportLog


class ImportLogFilter(BaseModelFilter):
    """FilterSet for ImportLog list queries.

    Supported query parameters
    --------------------------
    ``status``
        Exact match on the import status
        (e.g. ``?status=FAILED``).
        Accepted values: ``PENDING``, ``IN_PROGRESS``, ``PARTIAL_SUCCESS``,
        ``SUCCESS``, ``FAILED``.
    ``source``
        Case-insensitive substring match on the source identifier
        (e.g. ``?source=viernulvier``).
    ``started_at_after``
        Only runs that started on or after the given datetime
        (e.g. ``?started_at_after=2024-01-01T00:00:00Z``).
    ``started_at_before``
        Only runs that started on or before the given datetime.
    ``finished_at_after``
        Only runs that finished on or after the given datetime.
    ``finished_at_before``
        Only runs that finished on or before the given datetime.
    ``has_error``
        Boolean - ``?has_error=true`` returns only runs with an error message set.
    """

    source = django_filters.CharFilter(lookup_expr="icontains")

    status = django_filters.ChoiceFilter(choices=ImportLog.Status.choices)

    started_at_after = django_filters.IsoDateTimeFilter(field_name="started_at", lookup_expr="gte")
    started_at_before = django_filters.IsoDateTimeFilter(field_name="started_at", lookup_expr="lte")
    finished_at_after = django_filters.IsoDateTimeFilter(field_name="finished_at", lookup_expr="gte")
    finished_at_before = django_filters.IsoDateTimeFilter(field_name="finished_at", lookup_expr="lte")

    has_error = django_filters.BooleanFilter(
        field_name="error_message",
        method="filter_has_error",
        label="Has error message",
    )

    def filter_has_error(self, queryset: QuerySet[ImportLog], _name: str, value: bool) -> QuerySet:
        """Filter by presence of an error message."""
        if value:
            return queryset.exclude(error_message="").exclude(error_message__isnull=True)

        return queryset.filter(Q(error_message="") | Q(error_message__isnull=True))

    class Meta:
        model = ImportLog
        fields = [
            "status",
            "source",
            "started_at_after",
            "started_at_before",
            "finished_at_after",
            "finished_at_before",
            "has_error",
            "external_id",
        ]
