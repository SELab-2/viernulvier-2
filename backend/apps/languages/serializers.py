from rest_framework import serializers
from .models import Language


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "code",
            "name",
            "is_active"
        ]
        read_only_fields = fields