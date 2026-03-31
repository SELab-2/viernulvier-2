"""Serializers for the Pricing app.

Field-level `help_text` and `extra_kwargs` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do
not need to be repeated inside the schema decorators.

The translated `description` field on both serializers returns all
available translations as a language-code dictionary
(e.g. {"en": "Full price", "fr": "Plein tarif"}).
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin

from .models import Price, PriceRank


class PriceSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
    """Represents a Price category.

    The `description` field contains all available translations as a
    dictionary (e.g. {"en": "Full price", "fr": "Plein tarif"}).
    """

    description = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the human-readable label "
            '(e.g. {"en": "Full price", "fr": "Plein tarif"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    display_description = serializers.SerializerMethodField(
        help_text=(
            "Human-readable label in the project's base language. "
            "Falls back to the first available translation when missing."
        )
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
            "display_description",
        ]
        read_only_fields = ["id", "description", "display_description"]
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

    def get_description(self, obj: Price) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "description")

    def get_display_description(self, obj: Price) -> str | None:
        """Return the price label in the project's base language."""
        return self.get_base_translated_value(obj, field_name="description")


class PriceRankSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
    """Represents a PriceRank availability tier.

    The `description` field contains all available translations as a
    dictionary (e.g. {"en": "Early Bird", "fr": "Prévente"}).
    """

    description = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the label "
            '(e.g. {"en": "Early Bird", "fr": "Prévente"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    display_description = serializers.SerializerMethodField(
        help_text=(
            "Human-readable label in the project's base language. "
            "Falls back to the first available translation when missing."
        )
    )

    class Meta:
        model = PriceRank
        fields = [
            "id",
            "position",
            "sold_out_buffer",
            "description",
            "display_description",
        ]
        read_only_fields = ["id", "description", "display_description"]
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

    def get_description(self, obj: PriceRank) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "description")

    def get_display_description(self, obj: PriceRank) -> str | None:
        """Return the price rank label in the project's base language."""
        return self.get_base_translated_value(obj, field_name="description")
