"""Serializers for the Language app.

Field-level `help_text` and `extra_kwargs` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do
not need to be repeated inside the schema decorators.
"""

from rest_framework import serializers

from .models import Language


class LanguageSerializer(serializers.ModelSerializer):
    """Represents a Language object.

    All fields are exposed.
    """

    class Meta:
        model = Language
        fields = [
            "code",
            "name",
            "is_active",
        ]
        extra_kwargs = {
            "code": {
                "help_text": "ISO 639-1 two-letter code (e.g. `en`, `nl`, `fr`). Used as the URL lookup key.",
            },
            "name": {
                "help_text": "Human-readable English name of the language (e.g. `English`, `Dutch`).",
            },
            "is_active": {
                "help_text": (
                    "Controls visibility in consumer-facing interfaces. "
                    "Set to `false` while translations are still being prepared."
                ),
            },
        }
