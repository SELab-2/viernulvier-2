"""
Admin configuration for the Productions app.

Productions are the core catalogue entity. The admin is structured around
the ``Production`` model as the primary entry point, with inlines for
translations, genres, and tags. Standalone admins are provided for each
related model to allow direct access and filtering.

Queryset optimisation
---------------------
Every admin class that renders related data overrides ``get_queryset`` to
add the necessary ``select_related`` and ``prefetch_related`` calls, keeping
the list and detail pages free of N+1 queries.
"""

from django.contrib import admin

from apps.core.admin import BaseAdmin

from .models import (
    Production,
    ProductionGenre,
    ProductionTag,
    ProductionTranslation,
    UitDatabaseTheme,
    UitDatabaseType,
)

# ===========================================================================
# Inlines
# ===========================================================================


class ProductionTranslationInline(admin.TabularInline):
    """
    Inline for editing localised text fields directly inside the
    Production change page.

    Translations are collapsed by default to keep the page readable when
    many languages are configured.
    """

    model = ProductionTranslation
    extra = 1
    autocomplete_fields = ("language",)
    classes = ("collapse",)
    fields = (
        "language",
        "title",
        "artist_name",
        "tagline",
        "teaser",
    )


class ProductionGenreInline(admin.TabularInline):
    """
    Inline for managing genre assignments and their display order directly
    inside the Production change page.

    The ``position`` field must be set explicitly to control the order in
    which genres appear on the frontend.
    """

    model = ProductionGenre
    extra = 1
    autocomplete_fields = ("genre",)
    fields = ("genre", "position")
    ordering = ("position",)


class ProductionTagInline(admin.TabularInline):
    """
    Inline for managing tag assignments directly inside the Production
    change page.
    """

    model = ProductionTag
    extra = 1
    autocomplete_fields = ("tag",)
    fields = ("tag",)


# ===========================================================================
# UIT Database classification admins
# ===========================================================================


@admin.register(UitDatabaseTheme)
class UitDatabaseThemeAdmin(BaseAdmin):
    """
    Admin for UIT Database Theme classifications.

    Themes are typically imported from an external source and assigned
    to productions. ``search_fields`` is required so this model can be
    used as an ``autocomplete_fields`` target on ``ProductionAdmin``.
    """

    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(UitDatabaseType)
class UitDatabaseTypeAdmin(BaseAdmin):
    """
    Admin for UIT Database Type classifications.

    Types provide a more granular classification than themes. Like
    ``UitDatabaseThemeAdmin``, ``search_fields`` is required so this model
    can be used as an ``autocomplete_fields`` target on ``ProductionAdmin``.
    """

    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


# ===========================================================================
# Production admin
# ===========================================================================


@admin.register(Production)
class ProductionAdmin(BaseAdmin):
    """
    Admin configuration for the Production model.

    The list view shows structural metadata. All translatable content is
    accessible via the ``ProductionTranslationInline`` (collapsed by default).
    Genre ordering and tag assignments are managed via their respective inlines.

    Queryset strategy
    -----------------
    - ``select_related`` covers the single-row FK references displayed in
      ``list_display`` (``uit_database_theme``, ``uit_database_type``,
      ``media_gallery``).
    - ``prefetch_related("translations")`` prevents N+1 queries when the
      admin search uses ``translations__title`` or ``translations__artist_name``.
    """

    list_display = (
        "id",
        "attendance_mode",
        "performer_type",
        "uit_database_theme",
        "uit_database_type",
        "media_gallery",
    )

    list_filter = (
        "attendance_mode",
        "performer_type",
        "uit_database_theme",
        "uit_database_type",
    )

    search_fields = (
        "id",
        "translations__title",
        "translations__artist_name",
    )

    autocomplete_fields = (
        "uit_database_theme",
        "uit_database_type",
        "media_gallery",
    )

    ordering = ("-id",)

    inlines = [
        ProductionTranslationInline,
        ProductionGenreInline,
        ProductionTagInline,
    ]

    def get_queryset(self, request):
        """Optimise the queryset with select_related and prefetch_related."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "uit_database_theme",
                "uit_database_type",
                "media_gallery",
            )
            .prefetch_related("translations")
        )


# ===========================================================================
# Standalone translation admin
# ===========================================================================


@admin.register(ProductionTranslation)
class ProductionTranslationAdmin(BaseAdmin):
    """
    Standalone admin for ProductionTranslation.

    Useful for bulk-editing translations or filtering by language across all
    productions. For editing the translation of a specific production, prefer
    the inline on :class:`ProductionAdmin`.

    Queryset strategy
    -----------------
    ``select_related("production", "language")`` prevents N+1 queries on the
    list page where both FK fields appear in ``list_display``.
    """

    list_display = (
        "id",
        "production",
        "language",
        "title",
        "artist_name",
    )

    list_filter = ("language",)

    search_fields = (
        "title",
        "artist_name",
        "production__id",
    )

    autocomplete_fields = ("production", "language")

    ordering = ("production", "language__code")

    def get_queryset(self, request):
        """Select related production and language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("production", "language")


# ===========================================================================
# Standalone through-table admins
# ===========================================================================


@admin.register(ProductionGenre)
class ProductionGenreAdmin(BaseAdmin):
    """
    Standalone admin for the ProductionGenre through-table.

    Allows direct inspection and editing of genre–production links and
    their ``position`` values without going through the production change
    page. For most use cases, prefer the inline on :class:`ProductionAdmin`.

    Queryset strategy
    -----------------
    ``select_related("production", "genre")`` prevents N+1 queries on the
    list page.
    """

    list_display = (
        "id",
        "production",
        "genre",
        "position",
    )

    list_filter = ("genre",)

    search_fields = (
        "production__id",
        "genre__type",
    )

    autocomplete_fields = ("production", "genre")

    ordering = ("production", "position")

    def get_queryset(self, request):
        """Select related production and genre to avoid N+1 queries."""
        return super().get_queryset(request).select_related("production", "genre")


@admin.register(ProductionTag)
class ProductionTagAdmin(BaseAdmin):
    """
    Standalone admin for the ProductionTag through-table.

    Allows direct inspection and editing of tag–production links without
    going through the production change page. For most use cases, prefer
    the inline on :class:`ProductionAdmin`.

    Queryset strategy
    -----------------
    ``select_related("production", "tag")`` prevents N+1 queries on the
    list page.
    """

    list_display = (
        "id",
        "production",
        "tag",
    )

    list_filter = ("tag__type",)

    search_fields = (
        "production__id",
        "tag__type",
    )

    autocomplete_fields = ("production", "tag")

    ordering = ("production", "tag__type")

    def get_queryset(self, request):
        """Select related production and tag to avoid N+1 queries."""
        return super().get_queryset(request).select_related("production", "tag")
