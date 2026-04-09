"""Admin configuration for the Media Files app."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import BaseAdmin

from .models import MediaFile


@admin.register(MediaFile)
class MediaFileAdmin(BaseAdmin):
    """Admin configuration for the MediaFile model.

    The list view surfaces the core file metadata so editors can quickly
    inspect uploaded assets such as posters and PDF documents.

    Queryset strategy
    -----------------
    ``select_related("uploaded_by")`` prevents N+1 queries on the list page
    where the uploader is shown in ``list_display``.
    """

    list_display = (
        "id",
        "filename",
        "file_type",
        "mime_type",
        "size_bytes",
        "uploaded_by",
        "created_at",
        "file_link",
    )

    list_filter = (
        "file_type",
        "mime_type",
        "created_at",
    )

    search_fields = (
        "filename",
        "mime_type",
        "external_id",
        "uploaded_by__username",
        "uploaded_by__email",
    )

    readonly_fields = (
        "id",
        "external_id",
        "mime_type",
        "size_bytes",
        "file_type",
        "uploaded_by",
        "created_at",
        "file_link",
    )

    ordering = ("-created_at",)

    fields = (
        "id",
        "external_id",
        "file",
        "file_link",
        "filename",
        "mime_type",
        "size_bytes",
        "file_type",
        "uploaded_by",
        "created_at",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related uploader to avoid N+1 queries."""
        return super().get_queryset(request).select_related("uploaded_by")

    def save_model(self, request: HttpRequest, obj: MediaFile, form, change: bool) -> None:
        """Store the logged-in admin user as uploader when missing."""
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="File")
    def file_link(self, obj: MediaFile) -> str:
        """Render a link to the uploaded file when available."""
        if not obj.file:
            return "-"

        return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">Open file</a>', obj.file.url)
