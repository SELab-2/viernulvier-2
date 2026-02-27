from django.contrib import admin
from apps.core.admin import BaseAdmin
from .models import ImportLog


@admin.register(ImportLog)
class ImportLogAdmin(BaseAdmin):
    """
    Admin configuration for ImportLog.
    """

    list_display = (
        "id",
        "source",
        "status",
        "records_total",
        "records_imported",
        "records_failed",
        "started_at",
        "finished_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "source",
        "error_message",
    )

    readonly_fields = (
        "source",
        "status",
        "records_total",
        "records_imported",
        "records_failed",
        "started_at",
        "finished_at",
        "error_message",
    )

    def has_add_permission(self, request):
        """
        Prevent manual creation of import logs via the admin.
        Import logs are created exclusively by the import pipeline.
        """
        return False