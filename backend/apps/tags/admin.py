from django.contrib import admin
from apps.core.admin import BaseAdmin
from .models import Tag, TagTranslation


class TagTranslationInline(admin.TabularInline):
    """
    Allows editing translations directly
    inside the Tag admin page.
    """

    model = TagTranslation
    extra = 1
    autocomplete_fields = ("language",)


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    """
    Admin configuration for Tag model.
    """

    list_display = (
        "id",
        "type",
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
    )

    inlines = [TagTranslationInline]


@admin.register(TagTranslation)
class TagTranslationAdmin(BaseAdmin):
    """
    Standalone admin for TagTranslation.

    Useful for filtering by language.
    """

    list_display = (
        "id",
        "tag",
        "language",
        "name",
    )

    list_filter = ("language",)
    search_fields = ("name", "tag__type")
    autocomplete_fields = ("tag", "language")