from django.db import models
from apps.core.model import BaseModel
from apps.languages.models import Language

class GenreUseAs(BaseModel):
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

class Genre(BaseModel):
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

    def __str__(self):
        english_name = GenreTranslation.objects.filter(
            genre=self,
            language_id="en"
        )

        dutch_name = GenreTranslation.objects.filter(
            genre=self,
            language_id="nl"
        )

        return f"{self.type} - {str(english_name)} - {str(dutch_name)}"


class GenreTranslation(BaseModel):
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
        related_name="genre_translations",
        db_comment="Reference to the genre."
    )

    class Meta(BaseModel.Meta):
        db_table = "genre_translation"
        verbose_name = "Genre Translation"
        verbose_name_plural = "Genre Translations"
    
    def __str__(self) -> str:
        return f"{self.language.code} - {self.name}"
