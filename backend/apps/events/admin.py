from django.contrib import admin
from apps.core.admin import BaseAdmin
from apps.events.models import Event, EventPrice


class EventPriceInline(admin.TabularInline):
    """Inline admin for EventPrice objects within an Event."""
    model = EventPrice
    extra = 0
    autocomplete_fields = ["price_rank"]
    fields = ("price_rank", "amount", "available")
    ordering = ("price_rank",)


@admin.register(Event)
class EventAdmin(BaseAdmin):
    """Admin configuration for Event."""

    list_display = (
        "id",
        "production",
        "hall",
        "starts_at",
        "ends_at",
    )

    list_filter = (
        "hall",
        "production",
        "starts_at",
    )

    search_fields = (
        "id",
        "production__translations__title",
        "production__translations__artist_name",
        "hall__translations__name",
    )

    autocomplete_fields = ["production", "hall"]

    ordering = ("-starts_at",)

    date_hierarchy = "starts_at"

    inlines = [EventPriceInline]

    def get_queryset(self, request):
        """
        Optimize related fetching:
        - production
        - hall → space → location
        - translations for production and hall
        """
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