"""
Tests for apps/genres/serializers.py

Covers:
- GenreUseAsSerializer serialization/deserialization
- GenreSerializer serialization/deserialization
- GenreTranslationSerializer serialization/deserialization
- Field presence and types
- Invalid data handling
"""

import pytest
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from apps.genres.models import Genre, GenreTranslation, GenreUseAs
from apps.genres.serializers import (
    GenreSerializer,
    GenreUseAsSerializer,
)
from apps.languages.models import Language
from tests.factories.genre import (
    GenreFactory,
    GenreTranslationFactory,
    GenreUseAsFactory,
)
from tests.factories.language import LanguageFactory


class TestGenreUseAsSerializerFields(TestCase):
    """Field exposure for GenreUseAsSerializer."""

    def setUp(self):
        self.use_as = GenreUseAsFactory(name="genre")

    def test_expected_fields_are_present(self):
        data = GenreUseAsSerializer(self.use_as).data

        self.assertEqual(set(data.keys()), {"id", "name"})
        self.assertEqual(data["name"], "genre")
        self.assertIsInstance(data["id"], int)


class TestGenreUseAsSerializerSerialization(TestCase):
    """Model -> dict serialization for GenreUseAsSerializer."""

    def test_serializes_instance(self):
        use_as = GenreUseAsFactory(name="tag")
        data = GenreUseAsSerializer(use_as).data

        self.assertEqual(data["name"], "tag")
        self.assertIsInstance(data["id"], int)

    def test_serializes_queryset(self):
        GenreUseAsFactory(name="tag")
        GenreUseAsFactory(name="genre")

        data = GenreUseAsSerializer(GenreUseAs.objects.all(), many=True).data
        names = {item["name"] for item in data}

        self.assertIn("tag", names)
        self.assertIn("genre", names)


class TestGenreUseAsSerializerDeserialization(TestCase):
    """dict -> model validation for GenreUseAsSerializer."""

    def test_valid_data_creates(self):
        serializer = GenreUseAsSerializer(data={"name": "genre"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        instance = serializer.save()
        self.assertEqual(instance.name, "genre")

    def test_missing_name_is_invalid(self):
        serializer = GenreUseAsSerializer(data={})

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_empty_name_is_invalid(self):
        serializer = GenreUseAsSerializer(data={"name": ""})

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)


class TestGenreSerializerFields(TestCase):
    """Field exposure for GenreSerializer."""

    def setUp(self):
        self.use_as = GenreUseAsFactory(name="genre")
        self.genre = GenreFactory(type="Theater", use_as=self.use_as)

    def test_expected_fields_are_present(self):
        data = GenreSerializer(self.genre).data
        self.assertEqual(
            set(data.keys()),
            {"id", "type", "use_as", "name", "display_name", "vendor_id"},
        )


class TestGenreSerializerSerialization(TestCase):
    """Model -> dict serialization for GenreSerializer."""

    def setUp(self):
        self.use_as = GenreUseAsFactory(name="genre")
        self.lang_en = LanguageFactory(code="en", name="English")
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")

    def test_serializes_instance(self):
        genre = GenreFactory(type="Theater", use_as=self.use_as)
        GenreTranslationFactory(name="Theatre", language=self.lang_en, genre=genre)
        GenreTranslationFactory(name="Theater", language=self.lang_nl, genre=genre)

        data = GenreSerializer(genre).data

        self.assertEqual(data["type"], "Theater")
        self.assertEqual(data["use_as"]["id"], self.use_as.id)
        self.assertIsInstance(data["id"], int)
        self.assertEqual(data["name"], {"en": "Theatre", "nl": "Theater"})

    def test_serializes_queryset(self):
        g1 = GenreFactory(type="Festival", use_as=self.use_as)
        g2 = GenreFactory(type="Concert", use_as=self.use_as)

        GenreTranslationFactory(name="Festival", language=self.lang_en, genre=g1)
        GenreTranslationFactory(name="Concert", language=self.lang_en, genre=g2)

        data = GenreSerializer(Genre.objects.all(), many=True).data
        types = {item["type"] for item in data}

        self.assertIn("Festival", types)
        self.assertIn("Concert", types)
        # name field is a dict, ensure present and keyed by language
        for item in data:
            self.assertIsInstance(item["name"], dict)


class TestGenreSerializerDeserialization(TestCase):
    """dict -> model validation for GenreSerializer."""

    def setUp(self):
        self.use_as = GenreUseAsFactory(name="genre")
        self.lang_en = LanguageFactory(code="en", name="English")

    def test_valid_data_creates(self):
        serializer = GenreSerializer(data={"type": "Theater", "use_as": self.use_as.id})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        instance = serializer.save()
        self.assertEqual(instance.type, "Theater")
        self.assertEqual(instance.use_as, self.use_as)
        # name is read-only (computed), so not required in input

    def test_missing_type_is_invalid(self):
        serializer = GenreSerializer(data={"use_as": self.use_as.id})

        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_missing_use_as_is_invalid(self):
        serializer = GenreSerializer(data={"type": "Concert"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("use_as", serializer.errors)

    def test_empty_type_is_invalid(self):
        serializer = GenreSerializer(data={"type": "", "use_as": self.use_as.id})

        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_partial_update_type_only(self):
        genre = GenreFactory(type="Concert", use_as=self.use_as)
        serializer = GenreSerializer(genre, data={"type": "Festival"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated = serializer.save()
        self.assertEqual(updated.type, "Festival")
        self.assertEqual(updated.use_as, self.use_as)


def _display_ctx():
    factory = APIRequestFactory()
    return {"request": factory.get("/dummy")}


class TestGenreDisplayNameBaseLanguage:
    """Verify whether display_name uses base language with a sensible fallback."""

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_uses_base_language_when_present(self):
        en = Language.objects.create(code="en", name="English")
        nl = Language.objects.create(code="nl", name="Dutch")

        use_as = GenreUseAs.objects.create(name="genre")
        genre = Genre.objects.create(type="festival", use_as=use_as)

        GenreTranslation.objects.create(genre=genre, language=nl, name="Feest")
        GenreTranslation.objects.create(genre=genre, language=en, name="Festival")

        data = GenreSerializer(genre, context=_display_ctx()).data
        assert data["display_name"] == "Festival"

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_falls_back_when_base_language_missing(self):
        nl = Language.objects.create(code="nl", name="Dutch")

        use_as = GenreUseAs.objects.create(name="genre")
        genre = Genre.objects.create(type="festival", use_as=use_as)
        GenreTranslation.objects.create(genre=genre, language=nl, name="Feest")

        data = GenreSerializer(genre, context=_display_ctx()).data
        assert data["display_name"] == "Feest"
