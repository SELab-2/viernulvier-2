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
from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django import forms
from django.template.response import TemplateResponse
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.tags.models import Tag
from .admin_filters import ArtistNameFilter, GenreFilter, TagFilter
from .models import (
    Production,
    ProductionGenre,
    ProductionTag,
    ProductionTranslation,
    UitDatabaseTheme,
    UitDatabaseType,
)


class AddTagToProductionsForm(forms.Form):
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.order_by("type"),
        required=True,
        label="Tag",
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
        TagFilter,
        GenreFilter,
        ArtistNameFilter,
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

    actions = ("add_tag_to_selected_productions",)

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

    @admin.action(description="Add selected tag to selected productions")
    def add_tag_to_selected_productions(self, request, queryset):
        """Two-step admin action to attach one tag to selected productions."""

        changelist_url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist"
        )

        if "apply" in request.POST:
            form = AddTagToProductionsForm(request.POST)
            selected_ids = request.POST.getlist(ACTION_CHECKBOX_NAME)
            selected_qs = self.model.objects.filter(pk__in=selected_ids)

            if not selected_ids:
                self.message_user(request, "Geen productions geselecteerd.", level=messages.ERROR)
                return

            if form.is_valid():
                tag = form.cleaned_data["tag"]
                production_ids = list(selected_qs.values_list("id", flat=True))
                through_model = Production.tags.through

                through_model.objects.bulk_create(
                    [through_model(production_id=production_id, tag_id=tag.id) for production_id in production_ids],
                    ignore_conflicts=True,
                )

                self.message_user(
                    request,
                    f"Tag '{tag.type}' toegevoegd aan {len(production_ids)} geselecteerde productions.",
                    level=messages.SUCCESS,
                )
                return

            context = {
                **self.admin_site.each_context(request),
                "opts": self.model._meta,
                "queryset": selected_qs,
                "form": form,
                "action_checkbox_name": ACTION_CHECKBOX_NAME,
                "action_name": "add_tag_to_selected_productions",
                "title": "Add tag to selected productions",
                "changelist_url": changelist_url,
            }
            return TemplateResponse(request, "productions/add_tag_action.html", context)

        form = AddTagToProductionsForm()
        selected_qs = queryset
        if not selected_qs.exists():
            self.message_user(request, "Geen productions geselecteerd.", level=messages.ERROR)
            return

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "queryset": selected_qs,
            "form": form,
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
            "action_name": "add_tag_to_selected_productions",
            "title": "Add tag to selected productions",
            "changelist_url": changelist_url,
        }
        return TemplateResponse(request, "productions/add_tag_action.html", context)


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
        return (
            super()
            .get_queryset(request)
            .select_related("production", "language")
        )


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
        return (
            super()
            .get_queryset(request)
            .select_related("production", "genre")
        )


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
        return (
            super()
            .get_queryset(request)
            .select_related("production", "tag")
        )