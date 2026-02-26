from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from apps.languages.models import Language
from apps.pricing.models import Price, PriceTranslation, PriceRank
from apps.pricing.serializers import PriceSerializer, PriceRankSerializer


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
        """
        Description is returned as a dict of translations (language_code -> value),
        even when a lang= query param is provided.
        """
        request = self._drf_request("/dummy?lang=nl")
        ser = PriceSerializer(instance=self.price, context={"request": request})

        self.assertEqual(
            ser.data["description"],
            {"en": "Standard ticket", "nl": "Standaard ticket"},
        )

    def test_price_serializer_description_falls_back_to_first_non_empty(self):
        """
        Without a requested language, description is still a dict of translations.
        """
        request = self._drf_request("/dummy")
        ser = PriceSerializer(instance=self.price, context={"request": request})

        self.assertEqual(
            ser.data["description"],
            {"en": "Standard ticket", "nl": "Standaard ticket"},
        )

    def test_price_serializer_description_returns_empty_if_no_translations(self):
        """
        If there are no translations, description is an empty dict.
        """
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

        self.assertEqual(ser.data["description"], {})

    def test_price_serializer_does_not_include_translations_field(self):
        """
        The serializer no longer exposes a separate `translations` field.
        """
        request = self._drf_request("/dummy?lang=en")
        ser = PriceSerializer(instance=self.price, context={"request": request})

        self.assertNotIn("translations", ser.data)


class PriceRankSerializerTests(TestCase):
    def test_price_rank_serializer_unique_position_validator(self):
        PriceRank.objects.create(position=1, sold_out_buffer=0)

        ser = PriceRankSerializer(data={"position": 1, "sold_out_buffer": 0})
        self.assertFalse(ser.is_valid())
        self.assertTrue(ser.errors)