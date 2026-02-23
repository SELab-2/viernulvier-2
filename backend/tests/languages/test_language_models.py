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


def test_language_creation():
    """Test that a language can be created successfully."""
    lang = LanguageFactory.create()

    assert lang.pk is not None
    assert lang.code == 'nl'
    assert lang.name == 'Dutch'
    assert lambda: lang.is_active == True
    
    lang2 = LanguageFactory.create(code='en', name='English', is_active=False)
    assert lang2.code == 'en'
    assert lang2.name == 'English'
    assert lang2.is_active == False
    

def test_language_creation_error():
    """Test that creating a language with invalid data raises an error."""
    with pytest.raises(ValidationError):
        LanguageFactory.create(code='invalidCodeLength', name='English')

    with pytest.raises(ValidationError):
        LanguageFactory.create(code='en', name='InvalidNameLength')


def test_language_str():
    """Test the string representation of the Language model."""
    lang = LanguageFactory.create(code='en', name='English')
    assert str(lang) == 'en - English'


def test_language_code_is_primary_key():
    """Test that the code field is the primary key."""
    lang1 = LanguageFactory.create(code='en', name='English')
    lang2 = LanguageFactory.create(code='nl', name='Dutch')

    assert lang1.pk == 'en'
    assert lang2.pk == 'nl'


def test_blank_and_null_constraints():
    """Test that blank and null constraints are enforced."""
    with pytest.raises(ValidationError):
        LanguageFactory.create(code='en', name=None)

    with pytest.raises(ValidationError):
        LanguageFactory.create(code='en', name='')


def test_genre_translations():
    """Language should expose related genre translations via genre_translations."""
    language = LanguageFactory.create(code='en', name='English')
    translations = GenreTranslationFactory.create_batch(3, language=language)

    assert language.genre_translations.count() == 3
    assert all(tr.language == language for tr in translations)
    assert str(translations[0]).startswith('en - ')


def test_media_item_translations_related_name():
    """Language should expose media item translations via media_item_translations."""
    language = LanguageFactory.create(code='fr', name='French')
    MediaItemTranslationFactory.create_batch(2, language=language)

    assert language.media_item_translations.count() == 2


def test_location_space_hall_translations_related_names():
    """Language should expose location, space, and hall translations via <location|space|hall>_translations."""
    language = LanguageFactory.create(code='de', name='German')

    LocationTranslationFactory.create_batch(2, language=language)
    SpaceTranslationFactory.create(language=language)
    HallTranslationFactory.create(language=language)

    assert language.location_translations.count() == 2
    assert language.space_translations.count() == 1
    assert language.hall_translations.count() == 1


def test_price_translation_related_name():
    """Language should expose price translations via price_translations."""
    language = LanguageFactory.create(code='it', name='Italian')
    PriceTranslationFactory.create_batch(2, language=language)

    assert language.price_translations.count() == 2


def test_price_rank_translation_reverse_manager():
    """Language should expose price rank translations via pricerank_translations."""
    language = LanguageFactory.create(code='es', name='Spanish')
    PriceRankTranslationFactory.create(language=language)

    assert language.pricerank_translations.count() == 1


def test_tag_translations_related_name():
    """Language should expose tag translations via tag_translations."""
    language = LanguageFactory.create(code='pt', name='Portuguese')
    TagTranslationFactory.create_batch(2, language=language)

    assert language.tag_translations.count() == 2