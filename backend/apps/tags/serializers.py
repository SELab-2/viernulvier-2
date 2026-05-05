"""Serializers for the Tags app.

Translated fields on ``TagSerializer`` (``name``, ``excerpt``,
``short_description``, ``url_title``) return all available translations
as language-code dictionaries
(e.g. {"en": "Contemporary", "fr": "Contemporain"}).
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from apps.media_library.serializers import MediaGallerySerializer

from .models import Tag


class TagSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Full representation of a Tag.

    Translated fields
    -----------------
    The following fields return all available translations as
    language-code dictionaries:

    - ``name``
    - ``excerpt``
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

    excerpt = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the tag excerpt "
            '(e.g. {"en": "A short summary", "fr": "Un court résumé"}). '
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

    display_excerpt = serializers.SerializerMethodField(
        help_text=(
            "Excerpt in the project's base language (derived from settings.LANGUAGE_CODE). "
            "Falls back to the first available translation when missing."
        ),
    )

    first_production_start = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
        help_text=(
            "Start time of the earliest production linked to this tag (UTC). "
            "`null` when the tag is not linked to any productions."
        ),
    )

    last_production_end = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
        help_text=(
            "End time of the latest production linked to this tag (UTC). "
            "`null` when the tag is not linked to any productions."
        ),
    )

    display_url_title = serializers.SerializerMethodField(
        help_text=(
            "URL-safe title in the project's base language (derived from settings.LANGUAGE_CODE). "
            "Falls back to the first available translation when missing."
        ),
    )

    media_gallery = MediaGallerySerializer(
        read_only=True,
        allow_null=True,
        help_text="Nested media gallery linked to this tag.",
    )

    class Meta:
        model = Tag
        fields = [
            "id",
            "url",
            "source",
            "type",
            "is_enabled",
            "display_name",
            "display_short_description",
            "display_excerpt",
            "display_url_title",
            "first_production_start",
            "last_production_end",
            "name",
            "excerpt",
            "short_description",
            "url_title",
            "media_gallery",
        ]
        read_only_fields = [
            "id",
            "name",
            "short_description",
            "display_name",
            "display_short_description",
            "display_excerpt",
            "display_url_title",
            "first_production_start",
            "last_production_end",
            "url_title",
            "media_gallery",
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

    def get_excerpt(self, obj: Tag) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "excerpt")

    def get_url_title(self, obj: Tag) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "url_title")

    def get_display_name(self, obj: Tag) -> str | None:
        """Return the base-language tag name (with fallback)."""
        return self.get_base_translated_value(obj, field_name="name")

    def get_display_short_description(self, obj: Tag) -> str | None:
        """Return the base-language short description (with fallback)."""
        return self.get_base_translated_value(obj, field_name="short_description")

    def get_display_excerpt(self, obj: Tag) -> str | None:
        """Return the base-language excerpt (with fallback)."""
        return self.get_base_translated_value(obj, field_name="excerpt")

    def get_display_url_title(self, obj: Tag) -> str | None:
        """Return the base-language URL title (with fallback)."""
        return self.get_base_translated_value(obj, field_name="url_title")
