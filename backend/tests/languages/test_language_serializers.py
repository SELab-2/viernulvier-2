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


class TestLanguageSerializerFields(TestCase):
    """Verify that the correct fields are exposed."""

    def setUp(self):
        self.lang = Language(code="nl", name="Dutch", is_active=True)

    def test_expected_fields_are_present(self):
        serializer = LanguageSerializer(self.lang)
        data = serializer.data
        self.assertIn("code", data)
        self.assertIn("name", data)
        self.assertIn("is_active", data)

    def test_no_extra_fields_are_exposed(self):
        serializer = LanguageSerializer(self.lang)
        self.assertEqual(set(serializer.data.keys()), {"code", "name", "is_active"})


class TestLanguageSerializerSerialization(TestCase):
    """Model → dict serialization."""

    def test_serializes_active_language_correctly(self):
        lang = Language.objects.create(code="nl", name="Dutch", is_active=True)
        serializer = LanguageSerializer(lang)
        self.assertEqual(serializer.data["code"], "nl")
        self.assertEqual(serializer.data["name"], "Dutch")
        self.assertTrue(serializer.data["is_active"])

    def test_serializes_inactive_language_correctly(self):
        lang = Language.objects.create(code="la", name="Latin", is_active=False)
        serializer = LanguageSerializer(lang)
        self.assertFalse(serializer.data["is_active"])

    def test_serializes_queryset(self):
        Language.objects.create(code="nl", name="Dutch", is_active=True)
        Language.objects.create(code="en", name="English", is_active=True)
        serializer = LanguageSerializer(Language.objects.all(), many=True)
        codes = [item["code"] for item in serializer.data]
        self.assertIn("nl", codes)
        self.assertIn("en", codes)

    def test_code_is_string(self):
        lang = Language.objects.create(code="en", name="English", is_active=True)
        data = LanguageSerializer(lang).data
        self.assertIsInstance(data["code"], str)

    def test_name_is_string(self):
        lang = Language.objects.create(code="en", name="English", is_active=True)
        data = LanguageSerializer(lang).data
        self.assertIsInstance(data["name"], str)

    def test_is_active_is_bool(self):
        lang = Language.objects.create(code="en", name="English", is_active=True)
        data = LanguageSerializer(lang).data
        self.assertIsInstance(data["is_active"], bool)


class TestLanguageSerializerDeserialization(TestCase):
    """dict → model (create / update)."""

    # -- Valid data -----------------------------------------------------------

    def test_valid_data_is_valid(self):
        data = {"code": "nl", "name": "Dutch", "is_active": True}
        serializer = LanguageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_data_saves_to_db(self):
        data = {"code": "nl", "name": "Dutch", "is_active": True}
        serializer = LanguageSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        _ = serializer.save()
        self.assertEqual(Language.objects.get(code="nl").name, "Dutch")

    def test_is_active_defaults_or_is_provided(self):
        """is_active can be provided as True or False."""
        for val in (True, False):
            data = {"code": f"t{int(val)}", "name": f"Lang {val}", "is_active": val}
            s = LanguageSerializer(data=data)
            self.assertTrue(s.is_valid(), s.errors)
            lang = s.save()
            self.assertEqual(lang.is_active, val)

    # -- Invalid data ---------------------------------------------------------

    def test_missing_code_is_invalid(self):
        data = {"name": "Dutch", "is_active": True}
        serializer = LanguageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)

    def test_missing_name_is_invalid(self):
        data = {"code": "nl", "is_active": True}
        serializer = LanguageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_empty_code_is_invalid(self):
        data = {"code": "", "name": "Dutch", "is_active": True}
        serializer = LanguageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)

    def test_empty_name_is_invalid(self):
        data = {"code": "nl", "name": "", "is_active": True}
        serializer = LanguageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_duplicate_code_is_invalid(self):
        Language.objects.create(code="nl", name="Dutch", is_active=True)
        data = {"code": "nl", "name": "Nederlands", "is_active": True}
        serializer = LanguageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)

    # -- Partial update -------------------------------------------------------

    def test_partial_update_name_only(self):
        lang = Language.objects.create(code="nl", name="Dutch", is_active=True)
        serializer = LanguageSerializer(lang, data={"name": "Nederlands"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.name, "Nederlands")
        self.assertEqual(updated.code, "nl")  # unchanged

    def test_partial_update_is_active_only(self):
        lang = Language.objects.create(code="nl", name="Dutch", is_active=True)
        serializer = LanguageSerializer(lang, data={"is_active": False}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertFalse(updated.is_active)
