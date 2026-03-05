"""
Serializers for the Productions app.

Field-level ``help_text`` and ``extra_kwargs`` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do not
need to be repeated inside the schema decorators.

Translatable fields on ``ProductionSerializer`` return all available
translations as language-code dictionaries
(e.g. {"en": "Title", "fr": "Titre"}).

Nested relations
----------------
- ``UitDatabaseThemeSerializer`` / ``UitDatabaseTypeSerializer`` — simple
  read-only nested representations of the classification FK targets.
- ``GenreSerializer`` — nested per production, ordered by ``position``.
- ``TagSerializer`` — nested many-to-many, carries its own translated fields.
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from apps.genres.serializers import GenreSerializer
from apps.tags.serializers import TagSerializer

from .models import Production, UitDatabaseTheme, UitDatabaseType


class UitDatabaseThemeSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a UIT Database Theme.

    Used as a nested field inside ``ProductionSerializer``.
    """

    class Meta:
        model = UitDatabaseTheme
        fields = ["id", "name"]


class UitDatabaseTypeSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a UIT Database Type.

    Used as a nested field inside ``ProductionSerializer``.
    """

    class Meta:
        model = UitDatabaseType
        fields = ["id", "name"]


class ProductionSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """
    Full representation of a Production.

    Translated fields
    -----------------
    The following fields return all available translations as
    language-code dictionaries:

    - ``title``
    - ``artist_name``
    - ``tagline``
    - ``teaser``
    - ``description``

    All translated fields are read-only. Use the **Production Translation**
    endpoints to manage translations.

    Nested relations
    ----------------
    - ``uit_database_theme`` / ``uit_database_type`` — nested FK objects.
    - ``tags`` — many-to-many, serialised with ``TagSerializer``.
    - ``genres`` — ordered by ``position`` via ``ProductionGenre.position``.
    """

    # ---------------------------------------------------------------------------
    # Translatable fields
    # ---------------------------------------------------------------------------

    title = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the production title "
            '(e.g. {"en": "Title", "fr": "Titre"}). '
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    artist_name = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the artist or company name "
            '(e.g. {"en": "Artist", "fr": "Artiste"}). '
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    tagline = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the short tagline "
            '(e.g. {"en": "Short tagline", "fr": "Accroche courte"}). '
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    teaser = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the teaser text "
            '(e.g. {"en": "Teaser", "fr": "Teaser"}). '
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    description = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the long-form description "
            '(e.g. {"en": "Full description", "fr": "Description complète"}). '
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    # ---------------------------------------------------------------------------
    # Nested relations (read-only)
    # ---------------------------------------------------------------------------

    uit_database_theme = UitDatabaseThemeSerializer(
        read_only=True,
        help_text="Nested UIT Database Theme classification. `null` when not assigned.",
    )

    uit_database_type = UitDatabaseTypeSerializer(
        read_only=True,
        help_text="Nested UIT Database Type classification. `null` when not assigned.",
    )

    tags = TagSerializer(
        many=True,
        read_only=True,
        help_text="Tags attached to this production, each with localised fields.",
    )

    genres = serializers.SerializerMethodField(
        help_text=(
            "Genres attached to this production, ordered by their configured `position`. "
            "Read-only — use the genre endpoints to manage genre assignments."
        ),
    )

    class Meta:
        model = Production
        fields = [
            "id",
            "attendance_mode",
            "performer_type",
            "uit_database_theme",
            "uit_database_type",
            "title",
            "artist_name",
            "tagline",
            "teaser",
            "description",
            "tags",
            "genres",
        ]
        read_only_fields = [
            "id",
            "uit_database_theme",
            "uit_database_type",
            "title",
            "artist_name",
            "tagline",
            "teaser",
            "description",
            "tags",
            "genres",
        ]
        extra_kwargs = {
            "attendance_mode": {
                "help_text": ("How the audience attends the production. Accepted values: `offline`, `online`."),
            },
            "performer_type": {
                "help_text": ("Whether the performance is by a group or a solo artist. Accepted values: `group`, `solo`."),
            },
        }

    # ---------------------------------------------------------------------------
    # SerializerMethodField implementations
    # ---------------------------------------------------------------------------

    def get_genres(self, obj: Production) -> list:
        """
        Return serialised genres in correct position order.

        Reads from ``obj.prefetched_production_genres`` when the viewset has
        used an explicit ``Prefetch`` with ``to_attr``; falls back to a live
        queryset call to avoid silently returning an empty list.
        """
        production_genres = getattr(obj, "prefetched_production_genres", None)

        if production_genres is not None:
            genres = [pg.genre for pg in production_genres]
        else:
            # Fallback — will trigger an additional query per production.
            genres = obj.genres.all().order_by("productiongenre__position")

        return GenreSerializer(genres, many=True).data

    def get_title(self, obj: Production) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "title")

    def get_artist_name(self, obj: Production) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "artist_name")

    def get_tagline(self, obj: Production) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "tagline")

    def get_teaser(self, obj: Production) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "teaser")

    def get_description(self, obj: Production) -> str:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "description")
