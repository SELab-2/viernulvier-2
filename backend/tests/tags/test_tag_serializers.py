"""
Tests for apps/tags/serializers.py

Covers:
- TagSerializer field presence and completeness
- TagSerializer serialization (model -> dict)
- Translated fields (name, short_description, url_title) returned as dicts
- Translated fields return empty dict when no translations exist
- Translated fields omit blank/falsy values
- TagSerializer deserialization / validation (dict -> model)
- Invalid data handling
- Field types
"""

import pytest
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory
from apps.languages.models import Language
from apps.tags.models import Tag, TagTranslation
from apps.tags.serializers import TagSerializer
from tests.factories.language import LanguageFactory
from tests.factories.tag import TagFactory, TagTranslationFactory


# ---------------------------------------------------------------------------
# Field presence
# ---------------------------------------------------------------------------


class TestTagSerializerFields(TestCase):
    """Verify that the correct fields are exposed."""

    def setUp(self):
        self.tag = TagFactory.create()

    def test_expected_fields_are_present(self):
        serializer = TagSerializer(self.tag)
        data = serializer.data
        for field in (
            "id",
            "url",
            "source",
            "source_type",
            "type",
            "is_external",
            "is_enabled",
            "name",
            "short_description",
            "url_title",
        ):
            self.assertIn(field, data)

    def test_no_extra_fields_are_exposed(self):
        serializer = TagSerializer(self.tag)
        expected = {
            "id",
            "url",
            "source",
            "source_type",
            "type",
            "is_external",
            "is_enabled",
            "name",
            "display_name",
            "display_short_description",
            "display_url_title",
            "short_description",
            "url_title",
        }
        self.assertEqual(set(serializer.data.keys()), expected)


# ---------------------------------------------------------------------------
# Serialization — scalar fields
# ---------------------------------------------------------------------------


class TestTagSerializerScalarFields(TestCase):
    """Model → dict for non-translated fields."""

    def test_serializes_type_correctly(self):
        tag = TagFactory.create(type="mood")
        data = TagSerializer(tag).data
        self.assertEqual(data["type"], "mood")

    def test_serializes_source_correctly(self):
        tag = TagFactory.create(source="external-api")
        data = TagSerializer(tag).data
        self.assertEqual(data["source"], "external-api")

    def test_serializes_source_type_correctly(self):
        tag = TagFactory.create(source_type="api")
        data = TagSerializer(tag).data
        self.assertEqual(data["source_type"], "api")

    def test_serializes_is_external_true(self):
        tag = TagFactory.create(is_external=True)
        data = TagSerializer(tag).data
        self.assertTrue(data["is_external"])

    def test_serializes_is_external_false(self):
        tag = TagFactory.create(is_external=False)
        data = TagSerializer(tag).data
        self.assertFalse(data["is_external"])

    def test_serializes_is_enabled_true(self):
        tag = TagFactory.create(is_enabled=True)
        data = TagSerializer(tag).data
        self.assertTrue(data["is_enabled"])

    def test_serializes_is_enabled_false(self):
        tag = TagFactory.create(is_enabled=False)
        data = TagSerializer(tag).data
        self.assertFalse(data["is_enabled"])

    def test_serializes_url_correctly(self):
        tag = TagFactory.create(url="https://example.com/genre")
        data = TagSerializer(tag).data
        self.assertEqual(data["url"], "https://example.com/genre")

    def test_type_is_string(self):
        tag = TagFactory.create(type="genre")
        data = TagSerializer(tag).data
        self.assertIsInstance(data["type"], str)

    def test_is_external_is_bool(self):
        tag = TagFactory.create()
        data = TagSerializer(tag).data
        self.assertIsInstance(data["is_external"], bool)

    def test_is_enabled_is_bool(self):
        tag = TagFactory.create()
        data = TagSerializer(tag).data
        self.assertIsInstance(data["is_enabled"], bool)


# ---------------------------------------------------------------------------
# Serialization — translated fields
# ---------------------------------------------------------------------------


