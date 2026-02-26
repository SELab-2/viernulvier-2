from rest_framework import serializers
from apps.core.serializers import TranslatableSerializerMixin
from .models import MediaGallery, MediaItem, MediaItemCrop


class MediaItemCropSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaItemCrop
        fields = [
            "id",
            "name",
            "url",
        ]


class MediaItemSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """
    Public representation of a MediaItem.

    Fully optimized to prevent N+1 queries.
    Includes translated fields and nested crops.
    """

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    credits = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()

    crops = MediaItemCropSerializer(many=True, read_only=True)

    class Meta:
        model = MediaItem
        fields = [
            "id",
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

    def get_title(self, obj):
        return self.get_translated_field(obj, "title")

    def get_description(self, obj):
        return self.get_translated_field(obj, "description")

    def get_credits(self, obj):
        return self.get_translated_field(obj, "credits")

    def get_link(self, obj):
        return self.get_translated_field(obj, "link")


class MediaGallerySerializer(serializers.ModelSerializer):
    """
    Public representation of a MediaGallery.

    Fully optimized to prevent N+1 queries.
    Includes nested media items ordered by position.
    """

    media_items = MediaItemSerializer(many=True, read_only=True)

    class Meta:
        model = MediaGallery
        fields = [
            "id",
            "name",
            "media_items",
        ]