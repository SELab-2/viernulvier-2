import pytest
from django.core.exceptions import ValidationError

from apps.genres.models import Genre, GenreTranslation

# Use the factories to create test data
from tests.factories.genre import (
    GenreFactory,
    GenreTranslationFactory,
    GenreUseAsFactory,
)
from tests.factories.language import LanguageFactory

pytestmark = pytest.mark.django_db

# =====================================================
# GenreUseAs
# =====================================================

class TestGenreUseAs:

    def test_requires_name(self):
        instance = GenreUseAsFactory.build(name="")
        with pytest.raises(ValidationError):
            instance.full_clean()

    def test_reverse_relation_genres(self):
        use_as = GenreUseAsFactory()
        GenreFactory.create_batch(3, use_as=use_as)
        
        assert use_as.genres.count() == 3


# =====================================================
# Genre
# =====================================================

class TestGenre:

    def test_requires_use_as(self):
        genre = GenreFactory.build(use_as=None)
        with pytest.raises(ValidationError):
            genre.full_clean()

    def test_str_representation_contains_translations(self):
        genre = GenreFactory(type="Festival")
        GenreTranslationFactory(genre=genre, language__code="en", name="Festival")
        GenreTranslationFactory(genre=genre, language__code="nl", name="Festival NL")

        assert str(genre) == "Festival - [en - Festival] - [nl - Festival NL]"

    def test_delete_cascades_to_translations(self):
        genre = GenreFactory()
        # Create 2 translations for the genre
        GenreTranslationFactory.create_batch(2, genre=genre) 

        genre.delete() # Delete the genre, which should cascade to the translations

        assert GenreTranslation.objects.count() == 0


# =====================================================
# GenreTranslation
# =====================================================

class TestGenreTranslation:

    def test_str(self):
        translation = GenreTranslationFactory(
            language__code="en",
            name="Rock",
        )
        assert str(translation) == "en - Rock"

    def test_language_reverse_relation(self):
        language = LanguageFactory()
        GenreTranslationFactory.create_batch(2, language=language)
        
        assert language.genre_translations.count() == 2


# =====================================================
# Cascade behaviour
# =====================================================

class TestCascadeBehaviour:

    def test_deleting_use_as_cascades_to_genres(self):
        use_as = GenreUseAsFactory()
        GenreFactory(use_as=use_as)

        # Check if the setup is correct
        assert Genre.objects.count() == 1
        
        use_as.delete()

        # Check if the genre was deleted
        assert Genre.objects.count() == 0

    def test_deleting_language_cascades_to_translations(self):
        language = LanguageFactory()
        GenreTranslationFactory(language=language)

        # Check if the setup is correct
        assert GenreTranslation.objects.count() == 1

        language.delete()

        # Check if the translation was deleted
        assert GenreTranslation.objects.count() == 0