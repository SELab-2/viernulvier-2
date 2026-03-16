"""
Serializers for the Media app.

Field-level `help_text` and `extra_kwargs` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do
not need to be repeated inside the schema decorators.

Translated fields (`title`, `description`, `credits`, `link`) return
all available translations as language-code dictionaries
(e.g. {"en": "Poster", "fr": "Affiche"}).
"""

from rest_framework import serializers

from apps.core.serializers import NestedRepresentationPKField, TranslatableSerializerMixin

from .models import MediaGallery, MediaItem, MediaItemCrop


class MediaItemCropSerializer(serializers.ModelSerializer):
    """
    Represents a named crop variant of a MediaItem.

    ``image_url`` is a read-only computed field that returns the publicly
    accessible URL of the stored image file. It is derived from the
    ``image`` ImageField via Django's storage backend so the URL stays
    correct regardless of which storage backend is configured (local,
    S3, etc.).

    Read-only - crops are managed via the scraper sync pipeline.
    """

    image_url = serializers.SerializerMethodField(
        help_text="Publicly accessible URL of the cropped asset.",
    )

    class Meta:
        model = MediaItemCrop
        fields = [
            "id",
            "name",
            "image_url",
        ]
        read_only_fields = ["id", "image_url"]
        extra_kwargs = {
            "name": {
                "help_text": "Crop variant identifier (e.g. `hd_ready`, `FE3_header`).",
            },
        }

    def get_image_url(self, obj: MediaItemCrop) -> str | None:
        """Return the storage URL of the crop image, or None if no image is stored."""
        if obj.image:
            request = self.context.get("request")
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class MediaGalleryReferenceSerializer(serializers.ModelSerializer):
    """Lightweight nested representation used for FK expansion."""

    class Meta:
        model = MediaGallery
        fields = ["id", "name"]


class MediaItemSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """
    Represents a MediaItem with its translated metadata and nested crops.

    Translated fields (`title`, `description`, `credits`, `link`) return all
    available translations as dictionaries (e.g. {"en": "Poster", "fr": "Affiche"}).
    All translated fields are read-only - use the Media Item Translation
    endpoints to manage them.

    Nested `crops` is a read-only list of all pre-rendered crop variants.
    """

    title = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the title "
            '(e.g. {"en": "Poster", "fr": "Affiche"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    display_title = serializers.SerializerMethodField(
        help_text=(
            "Title in the project's base language (derived from settings.LANGUAGE_CODE). "
            "Falls back to the first available translation when missing."
        )
    )

    description = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the description "
            '(e.g. {"en": "Event poster", "fr": "Affiche de l\'événement"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    credits = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the credits string "
            '(e.g. {"en": "Photo by John Doe", "fr": "Photo par John Doe"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    link = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the external URL "
            '(e.g. {"en": "https://example.com/en", '
            '"fr": "https://example.com/fr"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    crops = MediaItemCropSerializer(many=True, read_only=True)
    gallery = NestedRepresentationPKField(
        queryset=MediaGallery.objects.all(),
        serializer_class=MediaGalleryReferenceSerializer,
        allow_null=True,
        required=False,
        help_text="Primary key of the parent **MediaGallery** this item belongs to.",
    )

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
            "display_title",
            "description",
            "credits",
            "link",
            "crops",
        ]
        read_only_fields = [
            "id",
            "display_title",
            "title",
            "description",
            "credits",
            "link",
            "crops",
        ]
        extra_kwargs = {
            "type": {
                "help_text": "Media type: `foto`, `video`, `audio`, or `other`.",
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

    def get_title(self, obj: MediaItem) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "title")

    def get_display_title(self, obj: MediaItem) -> str | None:
        """Return the media item title in the project's base language."""
        return self.get_base_translated_value(obj, "title")

    def get_description(self, obj: MediaItem) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "description")

    def get_credits(self, obj: MediaItem) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "credits")

    def get_link(self, obj: MediaItem) -> dict[str, str] | None:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "link")


class MediaGallerySerializer(serializers.ModelSerializer):
    """
    Represents a MediaGallery with its nested media items.

    The `media_items` field is a read-only nested list of all items in the
    gallery, ordered by `position`. Each item includes its translated metadata
    represented as language-code dictionaries and crop variants.
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
