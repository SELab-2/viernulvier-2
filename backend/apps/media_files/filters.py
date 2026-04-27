"""Filters for the Media Files app."""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import MediaFile


class MediaFileFilter(BaseModelFilter):
    """FilterSet for MediaFile list queries.

    Supported query parameters
    --------------------------
    ``file_type``
        Case-insensitive exact match on the normalized internal file type
        (e.g. ``?file_type=pdf`` or ``?file_type=image``).
    ``mime_type``
        Case-insensitive exact match on the stored MIME type
        (e.g. ``?mime_type=application/pdf``).
    ``filename``
        Case-insensitive substring match on the original uploaded filename
        (e.g. ``?filename=poster``).
    ``description``
        Case-insensitive substring match across all translated descriptions.
    ``external_id``
        Case-insensitive exact match on the inherited external identifier.
    """

    file_type = django_filters.CharFilter(lookup_expr="iexact")
    mime_type = django_filters.CharFilter(lookup_expr="iexact")
    filename = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(
        field_name="translations__description",
        lookup_expr="icontains",
        label="Translated description contains",
        distinct=True,
    )

    class Meta:
        model = MediaFile
        fields = [
            "file_type",
            "mime_type",
            "filename",
            "description",
            "external_id",
        ]
