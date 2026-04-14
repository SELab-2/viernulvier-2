"""Custom ordering filter that places null values last in the ordering."""
from rest_framework.filters import OrderingFilter
from django.db.models import F

class NullsLastOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        """Override the default ordering filter to place null values last."""
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