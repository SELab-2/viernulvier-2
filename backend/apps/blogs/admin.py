"""Admin configuration for the Blog app."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import BaseAdmin
from apps.core.admin_widgets import enable_rich_text_for_fields

from .models import Blog, BlogTranslation


@enable_rich_text_for_fields("excerpt", "body")
class BlogTranslationInline(admin.StackedInline):
    """Inline admin for blog translations."""

    model = BlogTranslation
    extra = 1
    classes = ("collapse",)
    fields = ("language", "title", "excerpt", "body")
    autocomplete_fields = ("language",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[BlogTranslation]:
        """Select related language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("language")


@admin.register(Blog)
class BlogAdmin(BaseAdmin):
    """Admin configuration for blog posts."""

    list_display = (
        "id",
        "display_title",
        "slug",
        "published_status",
        "published_at",
        "linked_productions_count",
    )
    list_filter = ("published_at",)
    search_fields = (
        "slug",
        "translations__title",
        "translations__body",
    )
    ordering = ("-published_at", "-id")
    autocomplete_fields = ("productions",)
    inlines = [BlogTranslationInline]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("slug", "published_at", "cover_image"),
            },
        ),
        (
            "Linked Productions",
            {
                "fields": ("productions",),
                "description": "Link this blog post to one or more productions to display them together on the frontend.",
            },
        ),
    )

    @admin.display(description="Title", ordering="translations__title")
    def display_title(self, obj: Blog) -> str:
        default_translation = obj.translations.filter(language__code="en").first()
        return default_translation.title if default_translation else obj.slug

    @admin.display(description="Status", boolean=True)
    def published_status(self, obj: Blog) -> bool:
        """Show whether the post is published or a draft."""
        return obj.published_at is not None

    @admin.display(description="Linked Productions")
    def linked_productions_count(self, obj: Blog) -> str:
        """Show the number of linked productions."""
        count = obj.productions.count()
        if count == 0:
            return format_html('<span style="color: #999;">{}</span>', "None")
        return str(count)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Blog]:
        """Prefetch translations and productions to avoid N+1 queries."""
        return super().get_queryset(request).prefetch_related("translations__language", "productions")
