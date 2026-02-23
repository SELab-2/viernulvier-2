import pytest
from django.core.exceptions import ValidationError
from apps.languages.models import Language
from tests.factories.language import LanguageFactory
from tests.factories.genre import GenreTranslationFactory
from tests.factories.media_library import MediaItemTranslationFactory
from tests.factories.location import (
    LocationTranslationFactory,
    SpaceTranslationFactory,
    HallTranslationFactory,
)
from tests.factories.pricing import PriceTranslationFactory, PriceRankTranslationFactory
from tests.factories.tag import TagTranslationFactory

pytestmark = pytest.mark.django_db

class TestLanguageModel:
    def test_language_creation_defaults(self):
        """Test that a language can be created with expected default values."""
        lang = LanguageFactory.create(code="nl", name="Dutch")

        assert lang.pk is not None
        assert lang.code == "nl"
        assert lang.name == "Dutch"
        assert lang.is_active is True  # default defined in factory

    def test_language_creation_inactive(self):
        """Test that is_active can be explicitly set to False."""
        lang = LanguageFactory.create(code="en", name="English", is_active=False)

        assert lang.code == "en"
        assert lang.name == "English"
        assert lang.is_active is False
        

    def test_language_code_too_long_raises_validation_error(self):
        """Code exceeding max_length=2 should raise ValidationError."""
        with pytest.raises(ValidationError):
            LanguageFactory.create(code="invalidCodeLength", name="English")

    def test_language_name_too_long_raises_validation_error(self):
        """Name exceeding max_length=15 should raise ValidationError."""
        with pytest.raises(ValidationError):
            LanguageFactory.create(code="en", name="A" * 16)

    def test_language_str(self):
        """Test the string representation of the Language model."""
        lang = LanguageFactory.create(code='en', name='English')
        assert str(lang) == 'en - English'


    def test_language_code_is_primary_key(self):
        """Test that the code field is the primary key."""
        lang1 = LanguageFactory.create(code='en', name='English')
        lang2 = LanguageFactory.create(code='nl', name='Dutch')

        assert lang1.pk == 'en'
        assert lang2.pk == 'nl'


    def test_name_null_raises_validation_error(self):
        """name=None should raise ValidationError."""
        with pytest.raises(ValidationError):
            LanguageFactory.create(code="en", name=None)

    def test_name_blank_raises_validation_error(self):
        """name='' should raise ValidationError."""
        with pytest.raises(ValidationError):
            LanguageFactory.create(code="en", name="")


    def test_genre_translations(self):
        """Language should expose related genre translations via genre_translations."""
        language = LanguageFactory.create(code='en', name='English')
        translations = GenreTranslationFactory.create_batch(3, language=language)

        assert language.genre_translations.count() == 3
        assert all(tr.language == language for tr in translations)
        assert str(translations[0]).startswith('en - ')


    def test_media_item_translations_related_name(self):
        """Language should expose media item translations via media_item_translations."""
        language = LanguageFactory.create(code='fr', name='French')
        MediaItemTranslationFactory.create_batch(2, language=language)

        assert language.media_item_translations.count() == 2


    def test_location_space_hall_translations_related_names(self):
        """Language should expose location, space, and hall translations via <location|space|hall>_translations."""
        language = LanguageFactory.create(code='de', name='German')

        LocationTranslationFactory.create_batch(2, language=language)
        SpaceTranslationFactory.create(language=language)
        HallTranslationFactory.create(language=language)

        assert language.location_translations.count() == 2
        assert language.space_translations.count() == 1
        assert language.hall_translations.count() == 1


    def test_price_translation_related_name(self):
        """Language should expose price translations via price_translations."""
        language = LanguageFactory.create(code='it', name='Italian')
        PriceTranslationFactory.create_batch(2, language=language)

        assert language.price_translations.count() == 2


    def test_price_rank_translation_reverse_manager(self):
        """Language should expose price rank translations via pricerank_translations."""
        language = LanguageFactory.create(code='es', name='Spanish')
        PriceRankTranslationFactory.create(language=language)

        assert language.pricerank_translations.count() == 1


    def test_tag_translations_related_name(self):
        """Language should expose tag translations via tag_translations."""
        language = LanguageFactory.create(code='pt', name='Portuguese')
        TagTranslationFactory.create_batch(2, language=language)

        assert language.tag_translations.count() == 2