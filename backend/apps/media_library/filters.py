"""Filters for the Media app."""

import django_filters

from apps.core.filters import BaseModelFilter

from .models import MediaGallery, MediaItem


class MediaGalleryFilter(BaseModelFilter):
    """FilterSet for MediaGallery list queries.

    Supported query parameters
    --------------------------
    ``name``
        Case-insensitive substring match on the gallery name
        (e.g. ``?name=season``).
    """

    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = MediaGallery
        fields = ["name", "external_id"]


class MediaItemFilter(BaseModelFilter):
    """FilterSet for MediaItem list queries.

    Supported query parameters
    --------------------------
    ``gallery``
        Exact match on the parent gallery ID (e.g. ``?gallery=5``).
    ``type``
        Exact match on the media type
        (e.g. ``?type=foto``).
        Accepted values: ``foto``, ``video``, ``audio``, ``other``.
    ``file_format``
        Case-insensitive substring match on the file format / extension
        (e.g. ``?file_format=jpg``).
    ``original_filename``
        Case-insensitive substring match on the original filename
        (e.g. ``?original_filename=poster``).
    """

    file_format = django_filters.CharFilter(field_name="format", lookup_expr="icontains")
    original_filename = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = MediaItem
        fields = ["gallery", "type", "file_format", "original_filename", "external_id"]
