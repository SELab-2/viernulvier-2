"""
Definitions of the models related to genres.
"""

from django.db import models
from apps.core.model import BaseModel
from apps.languages.models import Language

class GenreUseAs(BaseModel):
    """
    Model to define the use cases for genres. Like used in the existing viernulvier API.
    """
    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        db_comment="Use cases for the genre, ex. 'tag', 'genre'"
    )

    class Meta(BaseModel.Meta):
        db_table = "genre_use_as"
        verbose_name = "Genre Use As"
        verbose_name_plural = "Genres Used As"
        ordering = ["id"]
    
    def __str__(self):
        return self.name


class Genre(BaseModel):
    """
    Model to define genres.
    """
    type = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        db_comment="The type of the genre ex. 'Theater', 'Festival', 'Boek voorstelling', etc."
    )

    use_as = models.ForeignKey(
        GenreUseAs,
        on_delete=models.CASCADE,
        related_name="genres", 
        null=False,
        blank=False,
        db_comment="Reference to GenreUseAs."
    )

    class Meta(BaseModel.Meta):
        db_table = "genre"
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
        ordering = ["id"]

    def __str__(self): # TODO maybe this can be better, but for now it shows the type and the translations of the genre
        # Get the English name for the genre
        english_name = GenreTranslation.objects.filter(
            genre=self,
            language_id="en"
        ).first()

        # Get the Dutch name for the genre
        dutch_name = GenreTranslation.objects.filter(
            genre=self,
            language_id="nl"
        ).first()

        # Show both translations in the string representation of the genre
        return f"{self.type} - [{str(english_name)}] - [{str(dutch_name)}]"


class GenreTranslation(BaseModel):
    """
    Model to define different translations for genre names.
    """
    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        db_comment="The name of the genre in a specific language"
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="genre_translations",
        db_comment="Reference to the language of the genre translation."
    )

    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        related_name="translations",
        db_comment="Reference to the genre."
    )

    class Meta(BaseModel.Meta):
        db_table = "genre_translation"
        verbose_name = "Genre Translation"
        verbose_name_plural = "Genre Translations"
        ordering = ["id"]
    
    def __str__(self) -> str:
        return f"{self.language.code} - {self.name}"
