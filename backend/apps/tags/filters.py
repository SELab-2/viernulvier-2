"""
Filters for the Tags app.
"""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import Tag


class TagFilter(BaseModelFilter):
    """
    FilterSet for Tag list queries.

    Supported query parameters
    --------------------------
    ``type``
        Case-insensitive substring match on the internal type / category
        (e.g. ``?type=theme``).
    ``source``
        Case-insensitive substring match on the originating system
        identifier (e.g. ``?source=uitdatabank``).
    ``source_type``
        Case-insensitive substring match on the source sub-classification
        (e.g. ``?source_type=targetAudience``).
    ``is_external``
        Boolean flag - ``?is_external=true`` returns only tags imported
        from an external system.
    ``is_enabled``
        Boolean flag - ``?is_enabled=true`` returns only active tags.
    ``name``
        Case-insensitive substring match across all translated tag names
        (e.g. ``?name=contemporary``).
    """

    type = django_filters.CharFilter(lookup_expr="icontains")
    source = django_filters.CharFilter(lookup_expr="icontains")
    source_type = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(
        field_name="translations__name",
        lookup_expr="icontains",
        label="Translated name contains",
        distinct=True,
    )

    class Meta:
        model = Tag
        fields = ["type", "source", "source_type", "is_external", "is_enabled", "external_id"]
