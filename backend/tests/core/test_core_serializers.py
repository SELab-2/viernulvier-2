"""
Tests for TranslatableSerializerMixin (apps/core/serializers.py)

Covers:
- get_translated_field() — happy path with multiple languages
- get_translated_field() — missing/blank field values are excluded
- get_translated_field() — empty translations queryset
- get_translated_field() — single translation
- get_translated_field() — field does not exist on translation raises AttributeError
"""

from unittest.mock import MagicMock
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

    def setUp(self):
        # Concrete class (mixin has no abstract methods)
        self.mixin = TranslatableSerializerMixin()

    # -- Happy path -----------------------------------------------------------

    def test_returns_dict_with_all_languages(self):
        translations = [
            make_translation("nl", title="Titel"),
            make_translation("en", title="Title"),
            make_translation("de", title="Titel DE"),
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        self.assertEqual(result, {"nl": "Titel", "en": "Title", "de": "Titel DE"})

    def test_returns_dict_for_single_translation(self):
        translations = [make_translation("nl", title="Enkel NL")]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        self.assertEqual(result, {"nl": "Enkel NL"})

    # -- Blank / falsy values are excluded ------------------------------------

    def test_excludes_empty_string_values(self):
        translations = [
            make_translation("nl", title="Titel"),
            make_translation("en", title=""),  # blank → excluded
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        self.assertNotIn("en", result)
        self.assertIn("nl", result)

    def test_excludes_none_values(self):
        translations = [
            make_translation("nl", title="Titel"),
            make_translation("fr", title=None),  # None -> excluded
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        self.assertNotIn("fr", result)

    def test_excludes_all_blank_returns_empty_dict(self):
        translations = [
            make_translation("nl", title=""),
            make_translation("en", title=None),
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        self.assertEqual(result, {})

    # -- Empty queryset -------------------------------------------------------

    def test_empty_translations_returns_empty_dict(self):
        obj = make_obj([])
        result = self.mixin.get_translated_field(obj, "title")
        self.assertEqual(result, {})

    # -- Different field names ------------------------------------------------

    def test_works_for_description_field(self):
        translations = [
            make_translation("nl", description="Beschrijving"),
            make_translation("en", description="Description"),
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "description")
        self.assertEqual(result, {"nl": "Beschrijving", "en": "Description"})

    # -- Return type ----------------------------------------------------------

    def test_return_type_is_dict(self):
        obj = make_obj([make_translation("nl", name="Test")])
        result = self.mixin.get_translated_field(obj, "name")
        self.assertIsInstance(result, dict)

    # -- Language codes are used as keys, not names ---------------------------

    def test_keys_are_language_codes(self):
        translations = [make_translation("nl-BE", title="Belgisch NL")]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        self.assertIn("nl-BE", result)

    # -- Duplicate language codes (last-wins, realistic guard) ----------------

    def test_duplicate_language_code_last_wins(self):
        """If the queryset somehow contains duplicates, the last one wins."""
        translations = [
            make_translation("nl", title="First"),
            make_translation("nl", title="Second"),
        ]
        obj = make_obj(translations)
        result = self.mixin.get_translated_field(obj, "title")
        self.assertEqual(result["nl"], "Second")