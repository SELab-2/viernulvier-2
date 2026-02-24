from rest_framework import serializers
from apps.pricing.models import Price, PriceTranslation
from apps.languages.models import Language


class PriceTranslationSerializer(serializers.ModelSerializer):
    """Serializer for PriceTranslation model."""
    language = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.all(),
    )

    class Meta:
        model = PriceTranslation
        fields = [
            "id", 
            "price", 
            "language", 
            "description"
        ]
        read_only_fields = ["id"] # TODO: maybe add more read-only fields

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=PriceTranslation.objects.all(),
                fields=["price", "language"],
            )
        ]


class PriceSerializer(serializers.ModelSerializer):
    """Serializer for Price model."""
    translations = PriceTranslationSerializer(many=True, read_only=True)
    description = serializers.SerializerMethodField()

    class Meta:
        model = Price
        fields = [
            "id",
            "type",
            "visibility",
            "membership",
            "minimum",
            "maximum",
            "step",
            "sort_order",
            "cineville_box",
            "description",
            "translations"
        ]
        read_only_fields = ["id"] # TODO: maybe add more read-only fields

    def get_description(self, obj) -> str:
        """Retrieve the price's description in the requested language (if given)."""
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        qs = obj.translations.all()

        if lang:
            match = next((t for t in qs if t.language_id == lang and t.description), None)
            if match:
                return match.description

        first = next((t for t in qs if t.description), None)
        return first.description if first else ""