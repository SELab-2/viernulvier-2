"""Serializers for the Productions app.

Field-level ``help_text`` and ``extra_kwargs`` are picked up automatically
by drf-spectacular and rendered in the Swagger UI, so descriptions do not
need to be repeated inside the schema decorators.

Translatable fields on ``ProductionSerializer`` return all available
translations as language-code dictionaries
(e.g. {"en": "Title", "fr": "Titre"}).

Nested relations
----------------
- ``UitDatabaseTypeSerializer`` - simple read-only nested representation of
    the classification FK target.
- ``GenreSerializer`` - nested per production, ordered by ``position``.
- ``TagSerializer`` - nested many-to-many.
"""

from django.db.models import Exists, OuterRef, Prefetch, Max, Min, QuerySet
from django.db.models.functions import Now
from rest_framework import serializers

from apps.blogs.models import Blog
from apps.core.serializers import TranslatableSerializerMixin
from apps.events.models import Event
from apps.genres.serializers import GenreSerializer
from apps.media_library.models import MediaItem
from apps.media_library.serializers import MediaGallerySerializer
from apps.tags.models import Tag
from apps.tags.serializers import TagSerializer

from .models import Production, ProductionGenre, UitDatabaseType


class ProductionLandingStatsSerializer(serializers.Serializer):
    """Compact payload for homepage archive counters."""

    productions = serializers.IntegerField(min_value=0)
    series = serializers.IntegerField(min_value=0)
    years = serializers.IntegerField(min_value=0)
    blogs = serializers.IntegerField(min_value=0)


class UitDatabaseTypeSerializer(serializers.ModelSerializer):
    """Read-only representation of a UIT Database Type.

    Used as a nested field inside ``ProductionSerializer``.
    """

    class Meta:
        model = UitDatabaseType
        fields = ["id", "name"]


class RelatedTagSerializer(TagSerializer):
    """Compact tag representation for related production groupings."""

    class Meta(TagSerializer.Meta):
        fields = ["id", "name", "display_name"]
        read_only_fields = fields


class ProductionRelatedBlogSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Compact blog representation for `ProductionSerializer.blogs`."""

    title = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the blog title, "
            'e.g. {"en": "I Love Techno 2024", "nl": "I Love Techno 2024"}. '
            "Read-only."
        ),
    )

    excerpt = serializers.SerializerMethodField(
        help_text=(
            "Dictionary containing all available translations of the blog excerpt, "
            'e.g. {"en": "Short summary...", "nl": "Korte samenvatting..."}. '
            "Read-only."
        ),
    )

    display_title = serializers.SerializerMethodField(
        help_text=(
            "Human-readable title in the project's base language. "
            "Falls back to the first available translation when missing."
        )
    )

    display_excerpt = serializers.SerializerMethodField(
        help_text=(
            "Human-readable excerpt in the project's base language. "
            "Falls back to the first available translation when missing."
        )
    )

    class Meta:
        model = Blog
        fields = [
            "id",
            "slug",
            "published_at",
            "cover_image",
            "title",
            "excerpt",
            "display_title",
            "display_excerpt",
        ]
        read_only_fields = fields

    def get_title(self, obj: Blog) -> dict[str, str] | None:
        """Return all available title translations as a language-code dictionary."""
        return self.get_translated_field(obj, "title")

    def get_excerpt(self, obj: Blog) -> dict[str, str] | None:
        """Return all available excerpt translations as a language-code dictionary."""
        return self.get_translated_field(obj, "excerpt")

    def get_display_title(self, obj: Blog) -> str | None:
        """Return the blog title in the project's base language."""
        return self.get_base_translated_value(obj, "title")

    def get_display_excerpt(self, obj: Blog) -> str | None:
        """Return the blog excerpt in the project's base language."""
        return self.get_base_translated_value(obj, "excerpt")


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
    - ``uit_database_type`` - nested FK object.
    - ``tags`` - many-to-many, serialised with ``TagSerializer``.
    - ``genres`` - ordered by ``position`` via ``ProductionGenre.position``.
    """

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

    video_1 = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the primary video URL "
            '(e.g. {"en": "https://...", "nl": "https://..."}). '
            "Read-only."
        ),
    )

    video_2 = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available translations for the secondary video URL "
            '(e.g. {"en": "https://...", "nl": "https://..."}). '
            "Read-only."
        ),
    )

    description = serializers.SerializerMethodField(
        help_text="Production description in all available translations.",
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

    uit_database_type = UitDatabaseTypeSerializer(
        read_only=True,
        help_text="Nested UIT Database Type classification. `null` when not assigned.",
    )

    tags = serializers.SerializerMethodField(help_text="Tags attached to this production, each with localised fields.")

    genres = serializers.SerializerMethodField(
        help_text=(
            "Genres attached to this production, ordered by their configured `position`. "
            "Read-only - use the genre endpoints to manage genre assignments."
        ),
    )

    events = serializers.SerializerMethodField(
        help_text=(
            "List of events that are performances of this production. "
            "Only shown if `events` is passed to the `include` query parameter."
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

    blogs = serializers.SerializerMethodField(
        help_text=(
            "Published blogs linked to this production. Only present when `include=blogs` "
            "is passed to the production detail endpoint."
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
            "uit_database_type",
            "display_title",
            "display_artist_name",
            "title",
            "artist_name",
            "tagline",
            "teaser",
            "description",
            "video_1",
            "video_2",
            "tags",
            "genres",
            "events",
            "related",
            "blogs",
        ]
        read_only_fields = [
            "id",
            "first_event_start",
            "last_event_end",
            "uit_database_type",
            "display_title",
            "display_artist_name",
            "title",
            "artist_name",
            "tagline",
            "teaser",
            "description",
            "video_1",
            "video_2",
            "tags",
            "genres",
            "events",
            "related",
            "blogs",
        ]
        extra_kwargs = {
            "attendance_mode": {
                "help_text": "How the audience attends the production. Accepted values: `offline`, `online`.",
            },
            "performer_type": {
                "help_text": "Whether the performance is by a group or a solo artist. Accepted values: `group`, `solo`.",
            },
            "media_gallery": {
                "help_text": "PK of the associated MediaGallery. `null` when no gallery is assigned.",
            },
        }

    def get_genres(self, obj: Production) -> list:
        """Return serialised genres in correct position order."""
        production_genres = getattr(obj, "prefetched_production_genres", None)

        if production_genres is not None:
            genres = [pg.genre for pg in production_genres]
        else:
            genres = obj.genres.all().order_by("productiongenre__position")

        return GenreSerializer(genres, many=True).data

    def get_title(self, obj: Production) -> dict:
        """Return all available translations for the title as a language-code dictionary."""
        return self.get_translated_field(obj, "title")

    def get_artist_name(self, obj: Production) -> dict:
        """Return all available translations for the artist name as a language-code dictionary."""
        return self.get_translated_field(obj, "artist_name")

    def get_tagline(self, obj: Production) -> dict:
        """Return all available translations for the tagline as a language-code dictionary."""
        return self.get_translated_field(obj, "tagline")

    def get_teaser(self, obj: Production) -> dict:
        """Return all available translations for the teaser as a language-code dictionary."""
        return self.get_translated_field(obj, "teaser")

    def get_description(self, obj: Production) -> dict:
        """Return all available translations for the description as a language-code dictionary."""
        return self.get_translated_field(obj, "description")

    def get_video_1(self, obj: Production) -> dict[str, str] | None:
        """Return all available translations for `video_1` as a language-code dict."""
        return self.get_translated_field(obj, "video_1")

    def get_video_2(self, obj: Production) -> dict[str, str] | None:
        """Return all available translations for `video_2` as a language-code dict."""
        return self.get_translated_field(obj, "video_2")

    def get_display_title(self, obj: Production) -> str | None:
        """Return the title in the project's base language, falling back to the first available translation."""
        return self.get_base_translated_value(obj, field_name="title")

    def get_display_artist_name(self, obj: Production) -> str | None:
        """Return the artist name in the project's base language, falling back to the first available translation."""
        return self.get_base_translated_value(obj, field_name="artist_name")

    def get_tags(self, obj: Production) -> list:
        """Return serialised tags, from prefetch or fallback query."""
        tags = getattr(obj, "prefetched_tags", None)

        if tags is None:
            tags = obj.tags.prefetch_related("translations__language").order_by("type", "id")

        return TagSerializer(tags, many=True).data

    def _get_related_productions_qs(self, tag: Tag, exclude_id: int) -> QuerySet[Production]:
        """Return a queryset of productions sharing the given tag, excluding the current production."""
        return (
            Production.objects.filter(tags=tag)
            .exclude(id=exclude_id)
            .select_related("uit_database_type", "media_gallery")
            .prefetch_related(
                "translations__language",
                Prefetch(
                    "productiongenre_set",
                    queryset=ProductionGenre.objects.select_related("genre").order_by("position"),
                    to_attr="prefetched_production_genres",
                ),
                Prefetch(
                    "tags",
                    queryset=Tag.objects.prefetch_related("translations__language").order_by("type", "id"),
                    to_attr="prefetched_tags",
                ),
                Prefetch(
                    "media_gallery__media_items",
                    queryset=MediaItem.objects.prefetch_related("translations__language", "crops").order_by("position"),
                ),
            )
            .annotate(
                first_event_start=Min("events__starts_at"),
                last_event_end=Max("events__ends_at"),
            )
        )

    def get_related(self, obj: Production) -> list | None:
        """Return related productions grouped by the tags on this production."""
        if "related" not in self.context.get("include", set()):
            return None

        tags = getattr(obj, "prefetched_tags", None) or list(
            obj.tags.prefetch_related("translations__language").order_by("type", "id")
        )

        if not tags:
            return []

        return [
            {
                "tag": RelatedTagSerializer(tag, context=self.context).data,
                "productions": RelatedProductionSerializer(
                    self._get_related_productions_qs(tag, obj.id),
                    many=True,
                    context=self.context,
                ).data,
            }
            for tag in tags
        ]

    def get_events(self, obj: Production) -> list | None:
        """Return events for this production if included in the serializer context."""
        if "events" not in self.context.get("include", set()):
            return None

        from apps.events.serializers import NestedEventSerializer  # noqa: PLC0415

        events = getattr(obj, "prefetched_past_events", None)
        if events is None:
            events = obj.events.filter(ends_at__lte=Now())
        return NestedEventSerializer(events, many=True).data

    def get_blogs(self, obj: Production) -> list | None:
        """Return published blogs linked to this production when requested."""
        if "blogs" not in self.context.get("include", set()):
            return None

        blogs = getattr(obj, "prefetched_related_blogs", None)

        return ProductionRelatedBlogSerializer(blogs, many=True, context=self.context).data

    def to_representation(self, instance: Production) -> dict:
        """Conditionally strip ``events`` and ``related`` when not requested."""
        rep = super().to_representation(instance)
        if "events" not in self.context.get("include", set()):
            rep.pop("events", None)
        if "related" not in self.context.get("include", set()):
            rep.pop("related", None)
        if "blogs" not in self.context.get("include", set()):
            rep.pop("blogs", None)
        return rep


class RelatedProductionSerializer(ProductionSerializer):
    """Compact representation used inside ``ProductionSerializer.related``."""

    class Meta(ProductionSerializer.Meta):
        fields = [
            "id",
            "title",
            "display_title",
            "media_gallery",
            "first_event_start",
            "last_event_end",
            "tags",
            "genres",
        ]
        read_only_fields = fields
