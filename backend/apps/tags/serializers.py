"""Serializers for the Tags app.

Translated fields on ``TagSerializer`` (``name``,
``short_description``, ``url_title``) return all available translations
as language-code dictionaries
(e.g. {"en": "Contemporary", "fr": "Contemporain"}).
"""

from rest_framework import serializers
from django.db.models import Prefetch
from django.apps import apps

from apps.core.serializers import TranslatableSerializerMixin

from .models import Tag
from apps.media_library.models import MediaItem


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
            "image",
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

    def get_image(self, obj: Tag) -> str | None:
        """Return the absolute URL of the tag's uploaded image.

        If the Tag has no `image`, fall back to the image of the most
        recent Production that uses this Tag and has a media gallery with
        at least one media item crop image. This fallback is applied only
        when serializing (GET responses) and is not stored on the Tag.
        """
        request = self.context.get("request") if hasattr(self, "context") else None

        # Direct image on the tag
        if obj.image:
            try:
                url = obj.image.url
            except Exception:
                return None
            return request.build_absolute_uri(url) if request else url

        # Fallback: find most recent production with this tag and an image
        Production = apps.get_model("productions", "Production")
        MediaItemModel = MediaItem

        prod_qs = (
            Production.objects.filter(tags=obj, media_gallery__isnull=False)
            .select_related("media_gallery")
            .prefetch_related(
                Prefetch(
                    "media_gallery__media_items",
                    queryset=MediaItemModel.objects.prefetch_related("crops").order_by("position"),
                )
            )
            .order_by("-id")
        )

        for production in prod_qs:
            media_items = production.media_gallery.media_items.all() if production.media_gallery else []
            if not media_items:
                continue
            first_item = media_items[0]
            first_crop = next(iter(first_item.crops.all()), None)
            if first_crop and getattr(first_crop, "image", None):
                try:
                    url = first_crop.image.url
                except Exception:
                    return None
                return request.build_absolute_uri(url) if request else url

        return None
