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

from django.test import TestCase, override_settings
import pytest
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

    def setUp(self) -> None:
        self.tag = TagFactory.create()

    def test_expected_fields_are_present(self) -> None:
        serializer = TagSerializer(self.tag)
        data = serializer.data
        for field in (
            "id",
            "url",
            "source",
            "type",
            "is_enabled",
            "name",
            "short_description",
            "url_title",
        ):
            assert field in data

    def test_no_extra_fields_are_exposed(self) -> None:
        serializer = TagSerializer(self.tag)
        expected = {
            "id",
            "url",
            "source",
            "type",
            "is_enabled",
            "name",
            "display_name",
            "display_short_description",
            "display_url_title",
            "short_description",
            "url_title",
        }
        assert set(serializer.data.keys()) == expected


# ---------------------------------------------------------------------------
# Serialization - scalar fields
# ---------------------------------------------------------------------------


class TestTagSerializerScalarFields(TestCase):
    """Model -> dict for non-translated fields."""

    def test_serializes_type_correctly(self) -> None:
        tag = TagFactory.create(type="mood")
        data = TagSerializer(tag).data
        assert data["type"] == "mood"

    def test_serializes_source_correctly(self) -> None:
        tag = TagFactory.create(source="external-api")
        data = TagSerializer(tag).data
        assert data["source"] == "external-api"

    def test_serializes_is_enabled_true(self) -> None:
        tag = TagFactory.create(is_enabled=True)
        data = TagSerializer(tag).data
        assert data["is_enabled"]

    def test_serializes_is_enabled_false(self) -> None:
        tag = TagFactory.create(is_enabled=False)
        data = TagSerializer(tag).data
        assert not data["is_enabled"]

    def test_serializes_url_correctly(self) -> None:
        tag = TagFactory.create(url="https://example.com/genre")
        data = TagSerializer(tag).data
        assert data["url"] == "https://example.com/genre"

    def test_type_is_string(self) -> None:
        tag = TagFactory.create(type="genre")
        data = TagSerializer(tag).data
        assert isinstance(data["type"], str)

    def test_is_enabled_is_bool(self) -> None:
        tag = TagFactory.create()
        data = TagSerializer(tag).data
        assert isinstance(data["is_enabled"], bool)


# ---------------------------------------------------------------------------
# Serialization - translated fields
# ---------------------------------------------------------------------------


class TestTagSerializerTranslatedFields(TestCase):
    """name / short_description / url_title are returned as language-keyed dicts."""

    def setUp(self) -> None:
        self.tag = TagFactory.create()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        self.en = LanguageFactory.create(code="en", name="English")

    def test_name_is_dict(self) -> None:
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        assert isinstance(data["name"], dict)

    def test_name_contains_correct_language_keys(self) -> None:
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
        assert "nl" in data["name"]
        assert "en" in data["name"]

    def test_name_contains_correct_values(self) -> None:
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Muziekgenre",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        assert data["name"]["nl"] == "Muziekgenre"

    def test_short_description_is_dict(self) -> None:
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            short_description="Een muziekgenre",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        assert isinstance(data["short_description"], dict)

    def test_short_description_contains_correct_value(self) -> None:
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            short_description="Een muziekgenre",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        assert data["short_description"]["nl"] == "Een muziekgenre"

    def test_url_title_is_dict(self) -> None:
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            url_title="muziek-genre",
        )
        data = TagSerializer(self.tag).data
        assert isinstance(data["url_title"], dict)

    def test_url_title_contains_correct_value(self) -> None:
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            url_title="muziek-genre",
        )
        data = TagSerializer(self.tag).data
        assert data["url_title"]["nl"] == "muziek-genre"

    def test_name_is_empty_dict_when_no_translations(self) -> None:
        data = TagSerializer(self.tag).data
        assert data["name"] == {}

    def test_short_description_is_empty_dict_when_no_translations(self) -> None:
        data = TagSerializer(self.tag).data
        assert data["short_description"] == {}

    def test_url_title_is_empty_dict_when_no_translations(self) -> None:
        data = TagSerializer(self.tag).data
        assert data["url_title"] == {}

    def test_blank_short_description_is_excluded_from_dict(self) -> None:
        """Translations with blank short_description should not appear as a key."""
        TagTranslationFactory.create(
            tag=self.tag,
            language=self.nl,
            name="Genre",
            short_description="",
            url_title="genre",
        )
        data = TagSerializer(self.tag).data
        assert "nl" not in data["short_description"]

    def test_multiple_translations_all_included(self) -> None:
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
        assert len(data["name"]) == 2


