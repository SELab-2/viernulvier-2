"""Admin configuration for the Blog app."""

from django import forms
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import BaseAdmin

from .models import Blog, BlogTranslation


class BlogAdminForm(forms.ModelForm):
    """Admin form that restricts blog cover uploads to supported image types."""

    class Meta:
        model = Blog
        fields = [
            "slug",
            "published_at",
            "cover_image",
            "productions",
        ]
        widgets = {
            "cover_image": forms.FileInput(
                attrs={
                    "accept": ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp",
                },
            ),
        }


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


class BlogProductionInline(admin.TabularInline):
    """Inline for attaching productions directly on a Blog change page."""

    model = Blog.productions.through
    verbose_name = "Production"
    verbose_name_plural = "Linked Productions"
    extra = 1
    autocomplete_fields = ("production",)
    fields = ("production",)
    classes = ("collapse",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Select related productions to avoid N+1 queries."""
        return super().get_queryset(request).select_related("production")


@admin.register(Blog)
class BlogAdmin(BaseAdmin):
    """Admin configuration for blog posts."""

    form = BlogAdminForm

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

    inlines = [BlogTranslationInline, BlogProductionInline]
    autocomplete_fields = ("productions",)

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("slug", "published_at", "cover_image"),
            },
        ),
    )

    class Media:
        js = ("admin/js/media_file_upload.js",)

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
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "translations__language",
                "productions",
            )
        )
