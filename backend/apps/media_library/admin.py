from django.contrib import admin
from apps.core.admin import BaseAdmin
from .models import (
    MediaGallery,
    MediaItem,
    MediaItemTranslation,
    MediaItemCrop,
)


class MediaItemTranslationInline(admin.TabularInline):
    """
    Allows editing translations directly
    inside the MediaItem admin page.
    """

    model = MediaItemTranslation
    extra = 1
    autocomplete_fields = ("language",)
    classes = ("collapse",)


class MediaItemCropInline(admin.TabularInline):
    """
    Allows managing crops directly
    within the MediaItem admin page.
    """

    model = MediaItemCrop
    extra = 1


class MediaItemInline(admin.TabularInline):
    """
    Allows managing media items directly
    within the MediaGallery admin page.
    """

    model = MediaItem
    extra = 1
    classes = ("collapse",)
    show_change_link = True


@admin.register(MediaGallery)
class MediaGalleryAdmin(BaseAdmin):
    """
    Admin configuration for MediaGallery.

    Displays gallery name in list view.
    Allows searching by name.
    """

    list_display = (
        "id",
        "name",
    )

    search_fields = (
        "name",
    )

    inlines = [
        MediaItemInline,
    ]


@admin.register(MediaItem)
class MediaItemAdmin(BaseAdmin):
    """
    Admin configuration for MediaItem.

    Displays type, format, original filename,
    position, width and height in list view.

    Optimized queryset with select_related
    to prevent N+1 queries.
    """

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

    list_filter = (
        "type",
        "format",
        "gallery",
    )

    search_fields = (
        "original_filename",
        "gallery__name",
    )

    autocomplete_fields = (
        "gallery",
    )

    inlines = [
        MediaItemTranslationInline,
        MediaItemCropInline,
    ]

    def get_queryset(self, request):
        """
        Optimize queryset by selecting related
        foreign keys to avoid extra queries.
        """
        return super().get_queryset(request).select_related(
            "gallery",
        )


@admin.register(MediaItemTranslation)
class MediaItemTranslationAdmin(BaseAdmin):
    """
    Standalone admin for MediaItemTranslation.

    Useful for filtering translations by language.
    """

    list_display = (
        "id",
        "media_item",
        "language",
        "title",
        "credits",
    )

    list_filter = (
        "language",
    )

    search_fields = (
        "title",
        "credits",
        "media_item__original_filename",
    )

    autocomplete_fields = (
        "media_item",
        "language",
    )


@admin.register(MediaItemCrop)
class MediaItemCropAdmin(BaseAdmin):
    """
    Standalone admin for MediaItemCrop.

    Useful for managing named crops per media item.
    """

    list_display = (
        "id",
        "media_item",
        "name",
        "url",
    )

    search_fields = (
        "name",
        "media_item__original_filename",
    )

    autocomplete_fields = (
        "media_item",
    )