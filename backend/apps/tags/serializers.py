"""Serializers for the Tags app.

Translated fields on ``TagSerializer`` (``name``,
``short_description``, ``url_title``) return all available translations
as language-code dictionaries
(e.g. {"en": "Contemporary", "fr": "Contemporain"}).
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin

from .models import Tag


class TagSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Full representation of a Tag.

    Translated fields
    -----------------
    The following fields return all available translations as
    language-code dictionaries:

    - ``name``
    - ``short_description``
    - ``url_title``

    All translated fields are read-only.
    """

    # ---------------------------------------------------------------------------
    # Translatable fields
    # ---------------------------------------------------------------------------

    name = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the tag name "
            '(e.g. {"en": "Contemporary", "fr": "Contemporain"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    short_description = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the tag's short description "
            '(e.g. {"en": "Contemporary performing arts", "fr": "Arts du spectacle contemporain"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    url_title = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the URL-safe title "
            '(e.g. {"en": "contemporary", "fr": "contemporain"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    display_name = serializers.SerializerMethodField(
        help_text=(
            "Tag name in the project's base language (derived from settings.LANGUAGE_CODE). "
            "Falls back to the first available translation when missing."
        ),
    )

    display_short_description = serializers.SerializerMethodField(
        help_text=(
            "Short description in the project's base language (derived from settings.LANGUAGE_CODE). "
            "Falls back to the first available translation when missing."
        ),
    )

    display_url_title = serializers.SerializerMethodField(
        help_text=(
            "URL-safe title in the project's base language (derived from settings.LANGUAGE_CODE). "
            "Falls back to the first available translation when missing."
        ),
    )
        image = serializers.SerializerMethodField(
            help_text=(
                "URL of the uploaded image for this tag. "
                "If not set, falls back to the image of the most recent production using this tag. "
                "Read-only."
            ),
        )

    class Meta:
        model = Tag
        fields = [
            "id",
            "url",
            "source",
            "type",
            "is_enabled",
            "image",
            "display_name",
            "display_short_description",
            "display_url_title",
            "name",
            "short_description",
            "url_title",
        ]
        read_only_fields = [
            "id",
            "name",
            "short_description",
            "display_name",
            "display_short_description",
            "display_url_title",
            "url_title",
        ]
        extra_kwargs = {
            "url": {
                "help_text": "Public URL of the tag in the originating system. Empty string when not applicable.",
            },
            "source": {
                "help_text": "Identifier of the system that created this tag (e.g. `uitdatabank`, `system`).",
            },
            "type": {
                "help_text": "Internal category of the tag used for grouping (e.g. `theme`, `audience`).",
            },
            "is_enabled": {
                "help_text": "`false` to soft-disable the tag without removing it.",
            },
        }

    # ---------------------------------------------------------------------------
    # SerializerMethodField implementations
    # ---------------------------------------------------------------------------

    def get_name(self, obj: Tag) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "name")

    def get_short_description(self, obj: Tag) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "short_description")

    def get_url_title(self, obj: Tag) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "url_title")

    def get_display_name(self, obj: Tag) -> str | None:
        """Return the base-language tag name (with fallback)."""
        return self.get_base_translated_value(obj, field_name="name")

    def get_display_short_description(self, obj: Tag) -> str | None:
        """Return the base-language short description (with fallback)."""
        return self.get_base_translated_value(obj, field_name="short_description")

    def get_display_url_title(self, obj: Tag) -> str | None:
        """Return the base-language URL title (with fallback)."""
        return self.get_base_translated_value(obj, field_name="url_title")
