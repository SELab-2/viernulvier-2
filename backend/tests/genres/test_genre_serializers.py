"""
Tests for apps/genres/serializers.py

Covers:
- GenreUseAsSerializer serialization/deserialization
- GenreSerializer serialization/deserialization
- GenreTranslationSerializer serialization/deserialization
- Field presence and types
- Invalid data handling
"""

from django.test import TestCase, override_settings
import pytest
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

    def setUp(self) -> None:
        self.use_as = GenreUseAsFactory(name="genre")

    def test_expected_fields_are_present(self) -> None:
        data = GenreUseAsSerializer(self.use_as).data

        assert set(data.keys()) == {"id", "name"}
        assert data["name"] == "genre"
        assert isinstance(data["id"], int)


class TestGenreUseAsSerializerSerialization(TestCase):
    """Model -> dict serialization for GenreUseAsSerializer."""

    def test_serializes_instance(self) -> None:
        use_as = GenreUseAsFactory(name="tag")
        data = GenreUseAsSerializer(use_as).data

        assert data["name"] == "tag"
        assert isinstance(data["id"], int)

    def test_serializes_queryset(self) -> None:
        GenreUseAsFactory(name="tag")
        GenreUseAsFactory(name="genre")

        data = GenreUseAsSerializer(GenreUseAs.objects.all(), many=True).data
        names = {item["name"] for item in data}

        assert "tag" in names
        assert "genre" in names


class TestGenreUseAsSerializerDeserialization(TestCase):
    """dict -> model validation for GenreUseAsSerializer."""

    def test_valid_data_creates(self) -> None:
        serializer = GenreUseAsSerializer(data={"name": "genre"})
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.name == "genre"

    def test_missing_name_is_invalid(self) -> None:
        serializer = GenreUseAsSerializer(data={})

        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_empty_name_is_invalid(self) -> None:
        serializer = GenreUseAsSerializer(data={"name": ""})

        assert not serializer.is_valid()
        assert "name" in serializer.errors


class TestGenreSerializerFields(TestCase):
    """Field exposure for GenreSerializer."""

    def setUp(self) -> None:
        self.use_as = GenreUseAsFactory(name="genre")
        self.genre = GenreFactory(type="Theater", use_as=self.use_as)

    def test_expected_fields_are_present(self) -> None:
        data = GenreSerializer(self.genre).data
        assert set(data.keys()) == {"id", "type", "use_as", "name", "display_name", "vendor_id"}


class TestGenreSerializerSerialization(TestCase):
    """Model -> dict serialization for GenreSerializer."""

    def setUp(self) -> None:
        self.use_as = GenreUseAsFactory(name="genre")
        self.lang_en = LanguageFactory(code="en", name="English")
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")

    def test_serializes_instance(self) -> None:
        genre = GenreFactory(type="Theater", use_as=self.use_as)
        GenreTranslationFactory(name="Theatre", language=self.lang_en, genre=genre)
        GenreTranslationFactory(name="Theater", language=self.lang_nl, genre=genre)

        data = GenreSerializer(genre).data

        assert data["type"] == "Theater"
        assert data["use_as"]["id"] == self.use_as.id
        assert isinstance(data["id"], int)
        assert data["name"] == {"en": "Theatre", "nl": "Theater"}

    def test_serializes_queryset(self) -> None:
        g1 = GenreFactory(type="Festival", use_as=self.use_as)
        g2 = GenreFactory(type="Concert", use_as=self.use_as)

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
        self.use_as = GenreUseAsFactory(name="genre")
        self.lang_en = LanguageFactory(code="en", name="English")

    def test_valid_data_creates(self) -> None:
        serializer = GenreSerializer(data={"type": "Theater", "use_as_id": self.use_as.id})
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.type == "Theater"
        assert instance.use_as == self.use_as
        # name is read-only (computed), so not required in input

    def test_missing_type_is_invalid(self) -> None:
        serializer = GenreSerializer(data={"use_as_id": self.use_as.id})

        assert not serializer.is_valid()
        assert "type" in serializer.errors

    def test_missing_use_as_id_is_invalid(self) -> None:
        serializer = GenreSerializer(data={"type": "Concert"})

        assert not serializer.is_valid()
        assert "use_as_id" in serializer.errors

    def test_empty_type_is_invalid(self) -> None:
        serializer = GenreSerializer(data={"type": "", "use_as_id": self.use_as.id})

        assert not serializer.is_valid()
        assert "type" in serializer.errors

    def test_partial_update_type_only(self) -> None:
        genre = GenreFactory(type="Concert", use_as=self.use_as)
        serializer = GenreSerializer(genre, data={"type": "Festival"}, partial=True)
        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()
        assert updated.type == "Festival"
        assert updated.use_as == self.use_as


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

        use_as = GenreUseAs.objects.create(name="genre")
        genre = Genre.objects.create(type="festival", use_as=use_as)

        GenreTranslation.objects.create(genre=genre, language=nl, name="Feest")
        GenreTranslation.objects.create(genre=genre, language=en, name="Festival")

        data = GenreSerializer(genre, context=_display_ctx()).data
        assert data["display_name"] == "Festival"

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_falls_back_when_base_language_missing(self) -> None:
        nl = Language.objects.create(code="nl", name="Dutch")

        use_as = GenreUseAs.objects.create(name="genre")
        genre = Genre.objects.create(type="festival", use_as=use_as)
        GenreTranslation.objects.create(genre=genre, language=nl, name="Feest")

        data = GenreSerializer(genre, context=_display_ctx()).data
        assert data["display_name"] == "Feest"
