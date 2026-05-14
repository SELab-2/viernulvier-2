"""Admin configuration for the Locations app."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

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
    """Inline admin for managing translated location names."""
    model = LocationTranslation
    extra = 1
    fields = ("language", "name")
    autocomplete_fields = ("language",)
    classes = ("collapse",)


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

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Prefetch translations to avoid N+1 queries in the admin."""
        return super().get_queryset(request).prefetch_related("translations")


class SpaceTranslationInline(admin.TabularInline):
    """Inline admin for managing translated space names."""
    model = SpaceTranslation
    extra = 1
    fields = ("language", "name")
    autocomplete_fields = ("language",)
    classes = ("collapse",)


@admin.register(Space)
class SpaceAdmin(BaseAdmin):
    """Admin configuration for Space objects."""

    list_display = ("id", "location")
    list_select_related = ("location",)
    search_fields = ("translations__name", "location__city", "location__street")
    ordering = ("id",)
    autocomplete_fields = ("location",)
    inlines = [SpaceTranslationInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Prefetch translations to avoid N+1 queries in the admin."""
        return super().get_queryset(request).prefetch_related("translations")


class HallTranslationInline(admin.TabularInline):
    """Inline admin for managing translated hall names and remarks."""
    model = HallTranslation
    extra = 1
    fields = ("language", "name", "remark")
    autocomplete_fields = ("language",)
    classes = ("collapse",)


@admin.register(Hall)
class HallAdmin(BaseAdmin):
    """Admin configuration for Hall objects."""

    list_display = ("id", "space", "seat_selection", "open_seating")
    list_display_links = ("id", "space")
    list_filter = ("seat_selection", "open_seating")
    list_select_related = ("space", "space__location")
    search_fields = (
        "translations__name",
        "space__location__city",
        "space__location__street",
    )
    ordering = ("id",)
    autocomplete_fields = ("space",)
    inlines = [HallTranslationInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Prefetch translations to avoid N+1 queries in the admin."""
        return super().get_queryset(request).prefetch_related("translations")
