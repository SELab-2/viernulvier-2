from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from apps.languages.models import Language
from apps.pricing.models import Price, PriceTranslation, PriceRank, PriceRankTranslation
from apps.pricing.serializers import (
    PriceSerializer,
    PriceTranslationSerializer,
    PriceRankSerializer,
    PriceRankTranslationSerializer,
)


class PriceTranslationSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lang_en = Language.objects.create(code="en", name="English")
        cls.lang_nl = Language.objects.create(code="nl", name="Nederlands")
        cls.price = Price.objects.create(
            type="Standard",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
        )

    def test_price_translation_serializer_accepts_language_code(self):
        data = {
            "price": self.price.id,
            "language": "en",
            "description": "Standard ticket",
        }
        ser = PriceTranslationSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)

        obj = ser.save()
        self.assertEqual(obj.language.code, "en")
        self.assertEqual(obj.description, "Standard ticket")

    def test_price_translation_serializer_unique_together_validator(self):
        PriceTranslation.objects.create(
            price=self.price, language=self.lang_en, description="Standard ticket"
        )

        data = {
            "price": self.price.id,
            "language": "en",
            "description": "Duplicate",
        }
        ser = PriceTranslationSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertTrue(any("non_field_errors" in ser.errors for _ in [0]) or ser.errors)


class PriceSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.lang_en = Language.objects.create(code="en", name="English")
        cls.lang_nl = Language.objects.create(code="nl", name="Nederlands")

        cls.price = Price.objects.create(
            type="Standard",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
        )
        PriceTranslation.objects.create(
            price=cls.price, language=cls.lang_en, description="Standard ticket"
        )
        PriceTranslation.objects.create(
            price=cls.price, language=cls.lang_nl, description="Standaard ticket"
        )

    def _drf_request(self, path: str):
        django_req = self.factory.get(path)
        return Request(django_req)

    def test_price_serializer_description_prefers_requested_lang(self):
        request = self._drf_request("/dummy?lang=nl")
        ser = PriceSerializer(instance=self.price, context={"request": request})
        self.assertEqual(ser.data["description"], "Standaard ticket")

    def test_price_serializer_description_falls_back_to_first_non_empty(self):
        request = self._drf_request("/dummy")
        ser = PriceSerializer(instance=self.price, context={"request": request})
        self.assertIn(ser.data["description"], {"Standard ticket", "Standaard ticket"})

    def test_price_serializer_description_returns_empty_if_no_translations(self):
        p2 = Price.objects.create(
            type="NoTrans",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=1,
        )
        request = self._drf_request("/dummy?lang=en")
        ser = PriceSerializer(instance=p2, context={"request": request})
        self.assertEqual(ser.data["description"], "")

    def test_price_serializer_includes_translations_read_only(self):
        request = self._drf_request("/dummy?lang=en")
        ser = PriceSerializer(instance=self.price, context={"request": request})
        self.assertIn("translations", ser.data)
        self.assertEqual(len(ser.data["translations"]), 2)


class PriceRankSerializerTests(TestCase):
    def test_price_rank_serializer_unique_position_validator(self):
        PriceRank.objects.create(position=1, sold_out_buffer=0)

        ser = PriceRankSerializer(data={"position": 1, "sold_out_buffer": 0})
        self.assertFalse(ser.is_valid())
        self.assertTrue(ser.errors)


class PriceRankTranslationSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lang_en = Language.objects.create(code="en", name="English")
        cls.rank = PriceRank.objects.create(position=1, sold_out_buffer=0)

    def test_price_rank_translation_serializer_accepts_language_code(self):
        data = {
            "price_rank": self.rank.id,
            "language": "en",
            "description": "First rank",
        }
        ser = PriceRankTranslationSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)

        obj = ser.save()
        self.assertEqual(obj.language.code, "en")

    def test_price_rank_translation_serializer_unique_together_validator(self):
        PriceRankTranslation.objects.create(
            price_rank=self.rank, language=self.lang_en, description="First rank"
        )

        data = {
            "price_rank": self.rank.id,
            "language": "en",
            "description": "Duplicate",
        }
        ser = PriceRankTranslationSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertTrue(ser.errors)