class TestTagSerializerTranslatedFields(TestCase):
    """name / short_description / url_title are returned as language-keyed dicts."""

    def setUp(self):
        self.tag = TagFactory.create()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        self.en = LanguageFactory.create(code="en", name="English")

    def test_name_is_dict(self):
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        self.assertIsInstance(data["name"], dict)

    def test_name_contains_correct_language_keys(self):
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            url_title="genre",
        )
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.en,
            name="Genre EN",
            url_title="genre-en",
        )
        data = TagSerializer(self.tag).data
        self.assertIn("nl", data["name"])
        self.assertIn("en", data["name"])

    def test_name_contains_correct_values(self):
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Muziekgenre",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        self.assertEqual(data["name"]["nl"], "Muziekgenre")

    def test_short_description_is_dict(self):
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            short_description="Een muziekgenre",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        self.assertIsInstance(data["short_description"], dict)

    def test_short_description_contains_correct_value(self):
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            short_description="Een muziekgenre",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        self.assertEqual(data["short_description"]["nl"], "Een muziekgenre")

    def test_url_title_is_dict(self):
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            url_title="muziek-genre",
        )
        data = TagSerializer(self.tag).data
        self.assertIsInstance(data["url_title"], dict)

    def test_url_title_contains_correct_value(self):
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            url_title="muziek-genre",
        )
        data = TagSerializer(self.tag).data
        self.assertEqual(data["url_title"]["nl"], "muziek-genre")

    def test_name_is_empty_dict_when_no_translations(self):
        data = TagSerializer(self.tag).data
        self.assertEqual(data["name"], {})

    def test_short_description_is_empty_dict_when_no_translations(self):
        data = TagSerializer(self.tag).data
        self.assertEqual(data["short_description"], {})

    def test_url_title_is_empty_dict_when_no_translations(self):
        data = TagSerializer(self.tag).data
        self.assertEqual(data["url_title"], {})

    def test_blank_short_description_is_excluded_from_dict(self):
        """Translations with blank short_description should not appear as a key."""
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            short_description="",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        self.assertNotIn("nl", data["short_description"])

    def test_multiple_translations_all_included(self):
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre NL",
            url_title="genre-nl",
        )
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.en,
            name="Genre EN",
            url_title="genre-en",
        )
        data = TagSerializer(self.tag).data
        self.assertEqual(len(data["name"]), 2)


# ---------------------------------------------------------------------------
# Serialization — queryset
# ---------------------------------------------------------------------------


class TestTagSerializerQueryset(TestCase):
    def test_serializes_queryset_of_tags(self):
        TagFactory.create(type="genre")
        TagFactory.create(type="mood")
        serializer = TagSerializer(Tag.objects.all(), many=True)
        types = [item["type"] for item in serializer.data]
        self.assertIn("genre", types)
        self.assertIn("mood", types)


# ---------------------------------------------------------------------------
# Deserialization / validation
# ---------------------------------------------------------------------------


class TestTagSerializerDeserialization(TestCase):
    """dict → model (create / update)."""

    def _valid_payload(self, **overrides):
        payload = {
            "type": "genre",
            "source": "system",
            "source_type": "internal",
            "is_external": False,
            "is_enabled": True,
        }
        payload.update(overrides)
        return payload

    def test_valid_data_is_valid(self):
        serializer = TagSerializer(data=self._valid_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_data_saves_to_db(self):
        serializer = TagSerializer(data=self._valid_payload(type="mood"))
        self.assertTrue(serializer.is_valid())
        tag = serializer.save()
        self.assertTrue(Tag.objects.filter(id=tag.id).exists())

    def test_saved_tag_has_correct_type(self):
        serializer = TagSerializer(data=self._valid_payload(type="theme"))
        self.assertTrue(serializer.is_valid())
        tag = serializer.save()
        self.assertEqual(tag.type, "theme")

    def test_is_enabled_false_is_saved_correctly(self):
        serializer = TagSerializer(data=self._valid_payload(is_enabled=False))
        self.assertTrue(serializer.is_valid())
        tag = serializer.save()
        self.assertFalse(tag.is_enabled)

    def test_optional_url_field_can_be_omitted(self):
        payload = self._valid_payload()
        payload.pop("url", None)
        serializer = TagSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_optional_url_field_can_be_provided(self):
        payload = self._valid_payload(url="https://example.com/genre")
        serializer = TagSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_partial_update_with_single_field(self):
        tag = TagFactory.create(type="genre", is_enabled=True)
        serializer = TagSerializer(tag, data={"is_enabled": False}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertFalse(updated.is_enabled)

    def test_partial_update_does_not_touch_other_fields(self):
        tag = TagFactory.create(type="genre", source="manual")
        serializer = TagSerializer(tag, data={"is_enabled": False}, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.source, "manual")


def _display_ctx():
    factory = APIRequestFactory()
    return {"request": factory.get("/dummy")}


class TestTagDisplayNameBaseLanguage:
    """Verify whether display_name uses base language with a sensible fallback."""

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_uses_base_language_when_present(self):
        en = Language.objects.create(code="en", name="English")
        nl = Language.objects.create(code="nl", name="Dutch")

        tag = Tag.objects.create(
            url="",
            source="system",
            source_type="",
            type="theme",
            is_external=False,
            is_enabled=True,
        )
        TagTranslation.objects.create(
            tag=tag, language=nl, name="Thema", short_description="", url_title=""
        )
        TagTranslation.objects.create(
            tag=tag, language=en, name="Theme", short_description="", url_title=""
        )

        data = TagSerializer(tag, context=_display_ctx()).data
        assert data["display_name"] == "Theme"

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_falls_back_when_base_language_missing(self):
        nl = Language.objects.create(code="nl", name="Dutch")

        tag = Tag.objects.create(
            url="",
            source="system",
            source_type="",
            type="theme",
            is_external=False,
            is_enabled=True,
        )
        TagTranslation.objects.create(
            tag=tag, language=nl, name="Thema", short_description="", url_title=""
        )

        data = TagSerializer(tag, context=_display_ctx()).data
        assert data["display_name"] == "Thema"
