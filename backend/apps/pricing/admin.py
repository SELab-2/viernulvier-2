from django.contrib import admin
from apps.core.admin import BaseAdmin
from apps.pricing.models import (
    Price,
    PriceTranslation,
    PriceRank,
    PriceRankTranslation
)

# Inlines

class PriceTranslationInline(admin.TabularInline):
    """To display an instance of the PriceTranslation model as a table on an admin page."""
    model = PriceTranslation
    extra = 0
    autocomplete_fields = ["language"]
    fields = ("language", "description")
    ordering = ("language",)


class PriceRankTranslationInline(admin.TabularInline):
    """To display an instance of the PriceRankTranslation model as a table on an admin page."""
    model = PriceRankTranslation
    extra = 0
    autocomplete_fields = ["language"]
    fields = ("language", "description")
    ordering = ("language",)


# PriceAdmin

@admin.register(Price)
class PriceAdmin(BaseAdmin):
    """Admin for Price model."""
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
    ordering = ("sort_order",)
    inlines = [PriceTranslationInline]


# PriceRankAdmin

@admin.register(PriceRank)
class PriceRankAdmin(BaseAdmin):
    """Admin for PriceRank model."""
    list_display = ("id")
    ordering = ("id",)
    inlines = [PriceRankTranslationInline]

# PriceTranslation

@admin.register(PriceTranslation)
class PriceTranslationAdmin(BaseAdmin):
    """Admin for PriceTranslation model."""
    list_display = ("id", "price", "language", "description")
    list_filter = ("language")
    search_fields = ("price__id", "language__code", "description")
    autocomplete_fields = ["price", "language"]
    ordering = ("price", "language")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("price", "language")

# PriceRankTranslation

@admin.register(PriceRankTranslation)
class PriceRankTranslationAdmin(BaseAdmin):
    """Admin for PriceRankTranslation model."""
    list_display = ("id", "price_rank", "language", "description")
    list_filter = ("language",)
    search_fields = ("price_rank__id", "language__code", "description")
    autocomplete_fields = ["price_rank", "language"]
    ordering = ("price_rank", "language")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("price_rank", "language")