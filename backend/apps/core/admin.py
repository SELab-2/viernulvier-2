"""
Base admin configuration for the core app.

``BaseAdmin`` is the single parent class for every ``ModelAdmin`` in the
project. Centralising shared admin behaviour here means project-wide
changes (e.g. adding a global ``list_per_page``, disabling bulk delete,
or injecting request-scoped context) only need to be made in one place.
"""

from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    """
    Project-wide base class for all ``ModelAdmin`` registrations.

    Every app-level admin class should inherit from ``BaseAdmin`` instead
    of ``admin.ModelAdmin`` directly. This ensures any future cross-cutting
    concerns (auditing, permission overrides, queryset scoping, etc.) can
    be introduced here without touching individual app admins.

    Current behaviour
    -----------------
    Delegates entirely to Django's default ``ModelAdmin``. Subclasses
    override ``get_queryset`` to add ``select_related`` / ``prefetch_related``
    optimisations specific to their model.
    """

    def get_queryset(self, request):
        """
        Return the base queryset for this admin.

        Subclasses should call ``super().get_queryset(request)`` and chain
        ``select_related`` / ``prefetch_related`` calls on the result to
        prevent N+1 queries on list and detail pages.
        """
        return super().get_queryset(request)
