from rest_framework import serializers
from apps.core.serializers import TranslatableSerializerMixin
from .models import Tag


class TagSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """
    Public representation of Tag.
    Translations are nested per field.
    """

    name = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()
    url_title = serializers.SerializerMethodField()

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

    def get_name(self, obj):
        return self.get_translated_field(obj, "name")

    def get_short_description(self, obj):
        return self.get_translated_field(obj, "short_description")

    def get_url_title(self, obj):
        return self.get_translated_field(obj, "url_title")