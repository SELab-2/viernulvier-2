from django.contrib import admin
from apps.core.admin import BaseAdmin
from .models import (
    Production,
    ProductionTranslation,
    UitDatabaseTheme,
    UitDatabaseType,
    ProductionGenre,
    ProductionTag,
)


class ProductionTranslationInline(admin.TabularInline):
    """
    Allows editing translations directly
    inside the Production admin page.
    """

    model = ProductionTranslation
    extra = 1
    autocomplete_fields = ("language",)
    classes = ("collapse",)


class ProductionGenreInline(admin.TabularInline):
    """
    Allows managing genres directly
    within the Production admin page.
    """

    model = ProductionGenre
    extra = 1
    # autocomplete_fields = ("genre",) TODO if model implemented, add this


class ProductionTagInline(admin.TabularInline):
    """
    Allows managing tags directly
    within the Production admin page.
    """

    model = ProductionTag
    extra = 1
    autocomplete_fields = ("tag",)


@admin.register(UitDatabaseTheme)
class UitDatabaseThemeAdmin(BaseAdmin):
    """
    Admin configuration for UIT Database Theme.
    """

    list_display = (
        "id",
        "name",
    )

    search_fields = (
        "name",
    )


@admin.register(UitDatabaseType)
class UitDatabaseTypeAdmin(BaseAdmin):
    """
    Admin configuration for UIT Database Type.
    """

    list_display = (
        "id",
        "name",
    )

    search_fields = (
        "name",
    )


@admin.register(Production)
class ProductionAdmin(BaseAdmin):
    """
    Admin configuration for Production model.

    Displays attendance mode, performer type,
    UIT theme and UIT type in the list view.

    Optimized queryset with select_related
    to prevent N+1 queries.
    """

    list_display = (
        "id",
        "attendance_mode",
        "performer_type",
        "uit_database_theme",
        "uit_database_type",
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
        #"media_gallery", TODO if model implemented, add this
    )

    inlines = [
        ProductionTranslationInline,
        ProductionGenreInline,
        ProductionTagInline,
    ]

    def get_queryset(self, request):
        """
        Optimize queryset by selecting related
        foreign keys to avoid extra queries.
        """
        return super().get_queryset(request).select_related(
            "uit_database_theme",
            "uit_database_type",
        ).prefetch_related("translations")


@admin.register(ProductionTranslation)
class ProductionTranslationAdmin(BaseAdmin):
    """
    Standalone admin for ProductionTranslation.

    Useful for filtering by language.
    """

    list_display = (
        "id",
        "production",
        "language",
        "title",
        "artist_name",
    )

    list_filter = (
        "language",
    )

    search_fields = (
        "title",
        "artist_name",
        "production__id",
    )

    autocomplete_fields = (
        "production",
        "language",
    )


@admin.register(ProductionGenre)
class ProductionGenreAdmin(BaseAdmin):
    """
    Standalone admin for ProductionGenre.
    """

    list_display = (
        "id",
        "production",
        "genre",
        "position",
    )

    autocomplete_fields = (
        "production",
        # "genre", TODO if model implemented, add this
    )


@admin.register(ProductionTag)
class ProductionTagAdmin(BaseAdmin):
    """
    Standalone admin for ProductionTag.
    """

    list_display = (
        "id",
        "production",
        "tag",
    )

    autocomplete_fields = (
        "production",
        "tag",
    )