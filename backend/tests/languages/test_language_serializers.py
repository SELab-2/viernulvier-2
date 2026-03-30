"""
Tests for apps/languages/serializers.py

Covers:
- LanguageSerializer serialization (model -> dict)
- LanguageSerializer deserialization / validation (dict -> model)
- Field presence and types
- Read/write field behavior
- Invalid data handling
"""

from django.test import TestCase

from apps.languages.models import Language
from apps.languages.serializers import LanguageSerializer
from tests.factories.language import LanguageFactory


class TestLanguageSerializerFields(TestCase):
    """Verify that the correct fields are exposed."""

    def setUp(self) -> None:
        self.lang = LanguageFactory.build(code="nl", name="Dutch", is_active=True)

    def test_expected_fields_are_present(self) -> None:
        serializer = LanguageSerializer(self.lang)
        data = serializer.data
        assert "code" in data
        assert "name" in data
        assert "is_active" in data

    def test_no_extra_fields_are_exposed(self) -> None:
        serializer = LanguageSerializer(self.lang)
        assert set(serializer.data.keys()) == {"code", "name", "is_active"}


class TestLanguageSerializerSerialization(TestCase):
    """Model -> dict serialization."""

    def test_serializes_active_language_correctly(self) -> None:
        lang = LanguageFactory(code="nl", name="Dutch", is_active=True)
        serializer = LanguageSerializer(lang)
        assert serializer.data["code"] == "nl"
        assert serializer.data["name"] == "Dutch"
        assert serializer.data["is_active"]

    def test_serializes_inactive_language_correctly(self) -> None:
        lang = LanguageFactory(code="la", name="Latin", is_active=False)
        serializer = LanguageSerializer(lang)
        assert not serializer.data["is_active"]

    def test_serializes_queryset(self) -> None:
        LanguageFactory(code="nl", name="Dutch", is_active=True)
        LanguageFactory(code="en", name="English", is_active=True)
        serializer = LanguageSerializer(Language.objects.all(), many=True)
        codes = [item["code"] for item in serializer.data]
        assert "nl" in codes
        assert "en" in codes

    def test_code_is_string(self) -> None:
        lang = LanguageFactory(code="en", name="English", is_active=True)
        data = LanguageSerializer(lang).data
        assert isinstance(data["code"], str)

    def test_name_is_string(self) -> None:
        lang = LanguageFactory(code="en", name="English", is_active=True)
        data = LanguageSerializer(lang).data
        assert isinstance(data["name"], str)

    def test_is_active_is_bool(self) -> None:
        lang = LanguageFactory(code="en", name="English", is_active=True)
        data = LanguageSerializer(lang).data
        assert isinstance(data["is_active"], bool)


class TestLanguageSerializerDeserialization(TestCase):
    """dict -> model (create / update)."""

    # -- Valid data -----------------------------------------------------------

    def test_valid_data_is_valid(self) -> None:
        data = {"code": "nl", "name": "Dutch", "is_active": True}
        serializer = LanguageSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_data_saves_to_db(self) -> None:
        data = {"code": "nl", "name": "Dutch", "is_active": True}
        serializer = LanguageSerializer(data=data)
        assert serializer.is_valid()
        serializer.save()
        assert Language.objects.get(code="nl").name == "Dutch"

    def test_is_active_defaults_or_is_provided(self) -> None:
        """is_active can be provided as True or False."""
        for val in (True, False):
            data = {"code": f"t{int(val)}", "name": f"Lang {val}", "is_active": val}
            s = LanguageSerializer(data=data)
            assert s.is_valid(), s.errors
            lang = s.save()
            assert lang.is_active == val

    # -- Invalid data ---------------------------------------------------------

    def test_missing_code_is_invalid(self) -> None:
        data = {"name": "Dutch", "is_active": True}
        serializer = LanguageSerializer(data=data)
        assert not serializer.is_valid()
        assert "code" in serializer.errors

    def test_missing_name_is_invalid(self) -> None:
        data = {"code": "nl", "is_active": True}
        serializer = LanguageSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_empty_code_is_invalid(self) -> None:
        data = {"code": "", "name": "Dutch", "is_active": True}
        serializer = LanguageSerializer(data=data)
        assert not serializer.is_valid()
        assert "code" in serializer.errors

    def test_empty_name_is_invalid(self) -> None:
        data = {"code": "nl", "name": "", "is_active": True}
        serializer = LanguageSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_duplicate_code_is_invalid(self) -> None:
        LanguageFactory(code="nl", name="Dutch", is_active=True)
        data = {"code": "nl", "name": "Nederlands", "is_active": True}
        serializer = LanguageSerializer(data=data)
        assert not serializer.is_valid()
        assert "code" in serializer.errors

    # -- Partial update -------------------------------------------------------

    def test_partial_update_name_only(self) -> None:
        lang = LanguageFactory(code="nl", name="Dutch", is_active=True)
        serializer = LanguageSerializer(lang, data={"name": "Nederlands"}, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.name == "Nederlands"
        assert updated.code == "nl"  # unchanged

    def test_partial_update_is_active_only(self) -> None:
        lang = LanguageFactory(code="nl", name="Dutch", is_active=True)
        serializer = LanguageSerializer(lang, data={"is_active": False}, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert not updated.is_active
