"""Admin configuration for the Locations app."""

from django.contrib import admin

from apps.core.admin import BaseAdmin
from .models import (
    Hall,
    HallTranslation,
    Location,
    LocationTranslation,
    Space,
    SpaceTranslation,
)


class LocationTranslationInline(admin.TabularInline):
    model = LocationTranslation
    extra = 1
    fields = ("language", "name")
    autocomplete_fields = ("language",)


@admin.register(Location)
class LocationAdmin(BaseAdmin):
    """Admin configuration for Location objects."""

    list_display = ("id", "city", "street", "number", "country", "is_own_location")
    list_filter = ("is_own_location",)
    search_fields = (
        "translations__name",
        "city",
        "street",
        "country",
    )
    ordering = ("id",)
    inlines = [LocationTranslationInline]

    def get_queryset(self, request):
        "Avoiding N+1 queries by prefetching related translations."
        return super().get_queryset(request).prefetch_related("translations")


@admin.register(LocationTranslation)
class LocationTranslationAdmin(BaseAdmin):
    """Admin configuration for Location translations."""

    list_display = ("id", "language", "location", "name")
    list_filter = ("language", "location")
    search_fields = ("name", "location__city", "location__street")
    ordering = ("id",)
    autocomplete_fields = ("language", "location")


class SpaceTranslationInline(admin.TabularInline):
    model = SpaceTranslation
    extra = 1
    fields = ("language", "name")
    autocomplete_fields = ("language",)


@admin.register(Space)
class SpaceAdmin(BaseAdmin):
    """Admin configuration for Space objects."""

    list_display = ("id", "location")
    list_select_related = ("location",)
    search_fields = (
        "translations__name",
        "location__city",
        "location__street"
    )
    ordering = ("id",)
    autocomplete_fields = ("location",)
    inlines = [SpaceTranslationInline]

    def get_queryset(self, request):
        "Avoiding N+1 queries by prefetching related translations."
        return super().get_queryset(request).prefetch_related("translations")


@admin.register(SpaceTranslation)
class SpaceTranslationAdmin(BaseAdmin):
    """Admin configuration for Space translations."""

    list_display = ("id", "language", "space", "name")
    list_filter = ("language", "space")
    search_fields = ("name", "space__location__city")
    ordering = ("id",)
    autocomplete_fields = ("language", "space")


class HallTranslationInline(admin.TabularInline):
    model = HallTranslation
    extra = 1
    fields = ("language", "name", "remark")
    autocomplete_fields = ("language",)


@admin.register(Hall)
class HallAdmin(BaseAdmin):
    """Admin configuration for Hall objects."""

    list_display = ("id", "space", "seat_selection", "open_seating")
    list_display_links = ("id", "space")
    list_filter = ("seat_selection", "open_seating")
    list_select_related = ("space", "space__location")
    search_fields = ("translations__name", "space__location__city", "space__location__street")
    ordering = ("id",)
    autocomplete_fields = ("space",)
    inlines = [HallTranslationInline]

    def get_queryset(self, request):
        "Avoiding N+1 queries by prefetching related translations."
        return super().get_queryset(request).prefetch_related("translations")
    

@admin.register(HallTranslation)
class HallTranslationAdmin(BaseAdmin):
    """Admin configuration for Hall translations."""

    list_display = ("id", "language", "hall", "name")
    list_filter = ("language", "hall")
    search_fields = ("name", "hall__space__location__city")
    ordering = ("id",)
    autocomplete_fields = ("language", "hall")
