"""
Serializers for the Genre app.

Field-level `help_text` and `extra_kwargs` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do
not need to be repeated inside the schema decorators.
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from .models import Genre, GenreUseAs


class GenreUseAsSerializer(serializers.ModelSerializer):
    """
    Represents a GenreUseAs object — the role a genre plays in the system.
    """

    class Meta:
        model = GenreUseAs
        fields = ["id", "name"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "name": {
                "help_text": (
                    "Human-readable label for this usage context "
                    "(e.g. `genre`, `tag`, `category`)."
                ),
            },
        }


class GenreSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
    """
    Represents a Genre.

    The `name` field is localised: its value is resolved from the genre's
    translation table based on the `Accept-Language` request header.
    """

    name = serializers.SerializerMethodField(
        help_text=(
            "Localised display name resolved via the `Accept-Language` header. "
            "Falls back to the default language when no translation is available. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    class Meta:
        model = Genre
        fields = ["id", "type", "use_as", "name"]
        read_only_fields = ["id", "name"]
        extra_kwargs = {
            "type": {
                "help_text": (
                    "Internal technical identifier in `snake_case` "
                    "(e.g. `theater`, `contemporary_dance`, `festival`)."
                ),
            },
            "use_as": {
                "help_text": (
                    "Primary key of the **GenreUseAs** that defines how this "
                    "genre is applied (taxonomy classification or tag)."
                ),
            },
        }

    def get_name(self, obj: Genre) -> str | None:
        """Resolve the localised display name via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "name")