"""Admin configuration for the Blog app."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import BaseAdmin

from .models import Blog, BlogTranslation


class BlogTranslationInline(admin.TabularInline):
    """Inline admin for blog translations."""

    model = BlogTranslation
    extra = 1
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


@admin.register(BlogTranslation)
class BlogTranslationAdmin(BaseAdmin):
    """Admin configuration for blog translations."""

    list_display = ("id", "title", "language", "blog", "has_excerpt")
    list_filter = ("language__code",)
    search_fields = ("title", "body", "excerpt")
    ordering = ("id",)
    autocomplete_fields = ("language", "blog")

    fieldsets = (
        (
            "Translation",
            {
                "fields": ("blog", "language"),
            },
        ),
        (
            "Content",
            {
                "fields": ("title", "excerpt", "body"),
                "description": "The body supports HTML or Markdown formatting.",
            },
        ),
    )

    @admin.display(description="Has Excerpt", boolean=True)
    def has_excerpt(self, obj: BlogTranslation) -> bool:
        """Indicate whether an excerpt is provided."""
        return bool(obj.excerpt)

    def get_queryset(self, request: HttpRequest) -> QuerySet[BlogTranslation]:
        """Select related blog and language to avoid N+1 queries."""
        return super().get_queryset(request).select_related("blog", "language")
