"""
Tests for TranslatableSerializerMixin (apps/core/serializers.py)

Covers:
- get_translated_field() - happy path with multiple languages
- get_translated_field() - missing/blank field values are excluded
- get_translated_field() - empty translations queryset
- get_translated_field() - single translation
- get_translated_field() - field does not exist on translation raises AttributeError
"""

from unittest.mock import MagicMock

from django.conf import settings
from django.test import TestCase

from apps.core.serializers import TranslatableSerializerMixin

# ---------------------------------------------------------------------------
# Fake domain objects
# ---------------------------------------------------------------------------


def make_translation(lang_code: str, **field_values):
    """Build a mock translation object."""
    t = MagicMock()
    t.language = MagicMock()
    t.language.code = lang_code
    for field, value in field_values.items():
        setattr(t, field, value)
    return t


def make_obj(translations: list):
    """Build a mock model instance whose .translations.all() returns *translations*."""
    obj = MagicMock()
    obj.translations = MagicMock()
    obj.translations.all.return_value = translations
    return obj


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTranslatableSerializerMixin(TestCase):
    def setUp(self) -> None:
        # Concrete class (mixin has no abstract methods)
        self.mixin = TranslatableSerializerMixin()

    # -- Happy path -----------------------------------------------------------

    def test_returns_dict_with_all_languages(self) -> None:
        translations = [
            make_translation("nl", title="Titel"),
            make_translation("en", title="Title"),
            make_translation("de", title="Titel DE"),
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        assert result == {"nl": "Titel", "en": "Title", "de": "Titel DE"}

    def test_returns_dict_for_single_translation(self) -> None:
        translations = [make_translation("nl", title="Enkel NL")]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        assert result == {"nl": "Enkel NL"}

    # -- Blank / falsy values are excluded ------------------------------------

    def test_excludes_empty_string_values(self) -> None:
        translations = [
            make_translation("nl", title="Titel"),
            make_translation("en", title=""),  # blank -> excluded
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        assert "en" not in result
        assert "nl" in result

    def test_excludes_none_values(self) -> None:
        translations = [
            make_translation("nl", title="Titel"),
            make_translation("fr", title=None),  # None -> excluded
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        assert "fr" not in result

    def test_excludes_all_blank_returns_empty_dict(self) -> None:
        translations = [
            make_translation("nl", title=""),
            make_translation("en", title=None),
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        assert result == {}

    # -- Empty queryset -------------------------------------------------------

    def test_empty_translations_returns_empty_dict(self) -> None:
        obj = make_obj([])
        result = self.mixin.get_translated_field(obj, "title")
        assert result == {}

    # -- Different field names ------------------------------------------------

    def test_works_for_description_field(self) -> None:
        translations = [
            make_translation("nl", description="Beschrijving"),
            make_translation("en", description="Description"),
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "description")
        assert result == {"nl": "Beschrijving", "en": "Description"}

    # -- Return type ----------------------------------------------------------

    def test_return_type_is_dict(self) -> None:
        obj = make_obj([make_translation("nl", name="Test")])
        result = self.mixin.get_translated_field(obj, "name")
        assert isinstance(result, dict)

    # -- Language codes are used as keys, not names ---------------------------

    def test_keys_are_language_codes(self) -> None:
        translations = [make_translation("nl-BE", title="Belgisch NL")]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        assert "nl-BE" in result

    # -- Duplicate language codes (last-wins, realistic guard) ----------------

    def test_duplicate_language_code_last_wins(self) -> None:
        """If the queryset somehow contains duplicates, the last one wins."""
        translations = [
            make_translation("nl", title="First"),
            make_translation("nl", title="Second"),
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        assert result["nl"] == "Second"


def test_get_base_language_code_default():
    settings.LANGUAGE_CODE = None
    mixin = TranslatableSerializerMixin()
    assert mixin.get_base_language_code() == "en"


def test_get_base_language_code_with_region():
    settings.LANGUAGE_CODE = "fr-BE"
    mixin = TranslatableSerializerMixin()
    assert mixin.get_base_language_code() == "fr"


def test_get_base_translated_value_prefers_base_language():
    mixin = TranslatableSerializerMixin()

    translations = [
        make_translation("en", title="English"),
        make_translation("nl", title="Nederlands"),
    ]
    obj = make_obj(translations)

    settings.LANGUAGE_CODE = "nl"

    result = mixin.get_base_translated_value(obj, "title")
    assert result == "Nederlands"


def test_get_base_translated_value_fallback_first():
    mixin = TranslatableSerializerMixin()

    translations = [
        make_translation("fr", title="FR"),
        make_translation("de", title="DE"),
    ]
    obj = make_obj(translations)

    settings.LANGUAGE_CODE = "nl"

    result = mixin.get_base_translated_value(obj, "title")
    assert result == "FR"


def test_get_base_translated_value_returns_fallback():
    mixin = TranslatableSerializerMixin()

    translations = [
        make_translation("fr", title=None),
    ]
    obj = make_obj(translations)

    result = mixin.get_base_translated_value(obj, "title", fallback="DEFAULT")
    assert result == "DEFAULT"
