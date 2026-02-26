from django.contrib import admin
from apps.core.admin import BaseAdmin
from .models import Language


@admin.register(Language)
class LanguageAdmin(BaseAdmin):
    """
    Admin configuration for Language model.
    """

    list_display = (
        "code",
        "name",
        "is_active",
    )

    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("code",)