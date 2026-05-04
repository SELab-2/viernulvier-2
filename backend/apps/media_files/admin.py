"""Admin configuration for the Media Files app."""

from django import forms
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import BaseAdmin

from .models import MediaFile, MediaFileTranslation


class MediaFileAdminForm(forms.ModelForm):
    """Admin form that restricts selectable upload file types."""

    class Meta:
        model = MediaFile
        fields = [
            "external_id",
            "file",
            "filename",
        ]
        widgets = {
            "file": forms.FileInput(
                attrs={
                    "accept": ".jpg,.jpeg,.png,.webp,.pdf,image/jpeg,image/png,image/webp,application/pdf",
                },
            ),
        }


class MediaFileTranslationInline(admin.TabularInline):
    """Inline for editing localised media descriptions inside the MediaFile admin."""

    model = MediaFileTranslation
    extra = 1
    autocomplete_fields = ("language",)
    fields = ("language", "description")
    classes = ("collapse",)
    ordering = ("language__code",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("language")


@admin.register(MediaFile)
class MediaFileAdmin(BaseAdmin):
    """Admin configuration for the MediaFile model."""

    form = MediaFileAdminForm

    list_display = (
        "id",
        "filename",
        "display_description_preview",
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
        "translations__description",
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
        "mime_type",
        "size_bytes",
        "file_type",
        "created_at",
    )

    inlines = [MediaFileTranslationInline]

    class Media:
        js = ("admin/js/mediafile_upload_fix.js",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Prefetch translations to avoid N+1 queries in admin screens."""
        return super().get_queryset(request).prefetch_related("translations__language")

    @admin.display(description="Description")
    def display_description_preview(self, obj: MediaFile) -> str:
        """Render a shortened base-language description in admin list view."""
        description = obj.get_base_display_name(
            related_name="translations",
            name_field="description",
            fallback=None,
        )
        if not description:
            return "-"
        if len(description) <= 80:
            return description
        return f"{description[:77]}..."

    @admin.display(description="File")
    def file_link(self, obj: MediaFile) -> str:
        """Render a link to the uploaded file when available."""
        if not obj.file:
            return "-"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Open file</a>',
            obj.file.url,
        )
