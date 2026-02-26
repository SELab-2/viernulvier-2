from rest_framework import serializers
from apps.media_library.models import MediaItemTranslation
from apps.languages.models import Language


class MediaItemTranslationSerializer(serializers.ModelSerializer):
    language = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.all(),
    )

    class Meta:
        model = MediaItemTranslation
        fields = [
            "id",
            "media_item",
            "language",
            "title",
            "description",
            "credits",
            "link",
        ]
        read_only_fields = ["id"]