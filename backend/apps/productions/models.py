from django.db import models
from apps.core.model import BaseModel
from apps.languages.models import Language
from apps.events.models import Event
from apps.tags.models import Tag
from apps.genres.models import Genre

class UitDatabaseTheme(BaseModel):
    """Model representing a theme in the UIT database."""
    name = models.CharField(
        max_length=200,
        db_comment="The name of the theme."
    )

    class Meta(BaseModel.Meta):
        db_table = "uit_database_theme"
        verbose_name = "UIT Database Theme"
        verbose_name_plural = "UIT Database Themes"

    def __str__(self):
        return self.name

class UitDatabaseType(BaseModel):
    """Model representing a type in the UIT database."""
    name = models.CharField(
        max_length=200,
        db_comment="The name of the type."
    )

    class Meta(BaseModel.Meta):
        db_table = "uit_database_type"
        verbose_name = "UIT Database Type"
        verbose_name_plural = "UIT Database Types"

    def __str__(self):
        return self.name

class Production(BaseModel):
    """Model representing a production."""

    # TODO: add more choices for attendance model if needed (look at the api responses)
    class AttendanceMode(models.TextChoices):
        """Enum representing the attendance model of a production."""
        OFFLINE = "offline", "Offline"
        ONLINE = "online", "Online"

    # TODO: add more choices for performer model if needed (look at the api responses)
    class PerformerType(models.TextChoices):
        """Enum representing the performer type of a production."""
        GROUP = "group", "Group"
        SOLO = "solo", "Solo"

    uit_database_theme = models.ForeignKey(
        UitDatabaseTheme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_comment="The theme of the production as defined in the UIT database.",
        related_name="productions",
    )

    uit_database_type = models.ForeignKey(
        UitDatabaseType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_comment="The type of the production as defined in the UIT database.",
        related_name="productions",
    )

    media_gallery = models.ForeignKey(
        MediaGallery, # TODO: implement MediaGallery model
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_comment="The media gallery of the production.",
        related_name="productions",
    )

    attendance_mode = models.CharField(
        max_length=20,
        choices=AttendanceMode.choices,
        blank=True,
        db_comment="The attendance mode of the production."
    )

    performer_type = models.CharField(
        max_length=20,
        choices=PerformerType.choices,
        blank=True,
        db_comment="The performer type of the production."
    )

    genres = models.ManyToManyField(
        Genre, # TODO: implement Genre model
        blank=True,
        db_comment="The genres of the production.",
        through="ProductionGenre",
        related_name="productionGenres",
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        db_comment="The tags of the production.",
        through="ProductionTag",
        related_name="productionTags",
    )

    class Meta(BaseModel.Meta):
        db_table = "production"
        verbose_name = "Production"
        verbose_name_plural = "Productions"

    def __str__(self):
        return f"Production {self.id}" # TODO: change if we know how to do translations

class ProductionTranslation(BaseModel):
    """Model representing a translation of a production."""
    production = models.ForeignKey(
        Production,
        on_delete=models.CASCADE,
        db_comment="The production that the translation belongs to.",
        related_name="translations",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        db_comment="The language of the translation.",
        db_column="language_code",
    )

    supertitle = models.CharField(
        max_length=200,
        db_comment="The supertitle of the production in the given language.",
        blank=True
    )

    title = models.CharField(
        max_length=200,
        db_comment="The title of the production in the given language.",
        blank=True
    )

    artist_name = models.CharField(
        max_length=200,
        db_comment="The name of the artist of the production in the given language.",
        blank=True
    )

    tagline = models.CharField(
        max_length=200,
        db_comment="The tagline of the production in the given language.",
        blank=True
    )

    teaser = models.TextField(
        db_comment="The teaser of the production in the given language.",
        blank=True
    )

    description = models.TextField(
        db_comment="The description of the production in the given language.",
        blank=True
    )

    description_short = models.TextField(
        db_comment="The short description of the production in the given language.",
        blank=True
    )

    description_extra = models.TextField(
        db_comment="The extra description of the production in the given language.",
        blank=True
    )

    description_2 = models.TextField(
        db_comment="The second description of the production in the given language.",
        blank=True
    )

    video_1 = models.URLField(
        db_comment="The URL of the first video of the production in the given language.",
        blank=True
    )

    video_2 = models.URLField(
        db_comment="The URL of the second video of the production in the given language.",
        blank=True
    )

    meta_title = models.CharField(
        max_length=200,
        db_comment="The meta title of the production in the given language.",
        blank=True
    )

    meta_description = models.TextField(
        db_comment="The meta description of the production in the given language.",
        blank=True
    )

    class Meta(BaseModel.Meta):
        db_table = "production_translation"
        unique_together = ('production', 'language')
        verbose_name = "Production Translation"
        verbose_name_plural = "Production Translations"

    # TODO Add in save method html sanitization for the text fields to prevent XSS attacks, or use a library like bleach to sanitize the HTML content.

    def __str__(self):
        return f"Translation of Production {self.production.id} in {self.language.code}"
    
class ProductionTag(BaseModel):
    """Model representing the many-to-many relationship between productions and tags."""
    production = models.ForeignKey(
        Production, 
        on_delete=models.CASCADE
    )

    tag = models.ForeignKey(
        TAG, # TODO: implement TAG model
        on_delete=models.CASCADE
    )

    class Meta(BaseModel.Meta):
        db_table = "production_tag" 
        unique_together = ('production', 'tag')
        verbose_name = "Production Tag"
        verbose_name_plural = "Production Tags"

    def __str__(self):
        return f"Tag {self.tag.name} for Production {self.production.id}"

class ProductionGenre(BaseModel):
    """Model representing a genre of a production."""
    production = models.ForeignKey(
        Production,
        on_delete=models.CASCADE,
        db_comment="The production that the genre belongs to.",
    )

    genre = models.ForeignKey(
        Genre, # TODO: implement Genre model
        on_delete=models.CASCADE,
        db_comment="The genre of the production.",
    )

    position = models.PositiveIntegerField(
        db_comment="The position of the genre in the list of genres for the production.",
        # default=0, # TODO in viewset ordering definieren
    )

    class Meta(BaseModel.Meta):
        db_table = "production_genre"
        unique_together = ('production', 'genre')
        verbose_name = "Production Genre"
        verbose_name_plural = "Production Genres"

    def __str__(self):
        return f"Genre {self.genre.name} for Production {self.production.id}"