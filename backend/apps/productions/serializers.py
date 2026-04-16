"""Serializers for the Productions app.

Field-level ``help_text`` and ``extra_kwargs`` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do not
need to be repeated inside the schema decorators.

Translatable fields on ``ProductionSerializer`` return all available
translations as language-code dictionaries
(e.g. {"en": "Title", "fr": "Titre"}).

Nested relations
----------------
- ``UitDatabaseThemeSerializer`` / ``UitDatabaseTypeSerializer`` - simple
  read-only nested representations of the classification FK targets.
- ``GenreSerializer`` - nested per production, ordered by ``position``.
- ``TagSerializer`` - nested many-to-many, carries its own translated fields.
"""

from django.db.models import Prefetch
from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from apps.genres.serializers import GenreSerializer
from apps.media_library.models import MediaItem
from apps.media_library.serializers import MediaGallerySerializer
from apps.tags.models import Tag
from apps.tags.serializers import TagSerializer

from .models import Production, ProductionTag, UitDatabaseTheme, UitDatabaseType


class ProductionSeriesSerializer(serializers.ModelSerializer):
    """Aggregated series summary grouped by production tag.

    The serializer is used by the `/productions/series/` endpoint, where each
    item represents one production tag bundle with derived start/end boundaries.
    """

    tag = TagSerializer(source="*", read_only=True)
    first_production_start = serializers.DateTimeField(read_only=True, allow_null=True)
    last_production_end = serializers.DateTimeField(read_only=True, allow_null=True)
    last_production_image = serializers.SerializerMethodField(
        help_text=(
            "Absolute or relative URL of the first crop image of the most recent "
            "production in this series. `null` when no image is available."
        ),
    )

    class Meta:
        model = Tag
        fields = [
            "tag",
            "first_production_start",
            "last_production_end",
            "last_production_image",
        ]
        read_only_fields = fields

    def get_last_production_image(self, obj: Tag) -> str | None:
        """Resolve the image URL from the precomputed production-id lookup map."""
        production_id = getattr(obj, "last_production_id", None)
        if production_id is None:
            return None

        lookup = self.context.get("last_production_image_by_production_id", {})
        return lookup.get(production_id)


class UitDatabaseThemeSerializer(serializers.ModelSerializer):
    """Read-only representation of a UIT Database Theme.

    Used as a nested field inside ``ProductionSerializer``.
    """

    class Meta:
        model = UitDatabaseTheme
        fields = ["id", "name"]


class UitDatabaseTypeSerializer(serializers.ModelSerializer):
    """Read-only representation of a UIT Database Type.

    Used as a nested field inside ``ProductionSerializer``.
    """

    class Meta:
        model = UitDatabaseType
        fields = ["id", "name"]


class ProductionTagSerializer(serializers.ModelSerializer):
    """Serializes a ProductionTag through-table record.

    Exposes all ``Tag`` fields (delegated to ``TagSerializer``) plus a
    ``description`` dictionary carrying all available translations of the
    per-production-tag description.

    The ``description`` field returns translations as a language-code dict
    (e.g. ``{"nl": "...", "en": "..."}``) consistent with the pattern used
    by ``TranslatableSerializerMixin`` on other models.

    Queryset strategy
    -----------------
    Expects ``obj.translations`` to be pre-fetched with ``select_related("language")``
    to avoid N+1 queries. When the viewset uses ``to_attr="prefetched_production_tags"``
    the inline ``get_queryset`` should include
    ``.prefetch_related("translations__language")``.
    """

    description = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the tag description "
            'within this production (e.g. {"nl": "...", "en": "..."}). '
            "Empty dict when no descriptions have been added."
        ),
    )

    class Meta:
        model = ProductionTag
        fields = ["description"]

    def to_representation(self, instance: ProductionTag) -> dict:
        """Merge the full Tag representation with this through-table's own fields.

        Tag fields always come first so the shape is backward-compatible with
        the previous ``TagSerializer``-only output.
        """
        tag_data = TagSerializer(instance.tag).data
        own_data = super().to_representation(instance)
        return {**tag_data, **own_data}

    def get_description(self, obj: ProductionTag) -> dict:
        """Return all available translations as a language-code dictionary."""
        return {translation.language.code: translation.description for translation in obj.translations.all()}


