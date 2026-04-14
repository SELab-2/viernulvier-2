"""Custom ordering filter that places null values last in the ordering."""

from django.db.models import F, QuerySet
from django.http import HttpRequest
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView


class NullsLastOrderingFilter(OrderingFilter):
    """Ordering filter that always sorts NULL values last.

    Extends DRF's built-in ``OrderingFilter`` with a single behavioural
    change: when a queryset is ordered by a nullable field (e.g. a
    language-aware annotation that resolves to ``NULL`` when no translation
    exists, or an event date that is absent for productions without events),
    those rows are placed at the **end** of the result set regardless of
    whether the sort direction is ascending or descending.

    Without this filter, Django's default behaviour places ``NULL`` values
    first for ascending sorts and last for descending sorts, which causes
    items without data to jump to the top when a user selects A -> Z ordering.
    """

    def filter_queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet,
        view: APIView,
    ) -> QuerySet:
        """Apply nulls-last ordering to the queryset.

        Retrieves the requested ordering fields via the parent implementation,
        then rewrites each field as an explicit ``F().asc(nulls_last=True)``
        or ``F().desc(nulls_last=True)`` expression before passing them to
        ``order_by``.
        """
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset

        nulls_last = []
        for field in ordering:
            if field.startswith("-"):
                nulls_last.append(F(field[1:]).desc(nulls_last=True))
            else:
                nulls_last.append(F(field).asc(nulls_last=True))

        return queryset.order_by(*nulls_last)
