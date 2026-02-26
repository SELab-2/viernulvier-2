from rest_framework import serializers
from apps.pricing.models import Price, PriceRank
from apps.core.serializers import TranslatableSerializerMixin


class PriceSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Serializer for Price model."""
    description = serializers.SerializerMethodField()

    class Meta:
        model = Price
        fields = [
            "id",
            "type",
            "visibility",
            "membership",
            "minimum",
            "maximum",
            "step",
            "sort_order",
            "cineville_box",
            "description"
        ]
        read_only_fields = ["id", "description"]

    def get_type(self, obj):
        """Retrieve the price's type in the requested language (if given)."""
        return self.get_translated_field(obj, "type")
    
    def get_visibility(self, obj):
        """Retrieve the price's visibility in the requested language (if given)."""
        return self.get_translated_field(obj, "visibility")
    
    def get_membership(self, obj):
        """Retrieve the membership corresponding to the price in the requested language (if given)."""
        return self.get_translated_field(obj, "membership")

    def get_description(self, obj):
        """Retrieve the price's description in the requested language (if given)."""
        return self.get_translated_field(obj, "description")


class PriceRankSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Serializer for PriceRank model."""
    description = serializers.SerializerMethodField()

    class Meta:
        model = PriceRank
        fields = [
            "id",
            "position",
            "sold_out_buffer",
            "description"
        ]
        read_only_fields = ["id"]

    def get_description(self, obj):
        return self.get_translated_field(obj, "description")