"""
Serializers for the Events app.

Field-level ``help_text`` and ``extra_kwargs`` are picked up automatically by
drf-spectacular and rendered in the Swagger UI, so descriptions do not need to
be repeated inside the schema decorators.

``EventPriceSerializer`` is a flat serializer for the ``EventPrice``
through-table. It is nested read-only inside ``EventSerializer`` via the
``prices`` reverse relation.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin

from .models import Event, EventPrice


class EventPriceSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """
    Represents a single price tier assigned to an event.

    Each ``EventPrice`` links an event to a ``PriceRank`` and records the
    ticket amount (in euro) and the number of seats available at that rank.

    This serializer is used exclusively as a nested read-only representation
    inside ``EventSerializer``. Use the dedicated **Event Price** endpoints
    to create or modify price entries.
    """

    price_rank_display = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_price_rank_display(self, obj):
        """Return the price rank name in the project's base language."""
        if not obj.price_rank:
            return None
        return self.get_base_translated_value(
            obj.price_rank,
            field_name="description",
            related_name="translations",
            fallback=str(obj.price_rank_id),
        )

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_price_display(self, obj):
        if not obj.price:
            return None
        return self.get_base_translated_value(
            obj.price,
            field_name="description",
            related_name="translations",
            fallback=str(obj.price_id),
        )

    class Meta:
        model = EventPrice
        fields = [
            "id",
            "event",
            "price_rank",
            "price_rank_display",
            "price",
            "price_display",
            "amount",
            "available",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "event": {"help_text": "PK of the event this price entry belongs to."},
            "price_rank": {
                "help_text": (
                    "PK of the associated ``PriceRank`` availability tier. `null` when the rank has been deleted."
                ),
            },
            "price_rank_display": {"help_text": "String for the price rank in the display representation."},
            "price": {
                "help_text": ("PK of the associated ``Price`` category. `null` when the price has been deleted."),
            },
            "price_display": {"help_text": "String for the price category in the display representation."},
            "amount": {"help_text": "Ticket price in euro (e.g. `18.00`)."},
            "available": {"help_text": "Number of tickets available at this price rank for the event."},
        }


class EventSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """
    Full representation of an Event.

    An event is a scheduled occurrence of a production inside a hall. The
    ``prices`` field is a nested read-only array of ``EventPriceSerializer``
    instances and is populated from the ``prices`` reverse relation.

    Timestamps
    ----------
    Both ``starts_at`` and ``ends_at`` are ISO 8601 datetime strings in UTC.
    The API enforces ``ends_at > starts_at`` at the database level via a
    check constraint; the serializer surfaces a 400 response when this
    constraint would be violated.

    Prices
    ------
    ``prices`` is read-only on this serializer. To add, update, or remove
    price entries, use the dedicated **Event Price** endpoints.
    """

    prices = EventPriceSerializer(
        many=True,
        read_only=True,
        help_text=(
            "Price tiers assigned to this event, ordered by price rank. "
            "Read-only - use the Event Price endpoints to manage entries."
        ),
    )

    production_display = serializers.SerializerMethodField()
    hall_display = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField())
    def get_production_display(self, obj):
        """Return the production name in the project's base language."""
        return self.get_base_translated_value(
            obj.production,
            field_name="title",
            related_name="translations",
            fallback=str(obj.production_id),
        )

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_hall_display(self, obj):
        """Return the hall name in the project's base language."""
        if not obj.hall:
            return None
        return self.get_base_translated_value(
            obj.hall,
            field_name="name",
            related_name="translations",
            fallback=str(obj.hall_id),
        )

    class Meta:
        model = Event
        fields = [
            "id",
            "production",
            "production_display",
            "hall",
            "hall_display",
            "starts_at",
            "ends_at",
            "prices",
        ]
        read_only_fields = ["id", "prices"]
        extra_kwargs = {
            "production": {
                "help_text": "PK of the production this event is a performance of.",
            },
            "production_display": {"help_text": "String for the production in the display representation."},
            "hall": {
                "help_text": (
                    "PK of the hall in which the event takes place. `null` for online or location-independent events."
                ),
            },
            "hall_display": {"help_text": "String for the hall in the display representation."},
            "starts_at": {
                "help_text": "ISO 8601 UTC datetime at which the event begins.",
            },
            "ends_at": {
                "help_text": ("ISO 8601 UTC datetime at which the event ends. Must be strictly later than `starts_at`."),
            },
        }
