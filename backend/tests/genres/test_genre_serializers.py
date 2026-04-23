"""
Tests for apps/genres/serializers.py

Covers:
- GenreSerializer serialization/deserialization
- Field presence and types
- Invalid data handling
"""

from django.test import TestCase, override_settings
import pytest
from rest_framework.test import APIRequestFactory

from apps.genres.models import Genre, GenreTranslation
from apps.genres.serializers import (
    GenreSerializer,
)
from apps.languages.models import Language
from tests.factories.genre import (
    GenreFactory,
    GenreTranslationFactory,
)
from tests.factories.language import LanguageFactory


class TestGenreSerializerFields(TestCase):
    """Field exposure for GenreSerializer."""

    def setUp(self) -> None:
        self.genre = GenreFactory(type="Theater")

    def test_expected_fields_are_present(self) -> None:
        data = GenreSerializer(self.genre).data
        assert set(data.keys()) == {"id", "type", "name", "display_name", "vendor_id"}


class TestGenreSerializerSerialization(TestCase):
    """Model -> dict serialization for GenreSerializer."""

    def setUp(self) -> None:
        self.lang_en = LanguageFactory(code="en", name="English")
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")

    def test_serializes_instance(self) -> None:
        genre = GenreFactory(type="Theater")
        GenreTranslationFactory(name="Theatre", language=self.lang_en, genre=genre)
        GenreTranslationFactory(name="Theater", language=self.lang_nl, genre=genre)

        data = GenreSerializer(genre).data

        assert data["type"] == "Theater"
        assert isinstance(data["id"], int)
        assert data["name"] == {"en": "Theatre", "nl": "Theater"}

    def test_serializes_queryset(self) -> None:
        g1 = GenreFactory(type="Festival")
        g2 = GenreFactory(type="Concert")

        GenreTranslationFactory(name="Festival", language=self.lang_en, genre=g1)
        GenreTranslationFactory(name="Concert", language=self.lang_en, genre=g2)

        data = GenreSerializer(Genre.objects.all(), many=True).data
        types = {item["type"] for item in data}

        assert "Festival" in types
        assert "Concert" in types
        # name field is a dict, ensure present and keyed by language
        for item in data:
            assert isinstance(item["name"], dict)


class TestGenreSerializerDeserialization(TestCase):
    """dict -> model validation for GenreSerializer."""

    def setUp(self) -> None:
        self.lang_en = LanguageFactory(code="en", name="English")

    def test_valid_data_creates(self) -> None:
        serializer = GenreSerializer(data={"type": "Theater"})
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.type == "Theater"
        # name is read-only (computed), so not required in input

    def test_missing_type_is_invalid(self) -> None:
        serializer = GenreSerializer(data={})

        assert not serializer.is_valid()
        assert "type" in serializer.errors

    def test_empty_type_is_invalid(self) -> None:
        serializer = GenreSerializer(data={"type": ""})

        assert not serializer.is_valid()
        assert "type" in serializer.errors

    def test_partial_update_type_only(self) -> None:
        genre = GenreFactory(type="Concert")
        serializer = GenreSerializer(genre, data={"type": "Festival"}, partial=True)
        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()
        assert updated.type == "Festival"


def _display_ctx():
    factory = APIRequestFactory()
    return {"request": factory.get("/dummy")}


class TestGenreDisplayNameBaseLanguage:
    """Verify whether display_name uses base language with a sensible fallback."""

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_uses_base_language_when_present(self) -> None:
        en = Language.objects.create(code="en", name="English")
        nl = Language.objects.create(code="nl", name="Dutch")

        genre = Genre.objects.create(type="festival")

        GenreTranslation.objects.create(genre=genre, language=nl, name="Feest")
        GenreTranslation.objects.create(genre=genre, language=en, name="Festival")

        data = GenreSerializer(genre, context=_display_ctx()).data
        assert data["display_name"] == "Festival"

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_falls_back_when_base_language_missing(self) -> None:
        nl = Language.objects.create(code="nl", name="Dutch")

        genre = Genre.objects.create(type="festival")
        GenreTranslation.objects.create(genre=genre, language=nl, name="Feest")

        data = GenreSerializer(genre, context=_display_ctx()).data
        assert data["display_name"] == "Feest"
