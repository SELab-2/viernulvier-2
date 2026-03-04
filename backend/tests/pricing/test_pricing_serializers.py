"""
Covers:
- PriceSerializer serialization (model -> dict)
- PriceSerializer description translation behavior (dict of translations)
- PriceSerializer deserialization / validation (dict -> model)
- Field presence and types
- Read/write field behavior
- Invalid data handling
- Partial updates
- PriceRankSerializer validation (unique position)
"""

import pytest
from rest_framework.test import APIRequestFactory
from django.test import TestCase, override_settings
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from apps.languages.models import Language
from apps.pricing.models import Price, PriceTranslation, PriceRank, PriceRankTranslation
from apps.pricing.serializers import PriceSerializer, PriceRankSerializer


def _drf_request(factory: APIRequestFactory, path: str) -> Request:
    django_req = factory.get(path)
    return Request(django_req)


class TestPriceSerializerFields(TestCase):
    """Verify that the correct fields are exposed."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.lang_en = Language.objects.create(code="en", name="English")

        cls.price = Price.objects.create(
            type="Standard",
            visibility="public",
            membership="Member",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
            cineville_box=False,
        )
        PriceTranslation.objects.create(
            price=cls.price,
            language=cls.lang_en,
            description="Standard ticket",
        )

    def _drf_request(self, path: str) -> Request:
        django_req = self.factory.get(path)
        return Request(django_req)

    def test_expected_fields_are_present(self):
        """Test case for test_expected_fields_are_present."""
        serializer = PriceSerializer(self.price, context={"request": self._drf_request("/dummy")})
        data = serializer.data

        expected = {
            "id",
            "type",
            "visibility",
            "membership",
            "minimum",
            "maximum",
            "step",
            "sort_order",
            "cineville_box",
            "description",
        }
        for f in expected:
            self.assertIn(f, data)

    def test_translations_field_is_not_exposed(self):
        """Test case for test_translations_field_is_not_exposed."""
        serializer = PriceSerializer(self.price, context={"request": self._drf_request("/dummy")})
        self.assertNotIn("translations", serializer.data)

    def test_no_extra_fields_are_exposed(self):
        """Test case for test_no_extra_fields_are_exposed."""
        serializer = PriceSerializer(self.price, context={"request": self._drf_request("/dummy")})
        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "type",
                "visibility",
                "membership",
                "minimum",
                "maximum",
                "step",
                "sort_order",
                "cineville_box",
                "description",
                "display_description"
            },
        )


class TestPriceSerializerSerialization(TestCase):
    """Model → dict serialization."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.lang_en = Language.objects.create(code="en", name="English")
        cls.lang_nl = Language.objects.create(code="nl", name="Nederlands")

        cls.price = Price.objects.create(
            type="Standard",
            visibility="public",
            membership="Member",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
            cineville_box=False,
        )

        PriceTranslation.objects.create(price=cls.price, language=cls.lang_en, description="Standard ticket")
        PriceTranslation.objects.create(price=cls.price, language=cls.lang_nl, description="Standaard ticket")

    def test_serializes_price_core_fields(self):
        """Test case for test_serializes_price_core_fields."""
        serializer = PriceSerializer(self.price, context={"request": _drf_request(self.factory, "/dummy")})
        data = serializer.data

        self.assertEqual(data["type"], "Standard")
        self.assertEqual(data["visibility"], "public")
        self.assertEqual(data["membership"], "Member")
        self.assertIsNone(data["minimum"])
        self.assertIsNone(data["maximum"])
        self.assertIsNone(data["step"])
        self.assertEqual(data["sort_order"], 0)
        self.assertIsInstance(data["cineville_box"], bool)

    def test_description_is_dict(self):
        """Test case for test_description_is_dict."""
        serializer = PriceSerializer(self.price, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertIsInstance(serializer.data["description"], dict)

    def test_description_contains_all_translations(self):
        """Test case for test_description_contains_all_translations."""
        serializer = PriceSerializer(self.price, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertEqual(
            serializer.data["description"],
            {"en": "Standard ticket", "nl": "Standaard ticket"},
        )

    def test_description_with_requested_lang_still_returns_dict(self):
        """Test case for test_description_with_requested_lang_still_returns_dict."""
        serializer = PriceSerializer(self.price, context={"request": _drf_request(self.factory, "/dummy?lang=nl")})
        self.assertEqual(
            serializer.data["description"],
            {"en": "Standard ticket", "nl": "Standaard ticket"},
        )

    def test_serializes_queryset(self):
        """Test case for test_serializes_queryset."""
        Price.objects.create(
            type="Other",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=1,
            cineville_box=False,
        )
        serializer = PriceSerializer(
            Price.objects.all().order_by("sort_order"),
            many=True,
            context={"request": _drf_request(self.factory, "/dummy")},
        )
        types = [item["type"] for item in serializer.data]
        self.assertIn("Standard", types)
        self.assertIn("Other", types)

    def test_type_visibility_membership_are_strings(self):
        """Test case for test_type_visibility_membership_are_strings."""
        serializer = PriceSerializer(self.price, context={"request": _drf_request(self.factory, "/dummy")})
        data = serializer.data
        self.assertIsInstance(data["type"], str)
        self.assertIsInstance(data["visibility"], str)
        self.assertIsInstance(data["membership"], str)

    def test_sort_order_is_int(self):
        """Test case for test_sort_order_is_int."""
        serializer = PriceSerializer(self.price, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertIsInstance(serializer.data["sort_order"], int)


class TestPriceSerializerTranslationEdgeCases(TestCase):
    """Edge cases for translation dict output."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.lang_en = Language.objects.create(code="en", name="English")
        cls.lang_nl = Language.objects.create(code="nl", name="Nederlands")

    def test_description_empty_dict_if_no_translations(self):
        """Test case for test_description_empty_dict_if_no_translations."""
        price = Price.objects.create(
            type="NoTrans",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
            cineville_box=False,
        )
        serializer = PriceSerializer(price, context={"request": _drf_request(self.factory, "/dummy?lang=en")})
        self.assertEqual(serializer.data["description"], {})

    def test_description_skips_missing_language_keys(self):
        """Test case for test_description_skips_missing_language_keys."""
        """
        If only one translation exists, the dict contains only that language.
        """
        price = Price.objects.create(
            type="OneTrans",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
            cineville_box=False,
        )
        PriceTranslation.objects.create(price=price, language=self.lang_en, description="Only EN")
        serializer = PriceSerializer(price, context={"request": _drf_request(self.factory, "/dummy?lang=nl")})
        self.assertEqual(serializer.data["description"], {"en": "Only EN"})


class TestPriceSerializerDeserialization(TestCase):
    """dict → model (create / update)."""

    def setUp(self):
        self.factory = APIRequestFactory()

    # -- Valid data -----------------------------------------------------------

    def test_valid_data_is_valid(self):
        """Test case for test_valid_data_is_valid."""
        data = {
            "type": "Standard",
            "visibility": "public",
            "membership": "Member",
            "minimum": None,
            "maximum": None,
            "step": None,
            "sort_order": 0,
            "cineville_box": False,
        }
        serializer = PriceSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_data_saves_to_db(self):
        """Test case for test_valid_data_saves_to_db."""
        data = {
            "type": "Standard",
            "visibility": "public",
            "membership": "Member",
            "minimum": None,
            "maximum": None,
            "step": None,
            "sort_order": 0,
            "cineville_box": False,
        }
        serializer = PriceSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        price = serializer.save()
        self.assertTrue(Price.objects.filter(id=price.id).exists())

    # -- Read-only behavior ---------------------------------------------------

    def test_description_is_read_only(self):
        """Test case for test_description_is_read_only."""
        """
        If `description` is SerializerMethodField, it should not be writable.
        """
        data = {
            "type": "Standard",
            "visibility": "public",
            "membership": "Member",
            "minimum": None,
            "maximum": None,
            "step": None,
            "sort_order": 0,
            "cineville_box": False,
            "description": {"en": "Hacked"},  # should be ignored / not validated as input
        }
        serializer = PriceSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        price = serializer.save()
        # There are no translations created from serializer input; description output remains {}.
        out = PriceSerializer(price, context={"request": _drf_request(self.factory, "/dummy")}).data
        self.assertEqual(out["description"], {})

    # -- Invalid data ---------------------------------------------------------

    def test_missing_type_is_invalid(self):
        """Test case for test_missing_type_is_invalid."""
        data = {
            "visibility": "public",
            "membership": "",
            "sort_order": 0,
            "cineville_box": False,
        }
        serializer = PriceSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_missing_visibility_is_invalid(self):
        """Test case for test_missing_visibility_is_invalid."""
        data = {
            "type": "Standard",
            "membership": "",
            "sort_order": 0,
            "cineville_box": False,
        }
        serializer = PriceSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertFalse(serializer.is_valid())
        self.assertIn("visibility", serializer.errors)

    def test_sort_order_must_be_int(self):
        """Test case for test_sort_order_must_be_int."""
        data = {
            "type": "Standard",
            "visibility": "public",
            "membership": "",
            "sort_order": "not-an-int",
            "cineville_box": False,
        }
        serializer = PriceSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertFalse(serializer.is_valid())
        self.assertIn("sort_order", serializer.errors)

    # -- Partial update -------------------------------------------------------

    def test_partial_update_type_only(self):
        """Test case for test_partial_update_type_only."""
        price = Price.objects.create(
            type="Standard",
            visibility="public",
            membership="Member",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
            cineville_box=False,
        )
        serializer = PriceSerializer(
            price,
            data={"type": "Updated"},
            partial=True,
            context={"request": _drf_request(self.factory, "/dummy")},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.type, "Updated")
        self.assertEqual(updated.visibility, "public")  # unchanged


class TestPriceRankSerializer(TestCase):
    """PriceRankSerializer validation behavior."""

    def test_valid_price_rank_is_valid(self):
        """Test case for test_valid_price_rank_is_valid."""
        serializer = PriceRankSerializer(data={"position": 1, "sold_out_buffer": 0})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_price_rank_saves(self):
        """Test case for test_valid_price_rank_saves."""
        serializer = PriceRankSerializer(data={"position": 1, "sold_out_buffer": 0})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rank = serializer.save()
        self.assertTrue(PriceRank.objects.filter(id=rank.id).exists())

    def test_unique_position_validator(self):
        """Test case for test_unique_position_validator."""
        PriceRank.objects.create(position=1, sold_out_buffer=0)
        serializer = PriceRankSerializer(data={"position": 1, "sold_out_buffer": 0})
        self.assertFalse(serializer.is_valid())
        self.assertIn("position", serializer.errors)

    def test_position_must_be_int(self):
        """Test case for test_position_must_be_int."""
        serializer = PriceRankSerializer(data={"position": "nope", "sold_out_buffer": 0})
        self.assertFalse(serializer.is_valid())
        self.assertIn("position", serializer.errors)


def _display_ctx():
    factory = APIRequestFactory()
    return {"request": factory.get("/dummy")}


class TestPriceRankDisplayDescriptionBaseLanguage:
    """Verify whether display_description uses base language with a sensible fallback."""

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_uses_base_language_when_present(self):
        en = Language.objects.create(code="en", name="English")
        nl = Language.objects.create(code="nl", name="Dutch")

        rank = PriceRank.objects.create(position=1, sold_out_buffer=0)
        PriceRankTranslation.objects.create(price_rank=rank, language=nl, description="Standaard")
        PriceRankTranslation.objects.create(price_rank=rank, language=en, description="Standard")

        data = PriceRankSerializer(rank, context=_display_ctx()).data
        assert data["display_description"] == "Standard"

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_falls_back_when_base_language_missing(self):
        nl = Language.objects.create(code="nl", name="Dutch")

        rank = PriceRank.objects.create(position=1, sold_out_buffer=0)
        PriceRankTranslation.objects.create(price_rank=rank, language=nl, description="Standaard")

        data = PriceRankSerializer(rank, context=_display_ctx()).data
        assert data["display_description"] == "Standaard"