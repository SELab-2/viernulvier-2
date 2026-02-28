"""
Serializers for the Events app.

Field-level ``help_text`` and ``extra_kwargs`` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do not
need to be repeated inside the schema decorators.

``EventPriceSerializer`` is a flat serializer for the ``EventPrice``
through-table. It is nested read-only inside ``EventSerializer`` via the
``prices`` reverse relation.
"""

from rest_framework import serializers

from .models import Event, EventPrice


class EventPriceSerializer(serializers.ModelSerializer):
    """
    Represents a single price tier assigned to an event.

    Each ``EventPrice`` links an event to a ``PriceRank`` and records the
    ticket amount (in euro) and the number of seats available at that rank.

    This serializer is used exclusively as a nested read-only representation
    inside ``EventSerializer``. Use the dedicated **Event Price** endpoints
    to create or modify price entries.
    """

    class Meta:
        model = EventPrice
        fields = [
            "id",
            "event",
            "price_rank",
            "amount",
            "available",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "event": {
                "help_text": "PK of the event this price entry belongs to.",
            },
            "price_rank": {
                "help_text": (
                    "PK of the associated ``PriceRank`` availability tier. "
                    "`null` when the rank has been deleted."
                ),
            },
            "amount": {
                "help_text": "Ticket price in euro (e.g. `18.00`).",
            },
            "available": {
                "help_text": "Number of tickets available at this price rank for the event.",
            },
        }


class EventSerializer(serializers.ModelSerializer):
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
            "Read-only — use the Event Price endpoints to manage entries."
        ),
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "production",
            "hall",
            "starts_at",
            "ends_at",
            "ticketing_url",
            "prices",
        ]
        read_only_fields = ["id", "prices"]
        extra_kwargs = {
            "production": {
                "help_text": "PK of the production this event is a performance of.",
            },
            "hall": {
                "help_text": (
                    "PK of the hall in which the event takes place. "
                    "`null` for online or location-independent events."
                ),
            },
            "starts_at": {
                "help_text": "ISO 8601 UTC datetime at which the event begins.",
            },
            "ends_at": {
                "help_text": (
                    "ISO 8601 UTC datetime at which the event ends. "
                    "Must be strictly later than `starts_at`."
                ),
            },
            "ticketing_url": {
                "help_text": "Public URL where tickets for this event can be purchased. Empty string when not applicable.",
            },
        }