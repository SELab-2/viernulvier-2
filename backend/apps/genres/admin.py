"""Admin configuration for the Genre app."""

from django.contrib import admin

from apps.core.admin import BaseAdmin
from .models import Genre, GenreTranslation, GenreUseAs


class GenreTranslationInline(admin.TabularInline):
    model = GenreTranslation
    extra = 1
    fields = ("language", "name")
    autocomplete_fields = ("language",)


@admin.register(GenreUseAs)
class GenreUseAsAdmin(BaseAdmin):
    """Admin configuration for genre usage contexts."""

    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Genre)
class GenreAdmin(BaseAdmin):
    """Admin configuration for genres."""

    list_display = (
        "id",
        "type",
        "use_as",
        "name",
    )
    list_filter = ("use_as",)
    search_fields = (
        "type",
        "translations__name",
        "vendor_id",
    )
    ordering = ("id",)
    autocomplete_fields = ("use_as",)
    inlines = [GenreTranslationInline]

    @admin.display(description="Name")
    def name(self, obj):
        return str(obj)

    def get_queryset(self, request):
        """Prefetch translations to avoid N+1 queries on the detail page."""
        return super().get_queryset(request).prefetch_related("translations")


@admin.register(GenreTranslation)
class GenreTranslationAdmin(BaseAdmin):
    """Admin configuration for genre translations."""

    list_display = ("id", "name", "language", "genre")
    list_filter = ("language", "genre")
    search_fields = ("name",)
    ordering = ("id",)
    autocomplete_fields = ("language", "genre")
