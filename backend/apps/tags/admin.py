"""
Admin configuration for the Tags app.

The admin is structured around the ``Tag`` model as the primary entry point,
with an inline for translations. A standalone ``TagTranslationAdmin`` is
provided for filtering translations by language across all tags.

Queryset optimisation
---------------------
``TagAdmin`` prefetches translations to prevent N+1 queries on the list page.
``TagTranslationAdmin`` uses ``select_related`` to join the parent tag and
language in a single query.
"""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.core.admin import BaseAdmin

from .models import Tag, TagTranslation

# ===========================================================================
# Inline
# ===========================================================================


class TagTranslationInline(admin.TabularInline):
    """
    Inline for editing localised tag fields directly inside the Tag change page.

    Shows the language alongside the three translatable fields so editors
    can manage all translations from a single form.
    """

    model = TagTranslation
    extra = 1
    autocomplete_fields = ("language",)
    fields = ("language", "name", "short_description", "url_title")
    ordering = ("language__code",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("language")


# ===========================================================================
# Tag admin
# ===========================================================================


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    """
    Admin configuration for the Tag model.

    The list view surfaces the type and status flags so editors can quickly
    identify which tags are active, external, and what category they belong to.

    ``search_fields`` includes ``type`` and ``source`` to allow autocomplete
    from :class:`~apps.productions.admin.ProductionTagInline`.

    Queryset strategy
    -----------------
    ``prefetch_related("translations")`` prevents N+1 queries when the inline
    renders all language translations on the detail page.
    """

    list_display = (
        "id",
        "type",
        "source",
        "is_external",
        "is_enabled",
    )

    list_filter = (
        "is_external",
        "is_enabled",
        "type",
    )

    search_fields = (
        "type",
        "source",
        "translations__name",
    )

    ordering = ("type", "id")

    inlines = [TagTranslationInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Prefetch translations to avoid N+1 queries on the detail page."""
        return super().get_queryset(request).prefetch_related("translations")


# ===========================================================================
# Standalone translation admin
# ===========================================================================


@admin.register(TagTranslation)
class TagTranslationAdmin(BaseAdmin):
    """
    Standalone admin for TagTranslation.

    Useful for filtering translations by language across all tags, or for
    bulk-editing localised content. For editing the translations of a
    specific tag, prefer the inline on :class:`TagAdmin`.

    Queryset strategy
    -----------------
    ``select_related("tag", "language")`` prevents N+1 queries on the list
    page where both FK fields appear in ``list_display``.
    """

    list_display = (
        "id",
        "tag",
        "language",
        "name",
    )

    list_filter = ("language__code",)

    search_fields = (
        "name",
        "tag__type",
    )

    autocomplete_fields = ("tag", "language")

    ordering = ("tag", "language__code")

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related tag and language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("tag", "language")
