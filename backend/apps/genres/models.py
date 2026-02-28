"""
Models for the Genre app.

Genres classify productions and can be applied in different contexts
(e.g. as a taxonomy genre or as a lightweight tag).
"""

from django.db import models

from apps.core.models import BaseModel
from apps.languages.models import Language


class GenreUseAs(BaseModel):
    """
    Defines how a Genre is used in the system.

    Examples:
        - ``genre``  -> used as a production classification
        - ``tag``    -> used as a lightweight label
    """

    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="Context in which genres with this role are applied (e.g. 'genre', 'tag').",
        db_comment="Use-case label for the genre.",
    )

    class Meta(BaseModel.Meta):
        db_table = "genre_use_as"
        verbose_name = "Genre Use As"
        verbose_name_plural = "Genres Used As"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name


class Genre(BaseModel):
    """
    Core genre entity.

    A genre represents a classification type such as Theater, Festival,
    or Book Presentation. Each genre has:

    - A technical ``type`` (internal snake_case identifier)
    - A ``use_as`` relationship defining its role in the system
    - One or more ``translations`` (localised display names)
    """

    type = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="Internal snake_case identifier (e.g. 'theater', 'festival').",
        db_comment="Technical type of the genre.",
    )

    use_as = models.ForeignKey(
        GenreUseAs,
        on_delete=models.CASCADE,
        related_name="genres",
        null=False,
        blank=False,
        help_text="Defines how this genre is applied (taxonomy or tagging).",
        db_comment="FK to GenreUseAs.",
    )

    class Meta(BaseModel.Meta):
        db_table = "genre"
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.type


class GenreTranslation(BaseModel):
    """
    Localised display name for a Genre.

    Each genre can have at most one translation per language.
    """

    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="Localised display name of the genre.",
        db_comment="Translated name of the genre.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="genre_translations",
        help_text="Language of this translation.",
        db_comment="FK to Language.",
    )

    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Genre this translation belongs to.",
        db_comment="FK to Genre.",
    )

    class Meta(BaseModel.Meta):
        db_table = "genre_translation"
        verbose_name = "Genre Translation"
        verbose_name_plural = "Genre Translations"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.language.code} — {self.name}"