"""Serializers for the Blog app."""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from apps.languages.models import Language
from apps.productions.models import Production
from apps.productions.serializers import ProductionSerializer

from .models import Blog, BlogTranslation


class BlogTranslationInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for creating/updating blog translations."""

    language_id = serializers.IntegerField(
        source="language.id",
        help_text="Language ID for this translation",
    )

    class Meta:
        model = BlogTranslation
        fields = ["language_id", "title", "body", "excerpt"]


class BlogSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Represents a Blog post.

    The `title`, `body`, and `excerpt` fields contain all available translations
    as dictionaries, for example: {"en": "Title", "nl": "Titel"}.

    Linked productions are returned as full nested production objects.
    """

    title = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the blog title, "
            'e.g. {"en": "I Love Techno 2024", "nl": "I Love Techno 2024"}. '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    body = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the blog body content, "
            'e.g. {"en": "Full article...", "nl": "Volledig artikel..."}. '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    excerpt = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the blog excerpt, "
            'e.g. {"en": "Short summary...", "nl": "Korte samenvatting..."}. '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    display_title = serializers.SerializerMethodField(
        help_text=(
            "Human-readable title in the project's base language. "
            "Falls back to the first available translation when the base language is missing."
        )
    )

    display_excerpt = serializers.SerializerMethodField(
        help_text=(
            "Human-readable excerpt in the project's base language. "
            "Falls back to the first available translation when the base language is missing."
        )
    )

    production_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        source="productions",
        queryset=Production.objects.all(),
        required=False,
        write_only=True,
        help_text="List of production IDs to link to this blog post (write-only).",
    )

    productions = ProductionSerializer(many=True, read_only=True, help_text="List of linked production objects (read-only).")

    translations_data = BlogTranslationInlineSerializer(
        many=True,
        required=False,
        write_only=True,
        help_text="List of translations to create/update inline (write-only).",
    )

    class Meta:
        model = Blog
        fields = [
            "id",
            "slug",
            "published_at",
            "cover_image",
            "title",
            "body",
            "excerpt",
            "display_title",
            "display_excerpt",
            "productions",
            "production_ids",
            "translations_data",
        ]
        read_only_fields = [
            "id",
            "title",
            "body",
            "excerpt",
            "display_title",
            "display_excerpt",
            "productions",
        ]
        extra_kwargs = {
            "slug": {
                "help_text": ("URL-friendly identifier in `kebab-case` (e.g. `i-love-techno-2024`, `vooruit-100-years`)."),
            },
            "published_at": {
                "help_text": ("Publication timestamp (ISO 8601 format). If null, the post is considered a draft."),
            },
            "cover_image": {
                "help_text": (
                    "Upload a cover image for this blog post. Accepts an image file or a URL to an existing image."
                ),
            },
        }

    def get_title(self, obj: Blog) -> dict[str, str] | None:
        """Return all available title translations as a language-code dictionary."""
        return self.get_translated_field(obj, "title")

    def get_body(self, obj: Blog) -> dict[str, str] | None:
        """Return all available body translations as a language-code dictionary."""
        return self.get_translated_field(obj, "body")

    def get_excerpt(self, obj: Blog) -> dict[str, str] | None:
        """Return all available excerpt translations as a language-code dictionary."""
        return self.get_translated_field(obj, "excerpt")

    def get_display_title(self, obj: Blog) -> str | None:
        """Return the blog title in the project's base language."""
        return self.get_base_translated_value(obj, "title")

    def get_display_excerpt(self, obj: Blog) -> str | None:
        """Return the blog excerpt in the project's base language."""
        return self.get_base_translated_value(obj, "excerpt")

    def create(self, validated_data: dict) -> Blog:
        """Create a blog with inline translations."""
        translations_data = validated_data.pop("translations_data", [])
        blog = super().create(validated_data)

        # Create translations
        self._create_translations(blog, translations_data)

        return blog

    def update(self, instance: Blog, validated_data: dict) -> Blog:
        """Update a blog and optionally update/replace translations."""
        translations_data = validated_data.pop("translations_data", None)
        blog = super().update(instance, validated_data)

        # If translations_data is provided, replace all translations
        if translations_data is not None:
            blog.translations.all().delete()
            self._create_translations(blog, translations_data)

        return blog

    def _create_translations(self, blog: Blog, translations_data: list[dict]) -> None:
        """Helper method to create translations for a blog."""
        for trans_data in translations_data:
            language_id = trans_data.pop("language")["id"]
            language = Language.objects.get(id=language_id)

            BlogTranslation.objects.create(blog=blog, language=language, **trans_data)
