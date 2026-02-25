from rest_framework import serializers
from apps.core.serializers import TranslatableSerializerMixin
from apps.tags.serializers import TagSerializer
from .models import Production, UitDatabaseTheme, UitDatabaseType

class UitDatabaseThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UitDatabaseTheme
        fields = ['id', 'name']

class UitDatabaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UitDatabaseType
        fields = ['id', 'name']

class ProductionSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """
    Public representation of Production 
    """
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    teaser = serializers.SerializerMethodField()
    artist_name = serializers.SerializerMethodField()
    tagline = serializers.SerializerMethodField()

    tags = TagSerializer(many=True, read_only=True)
    uit_database_theme = UitDatabaseThemeSerializer(read_only=True)
    uit_database_type = UitDatabaseTypeSerializer(read_only=True)

    class Meta:
        model = Production
        fields = [
            "id",
            "attendance_mode",
            "performer_type",
            "uit_database_theme",
            "uit_database_type",
            "title",
            "description",
            "teaser",
            "artist_name",
            "tagline",
            "tags",
        ]

    def get_title(self, obj):
        return self.get_translated_field(obj, "title")

    def get_description(self, obj):
        return self.get_translated_field(obj, "description")

    def get_teaser(self, obj):
        return self.get_translated_field(obj, "teaser")

    def get_artist_name(self, obj):
        return self.get_translated_field(obj, "artist_name")

    def get_tagline(self, obj):
        return self.get_translated_field(obj, "tagline")