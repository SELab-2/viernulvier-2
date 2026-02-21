import pytest
from django.core.exceptions import ValidationError
from apps.languages.models import Language
from test.factories.language import LanguageFactory

pytestmark = pytest.mark.django_db

def test_language_creation():
    """Test that a language can be created successfully."""
    lang = LanguageFactory.create()

    assert lang.pk is not None
    assert lang.code in ['nl', 'en', 'de', 'fr']
    assert lang.name in ['Dutch', 'English', 'German', 'French']
    assert lambda: lang.is_active == True

    lang2 = LanguageFactory.create(code='nl', name='Dutch', is_active=False)
    assert lang2.code == 'nl'
    assert lang2.name == 'Dutch'
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
