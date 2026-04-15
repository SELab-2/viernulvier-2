"""Models for the Genre app.

Genres classify productions.
"""

from django.db import models

from apps.core.models import BaseModel
from apps.languages.models import Language


class Genre(BaseModel):
    """Core genre entity.

    A genre represents a classification type such as Theater, Festival,
    or Book Presentation. Each genre has:

    - A vendor-specific ``vendor_id`` (optional) provided by the upstream Viernulvier API
    - A technical ``type`` (internal snake_case identifier)
    - An optional ``vendor_id`` provided by the upstream Viernulvier API
    - One or more ``translations`` (localised display names)
    """

    vendor_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Vendor-specific identifier from the upstream API.",
        db_comment="Vendor identifier for the genre.",
    )

    type = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="Internal snake_case identifier (e.g. 'theater', 'festival').",
        db_comment="Technical type of the genre.",
    )

    class Meta(BaseModel.Meta):
        db_table = "genre"
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
        ordering = ["id"]

    def __str__(self) -> str:
        """Return a human-readable representation of the genre, preferring the base display name, then vendor_id, then type."""
        name = self.get_base_display_name(
            related_name="translations",
            fallback=None,
        )

        if name:
            return f"{name} ({self.type})"

        stripped_vendor_id = self.vendor_id.strip() if self.vendor_id else ""
        if stripped_vendor_id != "":
            return stripped_vendor_id

        return self.type


class GenreTranslation(BaseModel):
    """Localised display name for a Genre.

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
        """Return a string representation of the translation, including the language code and name."""
        return f"{self.language.code} - {self.name}"
