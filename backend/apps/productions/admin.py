from django.contrib import admin
from apps.core.admin import BaseAdmin
from .models import (
    Production, 
    ProductionTranslation, 
    UitDatabaseTheme, 
    UitDatabaseType,
    ProductionGenre,
    ProductionTag
)

class ProductionTranslationInline(admin.TabularInline):
    model = ProductionTranslation
    extra = 1
    autocomplete_fields = ("language",)
    classes = ("collapse",) if True else () 

class ProductionGenreInline(admin.TabularInline):
    model = ProductionGenre
    extra = 1
    autocomplete_fields = ("genre",)

class ProductionTagInline(admin.TabularInline):
    model = ProductionTag
    extra = 1
    autocomplete_fields = ("tag",)


@admin.register(UitDatabaseTheme)
class UitDatabaseThemeAdmin(BaseAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

@admin.register(UitDatabaseType)
class UitDatabaseTypeAdmin(BaseAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

@admin.register(Production)
class ProductionAdmin(BaseAdmin):
    """
    Admin configuration for Production.
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

    #