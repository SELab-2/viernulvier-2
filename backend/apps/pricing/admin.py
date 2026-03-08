"""Admin configuration for the Pricing app."""

from django.contrib import admin

from apps.core.admin import BaseAdmin
from .models import Price, PriceRank, PriceRankTranslation, PriceTranslation


class PriceTranslationInline(admin.TabularInline):
    """Allows editing translations directly inside the Price admin page."""

    model = PriceTranslation
    extra = 0
    fields = ("language", "description")
    autocomplete_fields = ("language",)
    ordering = ("language",)


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
    list_filter = ("type", "visibility", "membership", "cineville_box")
    search_fields = ("id", "type")
    ordering = ("sort_order", "id")
    inlines = [PriceTranslationInline]

    def get_queryset(self, request):
        """Prefetch translations to avoid N+1 queries on the list page."""
        return super().get_queryset(request).prefetch_related("translations")


@admin.register(PriceTranslation)
class PriceTranslationAdmin(BaseAdmin):
    """Admin configuration for Price translations."""

    list_display = ("id", "price", "language", "description")
    list_filter = ("language",)
    search_fields = ("price__id", "language__code", "description")
    ordering = ("price", "language")
    autocomplete_fields = ("price", "language")

    def get_queryset(self, request):
        """Select related price and language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("price", "language")


class PriceRankTranslationInline(admin.TabularInline):
    """Allows editing translations directly inside the PriceRank admin page."""

    model = PriceRankTranslation
    extra = 0
    fields = ("language", "description")
    autocomplete_fields = ("language",)
    ordering = ("language",)


@admin.register(PriceRank)
class PriceRankAdmin(BaseAdmin):
    """Admin configuration for PriceRank objects."""

    list_display = ("id", "position", "sold_out_buffer")
    search_fields = ("id", "position")
    ordering = ("position", "id")
    inlines = [PriceRankTranslationInline]


@admin.register(PriceRankTranslation)
class PriceRankTranslationAdmin(BaseAdmin):
    """Admin configuration for PriceRank translations."""

    list_display = ("id", "price_rank", "language", "description")
    list_filter = ("language",)
    search_fields = ("price_rank__id", "language__code", "description")
    ordering = ("price_rank", "language")
    autocomplete_fields = ("price_rank", "language")

    def get_queryset(self, request):
        """Select related price_rank and language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("price_rank", "language")
