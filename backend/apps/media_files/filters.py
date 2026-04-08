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
    ``original_name``
        Case-insensitive substring match on the original uploaded filename
        (e.g. ``?original_name=poster``).
    ``uploaded_by``
        Exact match on uploader user id.
    ``external_id``
        Case-insensitive exact match on the inherited external identifier.
    """

    file_type = django_filters.CharFilter(lookup_expr="iexact")
    mime_type = django_filters.CharFilter(lookup_expr="iexact")
    original_name = django_filters.CharFilter(lookup_expr="icontains")
    uploaded_by = django_filters.NumberFilter(field_name="uploaded_by_id")

    class Meta:
        model = MediaFile
        fields = [
            "file_type",
            "mime_type",
            "original_name",
            "uploaded_by",
            "external_id",
        ]
        