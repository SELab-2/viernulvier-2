from django.contrib import admin

from apps.core.admin import BaseAdmin
from apps.pricing.models import Price, PriceTranslation, PriceRank, PriceRankTranslation


class PriceTranslationInline(admin.TabularInline):
    model = PriceTranslation
    extra = 0
    autocomplete_fields = ["language"]
    fields = ("language", "description")
    ordering = ("language",)


class PriceRankTranslationInline(admin.TabularInline):
    model = PriceRankTranslation
    extra = 0
    autocomplete_fields = ["language"]
    fields = ("language", "description")
    ordering = ("language",)


@admin.register(Price)
class PriceAdmin(BaseAdmin):
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
    search_fields = ("id",)  # ✅ required for autocomplete on FK to Price
    ordering = ("sort_order",)
    inlines = [PriceTranslationInline]


@admin.register(PriceRank)
class PriceRankAdmin(BaseAdmin):
    list_display = ("id", "position", "sold_out_buffer")
    search_fields = ("id", "position")  # ✅ required for autocomplete on FK to PriceRank
    ordering = ("position",)
    inlines = [PriceRankTranslationInline]


@admin.register(PriceTranslation)
class PriceTranslationAdmin(BaseAdmin):
    list_display = ("id", "price", "language", "description")
    list_filter = ("language",)  # ✅ tuple
    search_fields = ("price__id", "language__code", "description")
    autocomplete_fields = ["price", "language"]
    ordering = ("price", "language")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("price", "language")


@admin.register(PriceRankTranslation)
class PriceRankTranslationAdmin(BaseAdmin):
    list_display = ("id", "price_rank", "language", "description")
    list_filter = ("language",)  # ✅ tuple
    search_fields = ("price_rank__id", "language__code", "description")
    autocomplete_fields = ["price_rank", "language"]
    ordering = ("price_rank", "language")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("price_rank", "language")