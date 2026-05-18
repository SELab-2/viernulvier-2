"""Admin configuration for the Media app."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import BaseAdmin

from .models import (
    MediaGallery,
    MediaItem,
    MediaItemCrop,
    MediaItemTranslation,
)


class MediaItemInline(admin.TabularInline):
    """Allows managing media items directly within the MediaGallery admin page."""

    model = MediaItem
    extra = 1
    fields = ("type", "format", "original_filename", "position")
    show_change_link = True
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Limit selected columns to keep the gallery inline lightweight."""
        return super().get_queryset(request).only("type", "format", "original_filename", "position", "gallery_id")


class MediaItemTranslationInline(admin.TabularInline):
    """Allows editing translations directly inside the MediaItem admin page."""

    model = MediaItemTranslation
    extra = 1
    fields = ("language", "title", "credits", "link")
    autocomplete_fields = ("language",)
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("language")


class MediaItemCropInline(admin.TabularInline):
    """Allows managing named crop variants directly within the MediaItem admin page."""

    model = MediaItemCrop
    extra = 1
    fields = ("name", "image", "get_url")
    classes = ("collapse",)
    readonly_fields = ("get_url",)

    @admin.display(description="URL")
    def get_url(self, obj: MediaItemCrop) -> str:
        """Return the raw stored crop URL for the inline preview."""
        if obj.image:
            return obj.image.url
        return "-"


@admin.register(MediaGallery)
class MediaGalleryAdmin(BaseAdmin):
    """Admin configuration for MediaGallery objects."""

    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)
    inlines = [MediaItemInline]


@admin.register(MediaItem)
class MediaItemAdmin(BaseAdmin):
    """Admin configuration for MediaItem objects."""

    list_display = (
        "id",
        "gallery",
        "type",
        "format",
        "original_filename",
        "position",
        "width",
        "height",
    )
    list_display_links = ("id", "original_filename")
    list_filter = ("type", "format")
    list_select_related = ("gallery",)
    search_fields = ("original_filename", "gallery__name")
    ordering = ("gallery", "position")
    autocomplete_fields = ("gallery",)
    inlines = [MediaItemTranslationInline, MediaItemCropInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related gallery to avoid N+1 queries on the list page."""
        return super().get_queryset(request).select_related("gallery")

    def get_changeform_initial_data(self, request: HttpRequest) -> dict:
        """Prefill the add-form with a `gallery` GET parameter when present.

        This allows other admins (for example `ProductionAdmin`) to provide
        a direct "Add image" link that opens the MediaItem add form with the
        correct gallery preselected.
        """
        initial = super().get_changeform_initial_data(request)
        gallery_id = request.GET.get("gallery")
        if gallery_id:
            initial["gallery"] = gallery_id
        return initial


@admin.register(MediaItemCrop)
class MediaItemCropAdmin(BaseAdmin):
    """Admin configuration for MediaItem crop variants."""

    list_display = ("id", "media_item", "name", "get_url")
    list_filter = ("name",)
    search_fields = ("name", "media_item__original_filename")
    ordering = ("id",)
    autocomplete_fields = ("media_item",)

    @admin.display(description="Asset URL")
    def get_url(self, obj: MediaItemCrop) -> str:
        """Render a clickable link to the stored crop asset."""
        if obj.image:
            # Makes the URL clickable in the overview.
            return format_html('<a href="{0}" target="_blank">Bekijk bestand</a>', obj.image.url)
        return "-"

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related media_item to avoid N+1 queries."""
        return super().get_queryset(request).select_related("media_item")
