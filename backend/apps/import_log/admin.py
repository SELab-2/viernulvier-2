"""
Admin configuration for the Imports app.

``ImportLogAdmin`` exposes the import pipeline's audit trail in the Django
admin as a read-only view. All fields are marked as ``readonly_fields`` and
manual creation is disabled via :meth:`ImportLogAdmin.has_add_permission`.

Import logs are created and updated exclusively by the import pipeline; the
admin exists purely for monitoring and debugging purposes.
"""

from django.contrib import admin

from apps.core.admin import BaseAdmin

from .models import ImportLog

# ===========================================================================
# ImportLog admin
# ===========================================================================


@admin.register(ImportLog)
class ImportLogAdmin(BaseAdmin):
    """
    Read-only admin for ImportLog records.

    The admin surfaces the full audit trail of every import run, including
    record counts, status, timestamps, and any error messages. All fields
    are rendered as read-only to prevent accidental edits.

    Manual creation of import logs via the admin is disabled - logs are
    created exclusively by the import pipeline.

    The list view is ordered from most recent to oldest via the model's
    default ``ordering = ["-started_at"]``. The ``status`` filter allows
    quick isolation of failed or in-progress runs.
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

    list_filter = ("status",)

    search_fields = (
        "source",
        "error_message",
    )

    ordering = ("-started_at",)

    # All fields are read-only - import logs must not be edited manually.
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

    def has_add_permission(self, request) -> bool:
        """
        Prevent manual creation of import logs via the admin.

        Import logs are created exclusively by the import pipeline and
        must never be inserted manually to preserve audit integrity.
        """
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """
        Prevent editing of import logs via the admin.

        All fields are already marked as ``readonly_fields``, but overriding
        this method provides an explicit additional guard and removes the
        save buttons from the detail page.
        """
        return False