# ---------------------------------------------------------------------------
# Serialization - queryset
# ---------------------------------------------------------------------------


class TestTagSerializerQueryset(TestCase):
    def test_serializes_queryset_of_tags(self) -> None:
        TagFactory.create(type="genre")
        TagFactory.create(type="mood")
        serializer = TagSerializer(Tag.objects.all(), many=True)
        types = [item["type"] for item in serializer.data]
        assert "genre" in types
        assert "mood" in types


# ---------------------------------------------------------------------------
# Deserialization / validation
# ---------------------------------------------------------------------------


class TestTagSerializerDeserialization(TestCase):
    """dict -> model (create / update)."""

    def _valid_payload(self, **overrides):
        payload = {
            "type": "genre",
            "source": "system",
            "is_enabled": True,
        }
        payload.update(overrides)
        return payload

    def test_valid_data_is_valid(self) -> None:
        serializer = TagSerializer(data=self._valid_payload())
        assert serializer.is_valid(), serializer.errors

    def test_valid_data_saves_to_db(self) -> None:
        serializer = TagSerializer(data=self._valid_payload(type="mood"))
        assert serializer.is_valid()
        tag = serializer.save()
        assert Tag.objects.filter(id=tag.id).exists()

    def test_saved_tag_has_correct_type(self) -> None:
        serializer = TagSerializer(data=self._valid_payload(type="theme"))
        assert serializer.is_valid()
        tag = serializer.save()
        assert tag.type == "theme"

    def test_is_enabled_false_is_saved_correctly(self) -> None:
        serializer = TagSerializer(data=self._valid_payload(is_enabled=False))
        assert serializer.is_valid()
        tag = serializer.save()
        assert not tag.is_enabled

    def test_optional_url_field_can_be_omitted(self) -> None:
        payload = self._valid_payload()
        payload.pop("url", None)
        serializer = TagSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    def test_optional_url_field_can_be_provided(self) -> None:
        payload = self._valid_payload(url="https://example.com/genre")
        serializer = TagSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    def test_partial_update_with_single_field(self) -> None:
        tag = TagFactory.create(type="genre", is_enabled=True)
        serializer = TagSerializer(tag, data={"is_enabled": False}, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert not updated.is_enabled

    def test_partial_update_does_not_touch_other_fields(self) -> None:
        tag = TagFactory.create(type="genre", source="manual")
        serializer = TagSerializer(tag, data={"is_enabled": False}, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.source == "manual"


def _display_ctx():
    factory = APIRequestFactory()
    return {"request": factory.get("/dummy")}


class TestTagDisplayNameBaseLanguage:
    """Verify whether display_name uses base language with a sensible fallback."""

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_uses_base_language_when_present(self) -> None:
        en = Language.objects.create(code="en", name="English")
        nl = Language.objects.create(code="nl", name="Dutch")

        tag = Tag.objects.create(
            url="",
            source="system",
            type="theme",
            is_enabled=True,
        )
        TagTranslation.objects.create(tag=tag, language=nl, name="Thema", short_description="", url_title="")
        TagTranslation.objects.create(tag=tag, language=en, name="Theme", short_description="", url_title="")

        data = TagSerializer(tag, context=_display_ctx()).data
        assert data["display_name"] == "Theme"

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_falls_back_when_base_language_missing(self) -> None:
        nl = Language.objects.create(code="nl", name="Dutch")

        tag = Tag.objects.create(
            url="",
            source="system",
            type="theme",
            is_enabled=True,
        )
        TagTranslation.objects.create(tag=tag, language=nl, name="Thema", short_description="", url_title="")

        data = TagSerializer(tag, context=_display_ctx()).data
        assert data["display_name"] == "Thema"
