"""Serializers for the Genre app.

Field-level `help_text` and `extra_kwargs` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do
not need to be repeated inside the schema decorators.
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin

from .models import Genre, GenreUseAs


class GenreUseAsSerializer(serializers.ModelSerializer):
    """Represents a GenreUseAs object - the role a genre plays in the system."""

    class Meta:
        model = GenreUseAs
        fields = ["id", "name"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "name": {
                "help_text": ("Human-readable label for this usage context (e.g. `genre`, `tag`, `category`)."),
            },
        }


class GenreSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Represents a Genre.

    The `name` field contains all available translations as a dictionary,
    for example: {"en": "Theatre", "fr": "Théâtre"}.
    """

    name = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the genre name, "
            'e.g. {"en": "Theatre", "fr": "Théâtre"}. '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    display_name = serializers.SerializerMethodField(
        help_text=(
            "Human-readable name in the project's base language "
            "(e.g. `Theatre`). Falls back to the first available "
            "translation when the base language is missing."
        )
    )

    vendor_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=(
            "Vendor-specific identifier from the upstream API. Optional, but "
            "can be used to link back to the original source."
        ),
    )

    use_as_id = serializers.PrimaryKeyRelatedField(
        queryset=GenreUseAs.objects.all(),
        source="use_as",
        write_only=True,
        required=True,
        help_text="ID of the parent GenreUseAs (write-only).",
    )

    use_as = GenreUseAsSerializer(
        help_text=(
            "Primary key of the **GenreUseAs** that defines how this genre is applied (taxonomy classification or tag)."
        ),
        read_only=True,
    )

    class Meta:
        model = Genre
        fields = ["id", "type", "use_as", "name", "display_name", "vendor_id", "use_as_id"]
        read_only_fields = ["id", "name", "display_name", "use_as"]
        extra_kwargs = {
            "type": {
                "help_text": (
                    "Internal technical identifier in `snake_case` (e.g. `theater`, `contemporary_dance`, `festival`)."
                ),
            },
            "vendor_id": {
                "help_text": (
                    "Vendor-specific identifier from the upstream API. Optional, but "
                    "can be used to link back to the original source."
                ),
            },
        }

    def get_name(self, obj: Genre) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "name")

    def get_display_name(self, obj: Genre) -> str | None:
        """Return the genre name in the project's base language."""
        return self.get_base_translated_value(obj, "name")
