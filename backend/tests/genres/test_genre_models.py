import pytest

from apps.genres.models import GenreTranslation

# Use the factories to create test data
from tests.factories.genre import (
    GenreFactory,
    GenreTranslationFactory,
)
from tests.factories.language import LanguageFactory

pytestmark = pytest.mark.django_db

# =====================================================
# Genre
# =====================================================


class TestGenre:
    def test_str_representation_contains_translations(self) -> None:
        genre = GenreFactory(type="Festival")
        GenreTranslationFactory(genre=genre, language__code="en", name="EN Festival")
        GenreTranslationFactory(genre=genre, language__code="nl", name="NL Festival")

        assert str(genre) == "EN Festival (Festival)"

    def test_str_uses_vendor_id_when_translation_missing(self) -> None:
        genre = GenreFactory(type="theater", vendor_id="opera")

        assert str(genre) == "opera"

    def test_str_falls_back_to_type_when_translation_and_vendor_id_blank(self) -> None:
        genre = GenreFactory(type="theater", vendor_id="")

        assert str(genre) == "theater"

    def test_str_falls_back_to_type_when_translation_and_vendor_id_none(self) -> None:
        genre = GenreFactory(type="theater", vendor_id=None)

        assert str(genre) == "theater"

    def test_delete_cascades_to_translations(self) -> None:
        genre = GenreFactory()
        GenreTranslationFactory.create_batch(2, genre=genre)  # Create 2 translations for the genre

        genre.delete()  # Delete the genre, which should cascade to the translations

        assert GenreTranslation.objects.count() == 0


# =====================================================
# GenreTranslation
# =====================================================


class TestGenreTranslation:
    def test_str(self) -> None:
        translation = GenreTranslationFactory(
            language__code="en",
            name="Rock",
        )
        assert str(translation) == "en - Rock"

    def test_language_reverse_relation(self) -> None:
        language = LanguageFactory()
        GenreTranslationFactory.create_batch(2, language=language)

        assert language.genre_translations.count() == 2


# =====================================================
# Cascade behaviour
# =====================================================


class TestCascadeBehaviour:
    def test_deleting_language_cascades_to_translations(self) -> None:
        language = LanguageFactory()
        GenreTranslationFactory(language=language)

        # Check if the setup is correct
        assert GenreTranslation.objects.count() == 1

        language.delete()

        # Check if the translation was deleted
        assert GenreTranslation.objects.count() == 0
