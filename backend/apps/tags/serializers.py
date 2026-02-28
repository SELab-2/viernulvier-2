"""
Serializers for the Tags app.

Field-level ``help_text`` and ``extra_kwargs`` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do not
need to be repeated inside the schema decorators.

The translatable fields on ``TagSerializer`` (``name``, ``short_description``,
``url_title``) are resolved via ``TranslatableSerializerMixin`` using the
``Accept-Language`` request header.
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from .models import Tag


class TagSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """
    Full representation of a Tag.

    Translatable fields
    -------------------
    The following fields are resolved from the tag's translation table based
    on the ``Accept-Language`` request header:

    - ``name``
    - ``short_description``
    - ``url_title``

    All translatable fields are read-only. Use the **Tag Translation**
    endpoints to manage translations.
    """

    # ---------------------------------------------------------------------------
    # Translatable fields (resolved via Accept-Language)
    # ---------------------------------------------------------------------------

    name = serializers.SerializerMethodField(
        help_text=(
            "Localised display name of the tag resolved via the `Accept-Language` header "
            "(e.g. `Contemporary`, `Family friendly`). "
            "Empty string when no translation exists for the resolved language. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    short_description = serializers.SerializerMethodField(
        help_text=(
            "Localised short description of the tag resolved via the `Accept-Language` header. "
            "`null` when no description has been provided. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    url_title = serializers.SerializerMethodField(
        help_text=(
            "Localised URL-safe title of the tag resolved via the `Accept-Language` header "
            "(e.g. `contemporary`, `family-friendly`). "
            "Empty string when no translation exists for the resolved language. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    class Meta:
        model = Tag
        fields = [
            "id",
            "url",
            "source",
            "source_type",
            "type",
            "is_external",
            "is_enabled",
            "name",
            "short_description",
            "url_title",
        ]
        read_only_fields = ["id", "name", "short_description", "url_title"]
        extra_kwargs = {
            "url": {
                "help_text": "Public URL of the tag in the originating system. Empty string when not applicable.",
            },
            "source": {
                "help_text": "Identifier of the system that created this tag (e.g. `uitdatabank`, `system`).",
            },
            "source_type": {
                "help_text": "Sub-classification of the source (e.g. `theme`, `targetAudience`).",
            },
            "type": {
                "help_text": "Internal category of the tag used for grouping (e.g. `theme`, `audience`).",
            },
            "is_external": {
                "help_text": "`true` when this tag was imported from an external system.",
            },
            "is_enabled": {
                "help_text": "`false` to soft-disable the tag without removing it.",
            },
        }

    # ---------------------------------------------------------------------------
    # SerializerMethodField implementations
    # ---------------------------------------------------------------------------

    def get_name(self, obj: Tag) -> str:
        """Resolve the localised name via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "name")

    def get_short_description(self, obj: Tag):
        """Resolve the localised short description via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "short_description")

    def get_url_title(self, obj: Tag) -> str:
        """Resolve the localised URL title via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "url_title")