class RelatedTagSerializer(TagSerializer):
    """Compact tag representation for related production groupings."""

    class Meta(TagSerializer.Meta):
        fields = ["id", "name", "display_name"]
        read_only_fields = fields


class ProductionSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Full representation of a Production.

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
    - ``uit_database_theme`` / ``uit_database_type`` - nested FK objects.
    - ``tags`` - many-to-many, serialised with ``TagSerializer``.
    - ``genres`` - ordered by ``position`` via ``ProductionGenre.position``.
    """

    # ---------------------------------------------------------------------------
    # Translatable fields
    # ---------------------------------------------------------------------------

    title = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the production title "
            '(e.g. {"en": "Title", "fr": "Titre"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    first_event_start = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
        help_text="Start time of the earliest event linked to this production (UTC). `null` when no events exist.",
    )

    last_event_end = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
        help_text="End time of the latest event linked to this production (UTC). `null` when no events exist.",
    )

    artist_name = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the artist or company name "
            '(e.g. {"en": "Artist", "fr": "Artiste"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    tagline = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the short tagline "
            '(e.g. {"en": "Short tagline", "fr": "Accroche courte"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    teaser = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the teaser text "
            '(e.g. {"en": "Teaser", "fr": "Teaser"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    description = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the long-form description "
            '(e.g. {"en": "Full description", "fr": "Description complète"}). '
            "Read-only - use the translation endpoints to manage translations."
        ),
    )

    display_title = serializers.SerializerMethodField(
        help_text=(
            "Production title in the project's base language (derived from settings.LANGUAGE_CODE). "
            "Falls back to the first available translation when missing."
        ),
    )

    display_artist_name = serializers.SerializerMethodField(
        help_text=(
            "Artist or company name in the project's base language (derived from settings.LANGUAGE_CODE). "
            "Falls back to the first available translation when missing."
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

    tags = serializers.SerializerMethodField(
        help_text=(
            "Tags attached to this production, each with localised fields and "
            "an optional per-production ``description`` dictionary."
        )
    )

    genres = serializers.SerializerMethodField(
        help_text=(
            "Genres attached to this production, ordered by their configured `position`. "
            "Read-only - use the genre endpoints to manage genre assignments."
        ),
    )

    events = serializers.SerializerMethodField(
        help_text=(
            "List of events that are performances of this production."
            "This is only shown if the request is to a specific production, "
            "and the `events` field is included in the request."
        ),
        read_only=True,
    )

    media_gallery = MediaGallerySerializer(
        read_only=True,
        allow_null=True,
        help_text="Nested MediaGallery with all media items and crops. `null` when no gallery is assigned.",
    )

    related = serializers.SerializerMethodField(
        help_text=(
            "Related productions grouped by tag. Only present when `include=related` is passed "
            "to the production detail endpoint."
        ),
        read_only=True,
    )

    class Meta:
        model = Production
        fields = [
            "id",
            "attendance_mode",
            "performer_type",
            "first_event_start",
            "last_event_end",
            "media_gallery",
            "uit_database_theme",
            "uit_database_type",
            "display_title",
            "display_artist_name",
            "title",
            "artist_name",
            "tagline",
            "teaser",
            "description",
            "tags",
            "genres",
            "events",
            "related",
        ]
        read_only_fields = [
            "id",
            "first_event_start",
            "last_event_end",
            "uit_database_theme",
            "uit_database_type",
            "display_title",
            "display_artist_name",
            "title",
            "artist_name",
            "tagline",
            "teaser",
            "description",
            "tags",
            "genres",
            "events",
            "related",
        ]
        extra_kwargs = {
            "attendance_mode": {
                "help_text": ("How the audience attends the production. Accepted values: `offline`, `online`."),
            },
            "performer_type": {
                "help_text": ("Whether the performance is by a group or a solo artist. Accepted values: `group`, `solo`."),
            },
            "media_gallery": {
                "help_text": "PK of the associated MediaGallery. `null` when no gallery is assigned.",
            },
        }

    # ---------------------------------------------------------------------------
    # SerializerMethodField implementations
    # ---------------------------------------------------------------------------

    def get_genres(self, obj: Production) -> list:
        """Return serialised genres in correct position order.

        Reads from ``obj.prefetched_production_genres`` when the viewset has
        used an explicit ``Prefetch`` with ``to_attr``; falls back to a live
        queryset call to avoid silently returning an empty list.
        """
        production_genres = getattr(obj, "prefetched_production_genres", None)

        if production_genres is not None:
            genres = [pg.genre for pg in production_genres]
        else:
            # Fallback - will trigger an additional query per production.
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

    def get_display_title(self, obj: Production) -> str | None:
        """Return the base-language title (with fallback)."""
        return self.get_base_translated_value(obj, field_name="title")

    def get_display_artist_name(self, obj: Production) -> str | None:
        """Return the base-language artist/company name (with fallback)."""
        return self.get_base_translated_value(obj, field_name="artist_name")

    def get_tags(self, obj: Production) -> list:
        """Return serialised production-tag records in type/id order.

        Reads from ``obj.prefetched_production_tags`` when the viewset has
        used an explicit ``Prefetch`` with ``to_attr``; falls back to a live
        queryset call to avoid silently returning an empty list.
        """
        production_tags = getattr(obj, "prefetched_production_tags", None)

        if production_tags is None:
            # Fallback — will trigger additional queries per production.
            production_tags = (
                obj.productiontag_set.select_related("tag")
                .prefetch_related("translations__language", "tag__translations__language")
                .order_by("tag__type", "id")
            )

        return ProductionTagSerializer(production_tags, many=True).data

    def get_related(self, obj: Production) -> list | None:
        """Return related productions grouped by the tags on this production."""
        if "related" not in self.context.get("include", set()):
            return None

        production_tags = getattr(obj, "prefetched_production_tags", None)
        if production_tags is not None:
            tags = [production_tag.tag for production_tag in production_tags]
        else:
            tags = list(obj.tags.all())

        if not tags:
            return []

        tag_ids = [tag.id for tag in tags]
        related_rows = (
            ProductionTag.objects.filter(tag_id__in=tag_ids)
            .exclude(production_id=obj.id)
            .select_related("production", "production__media_gallery")
            .prefetch_related(
                "production__translations__language",
                Prefetch(
                    "production__media_gallery__media_items",
                    queryset=MediaItem.objects.prefetch_related("translations__language", "crops").order_by("position"),
                ),
            )
            .order_by("tag__type", "id")
        )

        grouped_productions: dict[int, list[Production]] = {tag.id: [] for tag in tags}
        seen_production_ids: dict[int, set[int]] = {tag.id: set() for tag in tags}

        for row in related_rows:
            production = row.production
            if production.id in seen_production_ids[row.tag_id]:
                continue
            grouped_productions[row.tag_id].append(production)
            seen_production_ids[row.tag_id].add(production.id)

        result = []

        for tag in tags:
            result.append(
                {
                    "tag": RelatedTagSerializer(tag, context=self.context).data,
                    "productions": RelatedProductionSerializer(
                        grouped_productions.get(tag.id, []),
                        many=True,
                        context=self.context,
                    ).data,
                },
            )

        return result

    def get_events(self, obj: Production) -> list:
        """Return a list of events for this production, if included in the serializer context."""
        if "events" not in self.context.get("include", set()):
            return None

        # Lazy import, since importing at the top level would cause a circular import between the serializers.
        from apps.events.serializers import NestedEventSerializer  # noqa: PLC0415

        events = obj.events.all()
        return NestedEventSerializer(events, many=True).data

    def to_representation(self, instance: Production) -> dict:
        """Override to conditionally include the `events` field based on the serializer context.

        If the events are not included, the events field is removed from the output instead of being returned as `null`.
        """
        rep = super().to_representation(instance)
        if "events" not in self.context.get("include", set()):
            rep.pop("events", None)
        if "related" not in self.context.get("include", set()):
            rep.pop("related", None)
        return rep


class RelatedProductionSerializer(ProductionSerializer):
    """Compact representation used inside `ProductionSerializer.related`.

    This reuses the same translation and media-gallery wiring as the main
    production serializer, but only exposes the fields needed for related
    cards.
    """

    class Meta(ProductionSerializer.Meta):
        fields = ["id", "title", "display_title", "artist_name", "display_artist_name", "media_gallery"]
        read_only_fields = fields
