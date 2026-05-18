"""Serializers for the Events app.

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
from apps.locations.models import Hall
from apps.locations.serializers import HallSerializer
from apps.pricing.serializers import PriceRankSerializer, PriceSerializer
from apps.productions.models import Production
from apps.productions.serializers import ProductionSerializer

from .models import Event, EventPrice


class EventPriceSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Represents a single price tier assigned to an event.

    Each ``EventPrice`` links an event to a ``PriceRank`` and records the
    ticket amount (in euro) and the number of seats available at that rank.

    This serializer is used exclusively as a nested read-only representation
    inside ``EventSerializer``. Use the dedicated **Event Price** endpoints
    to create or modify price entries.
    """

    price_rank_display = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    price = PriceSerializer(
        allow_null=True,
        required=False,
        help_text="PK of the associated ``Price`` category. `null` when the price has been deleted.",
    )
    price_rank = PriceRankSerializer(
        allow_null=True,
        required=False,
        help_text="PK of the associated ``PriceRank`` availability tier. `null` when the rank has been deleted.",
    )

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_price_rank_display(self, obj: EventPrice) -> str | None:
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
    def get_price_display(self, obj: EventPrice) -> str | None:
        """Return the price category name in the project's base language."""
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
            "price_rank_display": {"help_text": "String for the price rank in the display representation."},
            "price_display": {"help_text": "String for the price category in the display representation."},
            "amount": {"help_text": "Ticket price in euro (e.g. `18.00`)."},
            "available": {"help_text": "Number of tickets available at this price rank for the event."},
        }


class EventSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Full representation of an Event.

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

    production = ProductionSerializer(read_only=True, help_text="Full production object (read-only)")
    hall = HallSerializer(read_only=True, help_text="Full hall object (read-only)")

    production_id = serializers.PrimaryKeyRelatedField(
        queryset=Production.objects.all(),
        write_only=True,
        required=True,
        help_text="ID of the production this event is a performance of. Use this field for create/update.",
        source="production",
    )

    hall_id = serializers.PrimaryKeyRelatedField(
        queryset=Hall.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of the hall in which the event takes place. "
        "Use null for online/location-independent events. Use this field for create/update.",
        source="hall",
    )

    @extend_schema_field(serializers.CharField())
    def get_production_display(self, obj: Event) -> str:
        """Return the production name in the project's base language."""
        return self.get_base_translated_value(
            obj.production,
            field_name="title",
            related_name="translations",
            fallback=str(obj.production_id),
        )

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_hall_display(self, obj: Event) -> str | None:
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
            "production_id",
            "production_display",
            "hall",
            "hall_id",
            "hall_display",
            "starts_at",
            "ends_at",
            "prices",
        ]
        read_only_fields = ["id", "prices", "production", "hall"]
        extra_kwargs = {
            "production_display": {"help_text": "String for the production in the display representation."},
            "hall_display": {"help_text": "String for the hall in the display representation."},
            "starts_at": {
                "help_text": "ISO 8601 UTC datetime at which the event begins.",
            },
            "ends_at": {
                "help_text": ("ISO 8601 UTC datetime at which the event ends. Must be later than or equal to `starts_at`."),
            },
        }


class NestedEventSerializer(EventSerializer):
    """Compact event representation for use when nested inside a Production response.

    Production fields are excluded to avoid redundant/circular data.
    """

    class Meta(EventSerializer.Meta):
        fields = [f for f in EventSerializer.Meta.fields if not f.startswith("production")]
        read_only_fields = [f for f in EventSerializer.Meta.read_only_fields if not f.startswith("production")]
