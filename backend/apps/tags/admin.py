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
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from apps.core.admin import BaseAdmin

from .models import Tag, TagTranslation

# ===========================================================================
# Inline
# ===========================================================================


class TagTranslationInline(admin.StackedInline):
    """
    Inline for editing localised tag fields directly inside the Tag change page.

    Shows the language alongside the translatable fields in a vertical layout
    so editors can manage all translations from a single form with better readability.
    """

    model = TagTranslation
    extra = 1
    autocomplete_fields = ("language",)
    fields = ("language", "name", "excerpt", "short_description", "url_title")
    ordering = ("language__code",)
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("language")


# ===========================================================================
# Tag admin
# ===========================================================================


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    """
    Admin configuration for the Tag model.

    The list view surfaces the type and status flag so editors can quickly
    identify which tags are active and what category they belong to.

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
        "is_enabled",
        "media_gallery",
    )

    list_filter = (
        "is_enabled",
        "type",
    )

    fields = (
        "id",
        "external_id",
        "url",
        "source",
        "is_enabled",
        "type",
        "media_gallery",
        "media_items_admin",
    )

    search_fields = (
        "type",
        "source",
        "translations__name",
    )

    autocomplete_fields = ("media_gallery",)

    readonly_fields = (
        "id",
        "media_items_admin",
    )

    ordering = ("type", "id")

    inlines = [TagTranslationInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Prefetch translations and media gallery data to avoid N+1 queries."""
        return (
            super()
            .get_queryset(request)
            .select_related("media_gallery")
            .prefetch_related(
                "translations",
                "media_gallery__media_items",
            )
        )

    @admin.display(description="Media items")
    def media_items_admin(self, obj: Tag) -> str:
        """Render linked media items and an add button for the tag gallery."""
        if not obj or not obj.media_gallery:
            return "-"

        gallery = obj.media_gallery
        items = gallery.media_items.all()

        if not items:
            add_url = reverse("admin:media_library_mediaitem_add") + f"?gallery={gallery.id}"
            return format_html(
                "<div>No images in gallery.</div>"
                '<div style="margin-top:0.5em">'
                '<a class="button" href="{}">Add image</a>'
                "</div>",
                add_url,
            )

        rows = format_html_join(
            "\n",
            '<div><a href="{}">{}</a></div>',
            (
                (
                    reverse("admin:media_library_mediaitem_change", args=(item.id,)),
                    item.original_filename or str(item.id),
                )
                for item in items
            ),
        )

        add_url = reverse("admin:media_library_mediaitem_add") + f"?gallery={gallery.id}"
        return format_html(
            '{}<div style="margin-top:0.5em"><a class="button" href="{}">Add image to gallery</a></div>',
            rows,
            add_url,
        )
