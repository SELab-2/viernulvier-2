"""Admin configuration for the Pricing app."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.core.admin import BaseAdmin

from .models import Price, PriceRank, PriceRankTranslation, PriceTranslation


class PriceTranslationInline(admin.TabularInline):
    """Allows editing translations directly inside the Price admin page."""

    model = PriceTranslation
    extra = 0
    fields = ("language", "description")
    autocomplete_fields = ("language",)
    ordering = ("language",)
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related language to avoid N+1 queries in the inline."""
        return super().get_queryset(request).select_related("language")


@admin.register(Price)
class PriceAdmin(BaseAdmin):
    """Admin configuration for Price objects."""

    list_display = (
        "id",
        "type",
        "visibility",
        "membership",
        "minimum",
        "maximum",
        "step",
        "sort_order",
        "cineville_box",
    )
    list_filter = ("type", "visibility", "cineville_box")
    search_fields = ("id", "type")
    ordering = ("sort_order", "id")
    inlines = [PriceTranslationInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Prefetch translations to avoid N+1 queries on the detail page."""
        return super().get_queryset(request).prefetch_related("translations")


class PriceRankTranslationInline(admin.TabularInline):
    """Allows editing translations directly inside the PriceRank admin page."""

    model = PriceRankTranslation
    extra = 0
    fields = ("language", "description")
    autocomplete_fields = ("language",)
    ordering = ("language",)
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("language")


@admin.register(PriceRank)
class PriceRankAdmin(BaseAdmin):
    """Admin configuration for PriceRank objects."""

    list_display = ("id", "position", "sold_out_buffer")
    search_fields = ("id", "position")
    ordering = ("position", "id")
    inlines = [PriceRankTranslationInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Prefetch translations to avoid N+1 queries on the detail page."""
        return super().get_queryset(request).prefetch_related("translations")
