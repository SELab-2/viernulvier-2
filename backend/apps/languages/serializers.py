from rest_framework import serializers

from .models import Language


class LanguageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Language model.

    All fields are exposed.
    """

    class Meta:
        model = Language
        fields = [
            "code",
            "name",
            "is_active",
        ]