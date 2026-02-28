"""
Serializers for the Pricing app.

Field-level `help_text` and `extra_kwargs` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do
not need to be repeated inside the schema decorators.

The translated `description` field on both serializers is resolved via
`TranslatableSerializerMixin` using the `Accept-Language` request header.
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from .models import Price, PriceRank


class PriceSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
    """
    Represents a Price category.

    The `description` field is localised: its value is resolved from the
    price's translation table based on the `Accept-Language` request header.
    """

    description = serializers.SerializerMethodField(
        help_text=(
            "Localised human-readable label resolved via the `Accept-Language` header "
            "(e.g. `Full price`, `Student`). "
            "Empty string when no translation is available for the resolved language. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

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
            "description",
        ]
        read_only_fields = ["id", "description"]
        extra_kwargs = {
            "type": {
                "help_text": "Internal identifier for the price category (e.g. `full`, `student`).",
            },
            "visibility": {
                "help_text": "Controls which audiences see this price (e.g. `public`, `members_only`).",
            },
            "membership": {
                "help_text": "Membership level required to access this price. Empty string means no requirement.",
            },
            "minimum": {
                "help_text": (
                    "Lower bound for variable pricing in euro cents (inclusive). "
                    "Must be set together with `maximum` and `step`, or left null."
                ),
            },
            "maximum": {
                "help_text": (
                    "Upper bound for variable pricing in euro cents (inclusive). "
                    "Must be set together with `minimum` and `step`, or left null."
                ),
            },
            "step": {
                "help_text": (
                    "Increment size in euro cents for variable pricing (≥ 1). "
                    "Must be set together with `minimum` and `maximum`, or left null."
                ),
            },
            "sort_order": {
                "help_text": "Display order index. Lower values appear first.",
            },
            "cineville_box": {
                "help_text": "`true` when this price applies to Cineville box holders.",
            },
        }

    def get_description(self, obj: Price) -> str:
        """Resolve the localised description via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "description")


class PriceRankSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
    """
    Represents a PriceRank availability tier.

    The `description` field is localised: its value is resolved from the
    price rank's translation table based on the `Accept-Language` request header.
    """

    description = serializers.SerializerMethodField(
        help_text=(
            "Localised human-readable label resolved via the `Accept-Language` header. "
            "Empty string when no translation is available for the resolved language. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    class Meta:
        model = PriceRank
        fields = [
            "id",
            "position",
            "sold_out_buffer",
            "description",
        ]
        read_only_fields = ["id", "description"]
        extra_kwargs = {
            "position": {
                "help_text": "Rank position used for ordering and priority. Must be unique.",
            },
            "sold_out_buffer": {
                "help_text": (
                    "Extra capacity offset used to consider this rank sold out "
                    "slightly earlier or later than actual capacity."
                ),
            },
        }

    def get_description(self, obj: PriceRank) -> str:
        """Resolve the localised description via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "description")