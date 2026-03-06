"""
Models for the Productions app.

Productions are the core catalogue entity in the archive. The hierarchy is:

    Production  ->  ProductionTranslation
    Production  ->  ProductionGenre  ->  Genre
    Production  ->  ProductionTag    ->  Tag

- A **Production** is the top-level record representing a performance work.
  It holds structural metadata (attendance mode, performer type) and FK
  references to optional classification objects.
- A **ProductionTranslation** carries all localised text fields (title,
  description, artist name, etc.) for a specific language.
- **ProductionGenre** is the ordered through-table for the M2M relation
  between productions and genres. The ``position`` field controls display order.
- **ProductionTag** is the unordered through-table for the M2M relation
  between productions and tags.
"""

from django.db import models

from apps.core.models import BaseModel
from apps.languages.models import Language
from apps.tags.models import Tag
from apps.genres.models import Genre
from apps.media_library.models import MediaGallery

class UitDatabaseTheme(BaseModel):
    """
    A theme classification imported from the UIT Database.

    UIT Database themes are used to broadly categorise productions
    (e.g. "Theater", "Muziek", "Dans"). They are typically synced from an
    external source and referenced by productions as a read-mostly FK.

    Attributes:
        name: Human-readable name of the theme.
    """

    name = models.CharField(
        max_length=200,
        help_text="Human-readable name of the UIT Database theme (e.g. `Theater`, `Muziek`).",
        db_comment="The name of the theme.",
    )

    class Meta(BaseModel.Meta):
        db_table = "uit_database_theme"
        verbose_name = "UIT Database Theme"
        verbose_name_plural = "UIT Database Themes"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UitDatabaseType(BaseModel):
    """
    A type classification imported from the UIT Database.

    UIT Database types provide a more granular classification than themes
    (e.g. "Voorstelling", "Concert", "Tentoonstelling"). Like themes they
    are read-mostly and synced from an external source.

    Attributes:
        name: Human-readable name of the type.
    """

    name = models.CharField(
        max_length=200,
        help_text="Human-readable name of the UIT Database type (e.g. `Voorstelling`, `Concert`).",
        db_comment="The name of the type.",
    )

    class Meta(BaseModel.Meta):
        db_table = "uit_database_type"
        verbose_name = "UIT Database Type"
        verbose_name_plural = "UIT Database Types"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Production(BaseModel):
    """
    The central catalogue record representing a performance work.

    A production groups one or more :class:`~apps.events.models.Event`
    instances and carries structural metadata. All human-readable text
    (title, description, artist name, etc.) lives in
    :class:`ProductionTranslation` to support multiple languages.

    Attributes:
        uit_database_theme: Optional FK to a UIT Database theme classification.
        uit_database_type:  Optional FK to a UIT Database type classification.
        media_gallery:      Optional FK to the associated media gallery.
        attendance_mode:    How the audience attends — ``offline`` or ``online``.
        performer_type:     Whether the act is a ``group`` or ``solo`` artist.
        genres:             Ordered M2M to :class:`~apps.genres.models.Genre`
                            via :class:`ProductionGenre`.
        tags:               Unordered M2M to :class:`~apps.tags.models.Tag`
                            via :class:`ProductionTag`.
    """

    class AttendanceMode(models.TextChoices):
        """Controls whether the audience attends in person or online."""

        OFFLINE = "offline", "Offline"
        ONLINE = "online", "Online"

    class PerformerType(models.TextChoices):
        """Distinguishes group performances from solo acts."""

        GROUP = "group", "Group"
        SOLO = "solo", "Solo"

    uit_database_theme = models.ForeignKey(
        UitDatabaseTheme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="productions",
        help_text="UIT Database theme classification. `null` when not assigned.",
        db_comment="The theme of the production as defined in the UIT database.",
    )

    uit_database_type = models.ForeignKey(
        UitDatabaseType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="productions",
        help_text="UIT Database type classification. `null` when not assigned.",
        db_comment="The type of the production as defined in the UIT database.",
    )

    media_gallery = models.ForeignKey(
        MediaGallery,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="productions",
        help_text="Media gallery associated with this production. `null` when not assigned.",
        db_comment="The media gallery of the production.",
    )

    attendance_mode = models.CharField(
        max_length=20,
        choices=AttendanceMode.choices,
        blank=True,
        help_text="How the audience attends the production. Accepted values: `offline`, `online`.",
        db_comment="The attendance mode of the production.",
    )

    performer_type = models.CharField(
        max_length=20,
        choices=PerformerType.choices,
        blank=True,
        help_text="Whether the performance is by a group or a solo artist. Accepted values: `group`, `solo`.",
        db_comment="The performer type of the production.",
    )

    genres = models.ManyToManyField(
        Genre,
        blank=True,
        through="ProductionGenre",
        related_name="productions",
        help_text="Genres associated with this production, ordered by `ProductionGenre.position`.",
        db_comment="The genres of the production.",
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        through="ProductionTag",
        related_name="productions",
        help_text="Tags associated with this production.",
        db_comment="The tags of the production.",
    )

    class Meta(BaseModel.Meta):
        db_table = "production"
        verbose_name = "Production"
        verbose_name_plural = "Productions"
        ordering = ["-id"]

    def __str__(self) -> str:
        title = self.get_base_display_name(
            related_name="translations",
            name_field="title",
            fallback=None,
        )
        return title or f"Production {self.id}"


