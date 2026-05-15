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
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from apps.core.admin import BaseAdmin, TwoStepBulkActionMixin
from apps.core.admin_widgets import enable_rich_text_for_fields
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
    """Confirmation form for selecting the tag to add to selected productions."""

    tag = forms.ModelChoiceField(
        queryset=Tag.objects.order_by("type"),
        required=True,
        label="Tag",
    )


class AddGenreToProductionsForm(forms.Form):
    """Confirmation form for selecting the genre to add to selected productions."""

    genre = forms.ModelChoiceField(
        queryset=Genre.objects.order_by("type"),
        required=True,
        label="Genre",
    )


# ===========================================================================
# Inlines
# ===========================================================================


class ProductionTranslationForm(forms.ModelForm):
    """
    Custom form to adjust the layout of fields in ProductionTranslationInline.
    """

    class Meta:
        model = ProductionTranslation
        fields = ["artist_name", "tagline"]
        widgets = {
            "artist_name": forms.TextInput(attrs={"rows": 1, "style": "width: 256px;"}),
            "tagline": forms.TextInput(attrs={"rows": 1, "style": "width: 256px;"}),
        }


@enable_rich_text_for_fields(
    "teaser",
    "description",
    widget_attrs={"data-richtext-headings": "h1,h2,h3,h4"},
)
class ProductionTranslationInline(admin.StackedInline):
    """
    Inline for editing localised text fields directly inside the
    Production change page.

    Translations are collapsed by default to keep the page readable when
    many languages are configured.
    """

    model = ProductionTranslation
    form = ProductionTranslationForm
    extra = 1
    autocomplete_fields = ("language",)
    classes = ("collapse",)
    fields = (
        "language",
        "title",
        "artist_name",
        "tagline",
        "teaser",
        "description",
        "video_1",
        "video_2",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related language to avoid N+1 queries in the translation inline."""
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
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related genre to avoid N+1 queries in the genre inline."""
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
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related tag to avoid N+1 queries in the tag inline."""
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
        """Select related language to avoid N+1 queries in the translation inline."""
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
        "display_title",
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

    readonly_fields = ("media_items_admin",)
    two_step_empty_selection_message = "No productions selected."

    @admin.display(description="Title")
    def display_title(self, obj: Production) -> str:
        """Return the best available title for changelist display."""
        title = obj.get_base_display_name(
            related_name="translations",
            name_field="title",
            fallback=None,
        )
        return title or f"Production #{obj.id}"

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

    def _selected_productions_from_request(self, request: HttpRequest, fallback_qs: QuerySet) -> QuerySet:
        """Resolve selected productions from POST ids, independent of current changelist filters."""
        selected_ids = request.POST.getlist("_selected_action")
        if not selected_ids:
            return fallback_qs
        return self.model.objects.filter(pk__in=selected_ids)

    def _apply_add_tag_to_productions(self, selected_qs: QuerySet, cleaned_data: dict) -> str:
        """Attach the selected tag to all selected productions using bulk_create.

        Existing production-tag links are ignored so the action can be safely
        repeated without raising duplicate constraint errors.
        """
        tag = cleaned_data["tag"]
        production_ids = list(selected_qs.values_list("id", flat=True))
        through_model = Production.tags.through

        through_model.objects.bulk_create(
            [through_model(production_id=production_id, tag_id=tag.id) for production_id in production_ids],
            ignore_conflicts=True,
        )

        return f"Tag '{tag!s}' added to {len(production_ids)} selected productions."

    def _apply_add_genre_to_productions(self, selected_qs: QuerySet, cleaned_data: dict) -> str:
        """Attach the selected genre to selected productions at the next position.

        Existing production-genre links are skipped. For new links, the next
        position is calculated per production so genre ordering remains stable.
        """
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

    @admin.display(description="Media items")
    def media_items_admin(self, obj: Production) -> str:
        """Render a small admin widget linking to media items and add action.

        Shows the list of media items attached to the production's gallery
        (if any) with links to edit each item and a button to add a new
        MediaItem prefilled with the gallery via GET params.
        """
        if not obj or not obj.media_gallery:
            return "-"

        gallery = obj.media_gallery
        items = gallery.media_items.all()
        if not items:
            add_url = reverse("admin:media_library_mediaitem_add") + f"?gallery={gallery.id}"
            return format_html(
                '<div>No images in gallery.</div><div style="margin-top:0.5em"><a class="button" href="{}">Add image</a></div>',
                add_url,
            )

        rows = format_html_join(
            "\n",
            '<div><a href="{}">{}</a></div>',
            (
                (reverse("admin:media_library_mediaitem_change", args=(i.id,)), i.original_filename or str(i.id))
                for i in items
            ),
        )

        add_url = reverse("admin:media_library_mediaitem_add") + f"?gallery={gallery.id}"
        return format_html(
            '{}<div style="margin-top:0.5em"><a class="button" href="{}">Add image to gallery</a></div>', rows, add_url
        )

    @admin.action(description="Add tag to selected productions")
    def add_tag_to_selected_productions(self, request: HttpRequest, queryset: QuerySet) -> HttpRequest:
        """Two-step admin action to attach one tag to selected productions."""

        selected_qs = self._selected_productions_from_request(request, queryset)

        return self._run_two_step_bulk_action(
            request,
            selected_qs,
            form_class=AddTagToProductionsForm,
            action_name="add_tag_to_selected_productions",
            title="Add tag to selected productions",
            apply_handler=self._apply_add_tag_to_productions,
            selected_label="Selected productions",
        )

    @admin.action(description="Add genre to selected productions")
    def add_genre_to_selected_productions(self, request: HttpRequest, queryset: QuerySet) -> HttpRequest:
        """Two-step admin action to attach one genre to selected productions."""

        selected_qs = self._selected_productions_from_request(request, queryset)

        return self._run_two_step_bulk_action(
            request,
            selected_qs,
            form_class=AddGenreToProductionsForm,
            action_name="add_genre_to_selected_productions",
            title="Add genre to selected productions",
            apply_handler=self._apply_add_genre_to_productions,
            selected_label="Selected productions",
        )
