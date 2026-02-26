from rest_framework import serializers
from apps.pricing.models import Price, PriceRank, PriceTranslation
from apps.core.serializers import TranslatableSerializerMixin


class PriceTranslationSerializer(serializers.ModelSerializer):
    language = serializers.CharField(source="language.code", read_only=True)

    class Meta:
        model = PriceTranslation
        fields = ["id", "language", "description"]
        read_only_fields = fields


class PriceSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Serializer for Price model."""
    description = serializers.SerializerMethodField()
    translations = PriceTranslationSerializer(many=True, read_only=True)

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
            "translations",
        ]
        read_only_fields = ["id", "translations", "description"]

    def get_translated_field(self, obj, field_name: str) -> str:
        """
        Return a translated value for the given field name.

        The method resolves translations in the following order:

        1. If a `lang` query parameter is present in the request context,
        return the value for that language (only if non-empty).
        2. Otherwise, return the first non-empty translation available.
        3. If no translations exist or all values are empty, return an empty string.
        """
        request = self.context.get("request")

        lang = None
        if request is not None:
            if hasattr(request, "query_params"):
                lang = request.query_params.get("lang")
            elif hasattr(request, "GET"):
                lang = request.GET.get("lang")

        translations = getattr(obj, "translations", None)
        if translations is None:
            return ""

        try:
            translations_qs = translations.all()
        except Exception:
            translations_qs = translations

        if lang:
            for t in translations_qs:
                if getattr(t.language, "code", None) == lang:
                    value = getattr(t, field_name, "") or ""
                    if value.strip():
                        return value

        for t in translations_qs:
            value = getattr(t, field_name, "") or ""
            if value.strip():
                return value

        return ""

    def get_description(self, obj) -> str:
        """Retrieve the price's description in the requested language (if given)."""
        return self.get_translated_field(obj, "description")


class PriceRankSerializer(serializers.ModelSerializer):
    """Serializer for PriceRank model."""
    class Meta:
        model = PriceRank
        fields = [
            "id",
            "position",
            "sold_out_buffer"
        ]
        read_only_fields = ["id"]