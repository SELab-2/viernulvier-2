"""Admin configuration for the Genre app."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.core.admin import BaseAdmin

from .models import Genre, GenreTranslation


class GenreTranslationInline(admin.TabularInline):
    """Inline admin for managing translated genre names."""

    model = GenreTranslation
    extra = 1
    fields = ("language", "name")
    autocomplete_fields = ("language",)
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[GenreTranslation]:
        """Select related language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("language")


@admin.register(Genre)
class GenreAdmin(BaseAdmin):
    """Admin configuration for genres."""

    list_display = (
        "id",
        "type",
        "name",
    )
    list_filter = ()
    list_select_related = ()
    search_fields = (
        "type",
        "translations__name",
        "vendor_id",
    )
    ordering = ("id",)
    autocomplete_fields = ()
    inlines = [GenreTranslationInline]

    @admin.display(description="Name")
    def name(self, obj: Genre) -> str:
        """Return the display name used in the admin changelist."""
        return str(obj)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Genre]:
        """Prefetch translations to avoid N+1 queries."""
        return super().get_queryset(request).prefetch_related("translations")
