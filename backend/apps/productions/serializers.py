"""
Serializers for the Productions app.

Field-level ``help_text`` and ``extra_kwargs`` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do not
need to be repeated inside the schema decorators.

Translatable fields on ``ProductionSerializer`` are resolved via
``TranslatableSerializerMixin`` using the ``Accept-Language`` request header.

Nested relations
----------------
- ``UitDatabaseThemeSerializer`` / ``UitDatabaseTypeSerializer`` — simple
  read-only nested representations of the classification FK targets.
- ``GenreSerializer`` — nested per production, ordered by ``position``.
- ``TagSerializer`` — nested many-to-many, carries its own localised fields.
"""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from apps.tags.serializers import TagSerializer
from apps.genres.serializers import GenreSerializer
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

    Translatable fields
    -------------------
    The following fields are resolved from the production's translation table
    based on the ``Accept-Language`` request header:

    - ``title``
    - ``artist_name``
    - ``tagline``
    - ``teaser``
    - ``description``

    All translatable fields are read-only. Use the **Production Translation**
    endpoints to manage translations.

    Nested relations
    ----------------
    - ``uit_database_theme`` / ``uit_database_type`` — nested FK objects.
    - ``tags`` — many-to-many, serialised with ``TagSerializer`` (includes
      localised tag fields).
    - ``genres`` — ordered by ``position`` via ``ProductionGenre.position``.
      Uses ``prefetched_production_genres`` when available to avoid extra
      queries; falls back to a direct queryset call otherwise.
    """

    # ---------------------------------------------------------------------------
    # Translatable fields (resolved via Accept-Language)
    # ---------------------------------------------------------------------------

    title = serializers.SerializerMethodField(
        help_text=(
            "Localised production title resolved via the `Accept-Language` header. "
            "Empty string when no translation exists for the resolved language. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    artist_name = serializers.SerializerMethodField(
        help_text=(
            "Localised artist or company name resolved via the `Accept-Language` header. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    tagline = serializers.SerializerMethodField(
        help_text=(
            "Localised short tagline resolved via the `Accept-Language` header. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    teaser = serializers.SerializerMethodField(
        help_text=(
            "Localised teaser text resolved via the `Accept-Language` header. "
            "Read-only — use the translation endpoints to manage translations."
        ),
    )

    description = serializers.SerializerMethodField(
        help_text=(
            "Localised long-form description resolved via the `Accept-Language` header. "
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
                "help_text": (
                    "How the audience attends the production. "
                    "Accepted values: `offline`, `online`."
                ),
            },
            "performer_type": {
                "help_text": (
                    "Whether the performance is by a group or a solo artist. "
                    "Accepted values: `group`, `solo`."
                ),
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
        """Resolve the localised title via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "title")

    def get_artist_name(self, obj: Production) -> str:
        """Resolve the localised artist name via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "artist_name")

    def get_tagline(self, obj: Production) -> str:
        """Resolve the localised tagline via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "tagline")

    def get_teaser(self, obj: Production) -> str:
        """Resolve the localised teaser via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "teaser")

    def get_description(self, obj: Production) -> str:
        """Resolve the localised description via TranslatableSerializerMixin."""
        return self.get_translated_field(obj, "description")