"""Filters for the Blog app."""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import Blog


class BlogFilter(BaseModelFilter):
    """FilterSet for Blog list queries.

    Supported query parameters
    --------------------------
    ``slug``
        Case-insensitive substring match on the slug
        (e.g. ``?slug=techno``).
    ``title``
        Case-insensitive substring match across translated blog titles
        (e.g. ``?title=festival``).
    ``published``
        Boolean filter to show only published or draft posts.
        - ``?published=true`` returns posts with a non-null ``published_at``
        - ``?published=false`` returns drafts (null ``published_at``)
    ``production``
        Filter by linked production ID (e.g. ``?production=42``).
    """

    slug = django_filters.CharFilter(lookup_expr="icontains")
    
    title = django_filters.CharFilter(
        field_name="translations__title",
        lookup_expr="icontains",
        label="Translated title contains",
        distinct=True,
    )
    
    published = django_filters.BooleanFilter(
        method="filter_published",
        label="Published status (true=published, false=draft)",
    )
    
    production = django_filters.NumberFilter(
        field_name="productions__id",
        label="Production ID",
        distinct=True,
    )

    class Meta:
        model = Blog
        fields = ["slug", "external_id"]

    def filter_published(self, queryset, name, value):
        """Filter by published status.
        
        - True: only published posts (published_at is not null)
        - False: only drafts (published_at is null)
        """
        if value is True:
            return queryset.filter(published_at__isnull=False)
        elif value is False:
            return queryset.filter(published_at__isnull=True)
        return queryset