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

from django import forms
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.core.admin import BaseAdmin

from apps.productions.models import ProductionTag

from .models import Tag, TagTranslation


class TagAdminForm(forms.ModelForm):
    """Admin form that restricts tag image uploads to supported image types."""

    class Meta:
        model = Tag
        fields = [
            "external_id",
            "url",
            "source",
            "is_enabled",
            "type",
            "image",
        ]
        widgets = {
            "image": forms.FileInput(
                attrs={
                    "accept": ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp",
                },
            ),
        }


class TagTranslationInline(admin.StackedInline):
    """
    Inline for editing localised tag fields directly inside the Tag change page.
    """

    model = TagTranslation
    extra = 1
    autocomplete_fields = ("language",)
    fields = ("language", "name", "excerpt", "short_description", "url_title")
    ordering = ("language__code",)
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("language")


class TagProductionInline(admin.TabularInline):
    """Inline for attaching productions directly on a Tag change page."""

    verbose_name = "Production"
    verbose_name_plural = "Add Productions to this Tag"
    model = ProductionTag
    extra = 1
    autocomplete_fields = ("production",)
    fields = ("production",)
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("production")


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

    form = TagAdminForm

    list_display = (
        "id",
        "display_name",
        "type",
        "source",
        "is_enabled",
    )

    list_filter = (
        "is_enabled",
        "type",
    )

    search_fields = (
        "type",
        "source",
        "translations__name",
    )

    ordering = ("type", "id")

    inlines = [TagTranslationInline, TagProductionInline]

    @admin.display(description="Display name")
    def display_name(self, obj: Tag) -> str:
        """Return the display name shown in admin lists."""
        return str(obj)

    class Media:
        js = ("admin/js/media_file_upload.js",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Prefetch translations to avoid N+1 queries on the detail page."""
        return super().get_queryset(request).prefetch_related("translations")
