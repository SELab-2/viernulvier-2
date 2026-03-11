"""
Filters for the Language app.
"""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import Language


class LanguageFilter(BaseModelFilter):
    """
    FilterSet for Language list queries.

    Supported query parameters
    --------------------------
    ``code``
        Case-insensitive exact match on the ISO 639-1 code
        (e.g. ``?code=nl``). Accepts both ``nl`` and ``NL``.
    ``name``
        Case-insensitive substring match on the display name
        (e.g. ``?name=dutch``).
    ``is_active``
        Boolean flag — ``?is_active=true`` returns only active languages.
    """

    code = django_filters.CharFilter(lookup_expr="iexact")
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Language
        fields = ["code", "name", "is_active", "external_id"]