"""
Serializers for the Media app.

Field-level `help_text` and `extra_kwargs` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do
not need to be repeated inside the schema decorators.

Translated fields (`title`, `description`, `credits`, `link`) are resolved
via `TranslatableSerializerMixin` using the `Accept-Language` request header.
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from .models import MediaGallery, MediaItem, MediaItemCrop


class MediaItemCropSerializer(serializers.ModelSerializer):
    """
    Represents a named crop variant of a MediaItem.

    Read-only — crops are managed via the Media Item Crop endpoints.
    """

    class Meta:
        model = MediaItemCrop
        fields = [
            "id",
            "name",
            "url",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "name": {
                "help_text": "Crop variant identifier (e.g. `thumbnail`, `banner`, `square`).",
            },
            "url": {
                "help_text": "Publicly accessible URL of the cropped asset.",
            },
        }


class MediaItemSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
    """
    Represents a MediaItem with its localised metadata and nested crops.

    The translated fields (`title`, `description`, `credits`, `link`) are
    resolved from the item's translation table based on the `Accept-Language`
    request header. All translated fields are read-only — use the Media Item
    Translation endpoints to manage them.

    Nested `crops` is a read-only list of all pre-rendered crop variants.
    """

    title = serializers.SerializerMethodField(
        help_text=(
            "Localised title resolved via the `Accept-Language` header. "
            "Empty string when no title has been set for the resolved language. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    description = serializers.SerializerMethodField(
        help_text=(
            "Localised description resolved via the `Accept-Language` header. "
            "Empty string when no description has been set for the resolved language. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    credits = serializers.SerializerMethodField(
        help_text=(
            "Localised credits string resolved via the `Accept-Language` header. "
            "Empty string when no credits have been set for the resolved language. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    link = serializers.SerializerMethodField(
        help_text=(
            "Localised external URL resolved via the `Accept-Language` header. "
            "Empty string when no link has been set for the resolved language. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    crops = MediaItemCropSerializer(many=True, read_only=True)

    class Meta:
        model = MediaItem
        fields = [
            "id",
            "gallery",
            "type",
            "format",
            "original_filename",
            "position",
            "width",
            "height",
            "title",
            "description",
            "credits",
            "link",
            "crops",
        ]
        read_only_fields = ["id", "title", "description", "credits", "link", "crops"]
        extra_kwargs = {
            "gallery": {
                "help_text": "Primary key of the parent **MediaGallery** this item belongs to.",
            },
            "type": {
                "help_text": "Media type: `image`, `video`, or `audio`.",
            },
            "format": {
                "help_text": "File format / extension (e.g. `jpg`, `mp4`, `mp3`).",
            },
            "original_filename": {
                "help_text": "Original filename as uploaded.",
            },
            "position": {
                "help_text": "Display order within the gallery. Lower values appear first.",
            },
            "width": {
                "help_text": "Width in pixels. Applies to images and videos only.",
            },
            "height": {
                "help_text": "Height in pixels. Applies to images and videos only.",
            },
        }

    def get_title(self, obj: MediaItem) -> str:
        """Resolve the localised title via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "title")

    def get_description(self, obj: MediaItem) -> str:
        """Resolve the localised description via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "description")

    def get_credits(self, obj: MediaItem) -> str:
        """Resolve the localised credits via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "credits")

    def get_link(self, obj: MediaItem) -> str:
        """Resolve the localised external link via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "link")


class MediaGallerySerializer(serializers.ModelSerializer):
    """
    Represents a MediaGallery with its nested media items.

    The `media_items` field is a read-only nested list of all items in the
    gallery, ordered by `position`. Each item includes its localised metadata
    and crop variants.
    """

    media_items = MediaItemSerializer(many=True, read_only=True)

    class Meta:
        model = MediaGallery
        fields = [
            "id",
            "name",
            "media_items",
        ]
        read_only_fields = ["id", "media_items"]
        extra_kwargs = {
            "name": {
                "help_text": "Human-readable name of the gallery.",
            },
        }