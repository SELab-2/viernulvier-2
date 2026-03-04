"""Admin configuration for the Media app."""

from django.contrib import admin

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


class MediaItemTranslationInline(admin.TabularInline):
    """Allows editing translations directly inside the MediaItem admin page."""

    model = MediaItemTranslation
    extra = 1
    fields = ("language", "title", "credits", "link")
    autocomplete_fields = ("language",)
    classes = ("collapse",)


class MediaItemCropInline(admin.TabularInline):
    """Allows managing named crop variants directly within the MediaItem admin page."""

    model = MediaItemCrop
    extra = 1
    fields = ("name", "url")


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
    list_filter = ("type", "format", "gallery")
    list_select_related = ("gallery",)
    search_fields = ("original_filename", "gallery__name")
    ordering = ("gallery", "position")
    autocomplete_fields = ("gallery",)
    inlines = [MediaItemTranslationInline, MediaItemCropInline]


@admin.register(MediaItemTranslation)
class MediaItemTranslationAdmin(BaseAdmin):
    """Admin configuration for MediaItem translations."""

    list_display = ("id", "media_item", "language", "title", "credits")
    list_filter = ("language",)
    search_fields = ("title", "credits", "media_item__original_filename")
    ordering = ("id",)
    autocomplete_fields = ("media_item", "language")


@admin.register(MediaItemCrop)
class MediaItemCropAdmin(BaseAdmin):
    """Admin configuration for MediaItem crop variants."""

    list_display = ("id", "media_item", "name", "url")
    list_filter = ("name",)
    search_fields = ("name", "media_item__original_filename")
    ordering = ("id",)
    autocomplete_fields = ("media_item",)
