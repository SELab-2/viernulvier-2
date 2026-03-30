"""Admin configuration for the Genre app."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.core.admin import BaseAdmin

from .models import Genre, GenreTranslation, GenreUseAs


class GenreTranslationInline(admin.TabularInline):
    model = GenreTranslation
    extra = 1
    fields = ("language", "name")
    autocomplete_fields = ("language",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[GenreTranslation]:
        return super().get_queryset(request).select_related("language")


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
    list_select_related = ("use_as",)
    search_fields = (
        "type",
        "translations__name",
        "vendor_id",
    )
    ordering = ("id",)
    autocomplete_fields = ("use_as",)
    inlines = [GenreTranslationInline]

    @admin.display(description="Name")
    def name(self, obj: Genre) -> str:
        return str(obj)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Genre]:
        """Select related use_as and prefetch translations to avoid N+1 queries."""
        return super().get_queryset(request).select_related("use_as").prefetch_related("translations")


@admin.register(GenreTranslation)
class GenreTranslationAdmin(BaseAdmin):
    """Admin configuration for genre translations."""

    list_display = ("id", "name", "language", "genre")
    list_filter = ("language__code",)
    search_fields = ("name",)
    ordering = ("id",)
    autocomplete_fields = ("language", "genre")

    def get_queryset(self, request: HttpRequest) -> QuerySet[GenreTranslation]:
        """Select related genre and language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("genre", "language")
