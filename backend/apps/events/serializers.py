from rest_framework import serializers
from apps.events.models import Event, EventPrice


class EventPriceSerializer(serializers.ModelSerializer):
    """Serializer for the EventPrice model."""
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


class EventSerializer(serializers.ModelSerializer):
    """Serializer for the Event model."""
    prices = EventPriceSerializer(many=True, read_only=True)

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