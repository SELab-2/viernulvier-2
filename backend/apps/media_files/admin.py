"""Admin configuration for the Media Files app."""

from django.contrib import admin
from django.utils.html import format_html

from apps.core.admin import BaseAdmin

from .models import MediaFile


@admin.register(MediaFile)
class MediaFileAdmin(BaseAdmin):
    """Admin configuration for the MediaFile model."""

    list_display = (
        "id",
        "filename",
        "description_preview",
        "file_type",
        "mime_type",
        "size_bytes",
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
        "description",
        "mime_type",
        "external_id",
    )

    readonly_fields = (
        "id",
        "mime_type",
        "size_bytes",
        "file_type",
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
        "description",
        "mime_type",
        "size_bytes",
        "file_type",
        "created_at",
    )

    @admin.display(description="Description")
    def description_preview(self, obj: MediaFile) -> str:
        """Render a shortened description in admin list view."""
        if not obj.description:
            return "-"
        if len(obj.description) <= 80:
            return obj.description
        return f"{obj.description[:77]}..."

    @admin.display(description="File")
    def file_link(self, obj: MediaFile) -> str:
        """Render a link to the uploaded file when available."""
        if not obj.file:
            return "-"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Open file</a>',
            obj.file.url,
        )
