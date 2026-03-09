"""
Serializers for the Locations app.

Field-level `help_text` and `extra_kwargs` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do
not need to be repeated inside the schema decorators.

Translated fields (`name`, `remark`) return all available translations
as a dictionary (e.g. {"en": "Main Hall", "fr": "Grande Salle"}).
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin

from .models import Hall, Location, Space


class LocationSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
    """
    Represents a Location.

    The `name` field contains all available translations as a dictionary,
    for example: {"en": "City Hall", "fr": "Hôtel de Ville"}.
    """

    name = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the location name "
            '(e.g. {"en": "City Hall", "fr": "Hôtel de Ville"}). '
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    display_name = serializers.SerializerMethodField(
        help_text=(
            "Human-readable location name in the project's base language. "
            "Falls back to the first available translation when the base "
            "language translation is missing."
        )
    )

    class Meta:
        model = Location
        fields = [
            "id",
            "street",
            "number",
            "postal_code",
            "city",
            "country",
            "phone_1",
            "phone_2",
            "is_own_location",
            "name",
            "display_name",
        ]
        read_only_fields = ["id", "display_name", "name"]
        extra_kwargs = {
            "street": {"help_text": "Street name of the location."},
            "number": {"help_text": "Street / house number."},
            "postal_code": {"help_text": "Postal or ZIP code."},
            "city": {"help_text": "City in which the location sits."},
            "country": {"help_text": "Country in which the location sits."},
            "phone_1": {"help_text": "Primary contact phone number (optional)."},
            "phone_2": {"help_text": "Secondary contact phone number (optional)."},
            "is_own_location": {
                "help_text": "`true` when this venue is owned or operated by the organisation.",
            },
        }

    def get_name(self, obj: Location) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "name")

    def get_display_name(self, obj: Location) -> str | None:
        """Return the location name in the project's base language."""
        return self.get_base_translated_value(obj, "name")


class SpaceSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
    """
    Represents a Space.

    The `name` field contains all available translations as a dictionary,
    for example: {"en": "Stage A", "fr": "Scène A"}.
    """

    name = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the space name "
            '(e.g. {"en": "Stage A", "fr": "Scène A"}). '
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    display_name = serializers.SerializerMethodField(
        help_text="Human-readable space name in the project's base language."
    )

    class Meta:
        model = Space
        fields = ["id", "location", "name", "display_name"]
        read_only_fields = ["id", "name", "display_name"]
        extra_kwargs = {
            "location": {
                "help_text": "Primary key of the parent **Location** this space belongs to.",
            },
        }

    def get_name(self, obj: Space) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "name")

    def get_display_name(self, obj: Space) -> str | None:
        """Return the space name in the project's base language."""
        return self.get_base_translated_value(obj, "name")


class HallSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
    """
    Represents a Hall.

    Both `name` and `remark` contain all available translations
    as dictionaries (e.g. {"en": "Main Hall", "fr": "Grande Salle"}).
    """

    name = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the hall name "
            '(e.g. {"en": "Main Hall", "fr": "Grande Salle"}). '
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    display_name = serializers.SerializerMethodField(
        help_text="Human-readable hall name in the project's base language."
    )

    remark = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the optional remark "
            '(e.g. {"en": "Wheelchair accessible", '
            '"fr": "Accessible en fauteuil roulant"}). '
            "`null` when no remark translations have been set. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    class Meta:
        model = Hall
        fields = [
            "id",
            "space",
            "seat_selection",
            "open_seating",
            "name",
            "display_name",
            "remark",
        ]
        read_only_fields = ["id", "name", "display_remark", "remark"]
        extra_kwargs = {
            "space": {
                "help_text": "Primary key of the parent **Space** this hall belongs to.",
            },
            "seat_selection": {
                "help_text": "`true` when visitors can choose a specific seat during purchase.",
            },
            "open_seating": {
                "help_text": "`true` when seating is general-admission (no fixed seat assignment).",
            },
        }

    def get_name(self, obj: Hall) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "name")

    def get_display_name(self, obj: Hall) -> str | None:
        """Return the hall name in the project's base language."""
        return self.get_base_translated_value(obj, "name")

    def get_remark(self, obj: Hall) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "remark")
