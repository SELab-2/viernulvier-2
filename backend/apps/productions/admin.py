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

from django import forms
from django.contrib import admin
from django.db.models import Max, QuerySet
from django.http import HttpRequest

from apps.core.admin import BaseAdmin, TwoStepBulkActionMixin
from apps.genres.models import Genre
from apps.tags.models import Tag

from .admin_filters import ArtistNameFilter, GenreFilter, TagFilter
from .models import (
    Production,
    ProductionGenre,
    ProductionTag,
    ProductionTagTranslation,
    ProductionTranslation,
    UitDatabaseType,
)


class AddTagToProductionsForm(forms.Form):
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.order_by("type"),
        required=True,
        label="Tag",
    )


class AddGenreToProductionsForm(forms.Form):
    genre = forms.ModelChoiceField(
        queryset=Genre.objects.order_by("type"),
        required=True,
        label="Genre",
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

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("language")


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

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("genre")


class ProductionTagInline(admin.TabularInline):
    """
    Inline for managing tag assignments directly inside the Production
    change page.
    """

    model = ProductionTag
    extra = 1
    autocomplete_fields = ("tag",)
    fields = ("tag",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("tag")


class ProductionTagTranslationInline(admin.TabularInline):
    """
    Inline for editing localised descriptions directly inside the
    ProductionTag change page.

    Translations are collapsed by default to keep the page readable when
    many languages are configured.
    """

    model = ProductionTagTranslation
    extra = 1
    autocomplete_fields = ("language",)
    classes = ("collapse",)
    fields = ("language", "description")

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("language")


@admin.register(UitDatabaseType)
class UitDatabaseTypeAdmin(BaseAdmin):
    """
    Admin for UIT Database Type classifications.

    Types are imported from an external source. ``search_fields`` is required
    so this model can be used as an ``autocomplete_fields`` target on
    ``ProductionAdmin``.
    """

    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


# ===========================================================================
# Production admin
# ===========================================================================


@admin.register(Production)
class ProductionAdmin(TwoStepBulkActionMixin, BaseAdmin):
    """
    Admin configuration for the Production model.

    The list view shows structural metadata. All translatable content is
    accessible via the ``ProductionTranslationInline`` (collapsed by default).
    Genre ordering and tag assignments are managed via their respective inlines.

    Queryset strategy
    -----------------
    - ``select_related`` covers the single-row FK references displayed in
            ``list_display`` (``uit_database_type``,
      ``media_gallery``).
    - ``prefetch_related("translations")`` prevents N+1 queries when the
      admin search uses ``translations__title`` or ``translations__artist_name``.
    """

    list_display = (
        "id",
        "attendance_mode",
        "performer_type",
        "uit_database_type",
        "media_gallery",
    )

    list_filter = (
        "attendance_mode",
        "performer_type",
        TagFilter,
        GenreFilter,
        ArtistNameFilter,
    )

    list_select_related = ("uit_database_type", "media_gallery")

    search_fields = (
        "id",
        "translations__title",
        "translations__artist_name",
    )

    autocomplete_fields = (
        "uit_database_type",
        "media_gallery",
    )

    ordering = ("-id",)

    actions = (
        "add_tag_to_selected_productions",
        "add_genre_to_selected_productions",
    )

    inlines = [
        ProductionTranslationInline,
        ProductionGenreInline,
        ProductionTagInline,
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Optimise the queryset with select_related and prefetch_related."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "uit_database_type",
                "media_gallery",
            )
            .prefetch_related("translations")
        )

    two_step_empty_selection_message = "No productions selected."

    def _apply_add_tag_to_productions(self, selected_qs: QuerySet, cleaned_data: dict) -> str:
        tag = cleaned_data["tag"]
        production_ids = list(selected_qs.values_list("id", flat=True))
        through_model = Production.tags.through

        through_model.objects.bulk_create(
            [through_model(production_id=production_id, tag_id=tag.id) for production_id in production_ids],
            ignore_conflicts=True,
        )

        return f"Tag '{tag!s}' added to {len(production_ids)} selected productions."

    def _apply_add_genre_to_productions(self, selected_qs: QuerySet, cleaned_data: dict) -> str:
        genre = cleaned_data["genre"]
        production_ids = list(selected_qs.values_list("id", flat=True))

        existing_links = set(
            ProductionGenre.objects.filter(
                production_id__in=production_ids,
                genre_id=genre.id,
            ).values_list("production_id", flat=True)
        )

        max_positions = {
            row["production_id"]: row["max_position"] or 0
            for row in ProductionGenre.objects.filter(production_id__in=production_ids)
            .values("production_id")
            .annotate(max_position=Max("position"))
        }

        to_create = []
        for production_id in production_ids:
            if production_id in existing_links:
                continue

            next_position = max_positions.get(production_id, 0) + 1
            max_positions[production_id] = next_position
            to_create.append(
                ProductionGenre(
                    production_id=production_id,
                    genre_id=genre.id,
                    position=next_position,
                )
            )

        if to_create:
            ProductionGenre.objects.bulk_create(to_create, ignore_conflicts=True)

        return f"Genre '{genre!s}' added to {len(to_create)} selected productions."

    @admin.action(description="Add tag to selected productions")
    def add_tag_to_selected_productions(self, request: HttpRequest, queryset: QuerySet) -> HttpRequest:
        """Two-step admin action to attach one tag to selected productions."""

        return self._run_two_step_bulk_action(
            request,
            queryset,
            form_class=AddTagToProductionsForm,
            action_name="add_tag_to_selected_productions",
            title="Add tag to selected productions",
            apply_handler=self._apply_add_tag_to_productions,
            selected_label="Selected productions",
        )

    @admin.action(description="Add genre to selected productions")
    def add_genre_to_selected_productions(self, request: HttpRequest, queryset: QuerySet) -> HttpRequest:
        """Two-step admin action to attach one genre to selected productions."""

        return self._run_two_step_bulk_action(
            request,
            queryset,
            form_class=AddGenreToProductionsForm,
            action_name="add_genre_to_selected_productions",
            title="Add genre to selected productions",
            apply_handler=self._apply_add_genre_to_productions,
            selected_label="Selected productions",
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

    list_filter = ("language__code",)

    search_fields = (
        "title",
        "artist_name",
        "production__id",
    )

    autocomplete_fields = ("production", "language")

    ordering = ("production", "language__code")

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related production and language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("production", "language")


# ===========================================================================
# Standalone through-table admins
# ===========================================================================


@admin.register(ProductionGenre)
class ProductionGenreAdmin(BaseAdmin):
    """
    Standalone admin for the ProductionGenre through-table.

    Allows direct inspection and editing of genre-production links and
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

    search_fields = (
        "production__id",
        "genre__translations__name",
    )

    autocomplete_fields = ("production", "genre")

    ordering = ("production", "position")

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related production and genre to avoid N+1 queries."""
        return super().get_queryset(request).select_related("production", "genre")


@admin.register(ProductionTag)
class ProductionTagAdmin(BaseAdmin):
    """
    Standalone admin for the ProductionTag through-table.

    Allows direct inspection and editing of tag-production links without
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
        "tag__translations__name",
    )

    autocomplete_fields = ("production", "tag")

    ordering = ("production", "tag__type")

    inlines = [ProductionTagTranslationInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related production and tag to avoid N+1 queries."""
        return super().get_queryset(request).select_related("production", "tag")
