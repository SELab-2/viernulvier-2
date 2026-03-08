"""
Admin configuration for the Events app.

Events are scheduled occurrences of productions. The admin surfaces the
core scheduling fields and allows managing ``EventPrice`` entries inline.

Queryset optimisation
---------------------
``EventAdmin.get_queryset`` joins the full hall–space–location chain with
``select_related`` and prefetches production and hall translations, keeping
the list and detail pages free of N+1 queries.
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.core.admin import BaseAdmin
from .models import Event, EventPrice


# ===========================================================================
# Inline
# ===========================================================================


class EventPriceInline(admin.TabularInline):
    """
    Inline for managing price tiers directly inside the Event change page.

    Editors can add, update, or remove ``EventPrice`` entries — specifying
    the price rank, the ticket amount, and the number of available seats —
    without leaving the event form.
    """

    model = EventPrice
    extra = 0
    autocomplete_fields = ("price_rank",)
    fields = ("price_rank", "amount", "available")
    ordering = ("price_rank__position",)


# ===========================================================================
# Event admin
# ===========================================================================


@admin.register(Event)
class EventAdmin(BaseAdmin):
    """
    Admin configuration for the Event model.

    The list view shows the linked production, hall, and scheduling window.
    A ``date_hierarchy`` on ``starts_at`` allows editors to drill down by
    day. The ``EventPriceInline`` makes price management accessible from
    the event form.

    Queryset strategy
    -----------------
    - ``select_related("production", "hall", "hall__space",
      "hall__space__location")`` prevents N+1 queries for the FK chain
      rendered in ``list_display`` and the detail page.
    - ``prefetch_related("production__translations", "hall__translations",
      "prices")`` avoids extra queries for the search fields and inline.
    """

    list_display = (
        "id",
        "production",
        "hall",
        "starts_at",
        "ends_at",
    )

    list_filter = ("starts_at",)

    search_fields = (
        "id",
        "production__translations__title",
        "production__translations__artist_name",
        "hall__translations__name",
    )

    autocomplete_fields = ("production", "hall")

    ordering = ("-starts_at",)

    date_hierarchy = "starts_at"

    inlines = [EventPriceInline]
    readonly_fields = ("production_admin_link",)

    @admin.display(description="Production details")
    def production_admin_link(self, obj):
        """Return a link to the related Production admin change page."""
        if not obj or not obj.production_id:
            return "-"

        url = reverse("admin:productions_production_change", args=[obj.production_id])
        translation = obj.production.get_base_translation(related_name="translations")
        artist_name = (getattr(translation, "artist_name", "") or "").strip()
        label = (
            f"{obj.production} by {artist_name}" if artist_name else str(obj.production)
        )
        return format_html('<a href="{}">{}</a>', url, label)

    def get_queryset(self, request):
        """Optimise the queryset with select_related and prefetch_related."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "production",
                "hall",
                "hall__space",
                "hall__space__location",
            )
            .prefetch_related(
                "production__translations",
                "hall__translations",
                "prices",
            )
        )