class ProductionTranslation(BaseModel):
    """
    Localised text fields for a Production.

    Each production can have at most one translation per language. All
    human-readable content that must be presented in multiple languages is
    stored here rather than on the :class:`Production` model itself.

    Text fields that may contain HTML (``teaser``, ``description``, etc.)
    should be sanitised before saving to prevent XSS attacks.

    Attributes:
        production:        The production this translation belongs to.
        language:          The language of this translation.
        supertitle:        Short line displayed above the main title.
        title:             Main display title of the production.
        artist_name:       Name of the performing artist or company.
        tagline:           One-line marketing phrase.
        teaser:            Short promotional text (may contain HTML).
        description:       Full-length description (may contain HTML).
        description_short: Condensed version of the description.
        description_extra: Supplementary description block.
        description_2:     Secondary description block.
        video_1:           URL of the primary video.
        video_2:           URL of the secondary video.
        meta_title:        SEO page title override.
        meta_description:  SEO meta description.
    """

    production = models.ForeignKey(
        Production,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Production this translation belongs to.",
        db_comment="The production that the translation belongs to.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="production_translations",
        help_text="Language of this translation.",
        db_comment="The language of the translation.",
        db_column="language_code",
    )

    supertitle = models.CharField(
        max_length=200,
        blank=True,
        help_text="Short line displayed above the main title (e.g. a season label).",
        db_comment="The supertitle of the production in the given language.",
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Main display title of the production in this language.",
        db_comment="The title of the production in the given language.",
    )

    artist_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the performing artist or company in this language.",
        db_comment="The name of the artist of the production in the given language.",
    )

    tagline = models.CharField(
        max_length=200,
        blank=True,
        help_text="One-line marketing phrase for the production.",
        db_comment="The tagline of the production in the given language.",
    )

    teaser = models.TextField(
        blank=True,
        help_text="Short promotional text. May contain HTML — sanitise before saving.",
        db_comment="The teaser of the production in the given language.",
    )

    description = models.TextField(
        blank=True,
        help_text="Full-length description of the production. May contain HTML — sanitise before saving.",
        db_comment="The description of the production in the given language.",
    )

    description_short = models.TextField(
        blank=True,
        help_text="Condensed version of the description, suitable for cards and previews.",
        db_comment="The short description of the production in the given language.",
    )

    description_extra = models.TextField(
        blank=True,
        help_text="Supplementary description block (e.g. practical information).",
        db_comment="The extra description of the production in the given language.",
    )

    description_2 = models.TextField(
        blank=True,
        help_text="Secondary description block for additional editorial content.",
        db_comment="The second description of the production in the given language.",
    )

    video_1 = models.URLField(
        blank=True,
        help_text="URL of the primary video (e.g. a Vimeo or YouTube embed URL).",
        db_comment="The URL of the first video of the production in the given language.",
    )

    video_2 = models.URLField(
        blank=True,
        help_text="URL of the secondary video.",
        db_comment="The URL of the second video of the production in the given language.",
    )

    meta_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="SEO page title override. Falls back to `title` when empty.",
        db_comment="The meta title of the production in the given language.",
    )

    meta_description = models.TextField(
        blank=True,
        help_text="SEO meta description. Ideally 120–160 characters.",
        db_comment="The meta description of the production in the given language.",
    )

    class Meta(BaseModel.Meta):
        db_table = "production_translation"
        verbose_name = "Production Translation"
        verbose_name_plural = "Production Translations"
        ordering = ["language__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["production", "language"],
                name="unique_production_language",
            )
        ]

    def __str__(self) -> str:
        return f"Translation of Production {self.production.id} in {self.language.code}"


class ProductionTag(BaseModel):
    """
    Through-table for the many-to-many relation between Productions and Tags.

    Each combination of production and tag must be unique. There is no
    ordering requirement — tags are an unordered set on a production.

    Attributes:
        production: The production the tag is attached to.
        tag:        The tag being attached.
    """

    production = models.ForeignKey(
        Production,
        on_delete=models.CASCADE,
        help_text="Production the tag is attached to.",
        db_comment="FK to Production.",
    )

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        help_text="Tag being attached to the production.",
        db_comment="FK to Tag.",
    )

    class Meta(BaseModel.Meta):
        db_table = "production_tag"
        verbose_name = "Production Tag"
        verbose_name_plural = "Production Tags"
        ordering = ["tag__type", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["production", "tag"],
                name="unique_production_tag",
            )
        ]

    def __str__(self) -> str:
        return f"Tag {self.tag} for {self.production}"


class ProductionGenre(BaseModel):
    """
    Ordered through-table for the many-to-many relation between Productions
    and Genres.

    The ``position`` field controls the display order of genres within a
    production. Lower values appear first. Unlike :class:`ProductionTag`,
    this through-table carries an ordering attribute and should always be
    queried with ``.order_by("position")``.

    Attributes:
        production: The production the genre is attached to.
        genre:      The genre being attached.
        position:   Display order index; lower values appear first.
    """

    production = models.ForeignKey(
        Production,
        on_delete=models.CASCADE,
        help_text="Production the genre is attached to.",
        db_comment="The production that the genre belongs to.",
    )

    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        help_text="Genre being attached to the production.",
        db_comment="The genre of the production.",
    )

    position = models.PositiveIntegerField(
        help_text="Display order index for this genre within the production. Lower values appear first.",
        db_comment="The position of the genre in the list of genres for the production.",
    )

    class Meta(BaseModel.Meta):
        db_table = "production_genre"
        verbose_name = "Production Genre"
        verbose_name_plural = "Production Genres"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["production", "genre"],
                name="unique_production_genre",
            )
        ]

    def __str__(self) -> str:
        return str(self.genre)