"""
Tests for apps/locations/serializers.py

Covers:
- Field exposure for LocationSerializer, SpaceSerializer, HallSerializer
- Translation rendering via TranslatableSerializerMixin
- Queryset serialization for many=True
"""

import pytest
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from apps.languages.models import Language
from apps.locations.models import Hall, HallTranslation, Location, Space
from apps.locations.serializers import (
    HallSerializer,
    LocationSerializer,
    SpaceSerializer,
)
from tests.factories.language import LanguageFactory
from tests.factories.location import (
    HallFactory,
    HallTranslationFactory,
    LocationFactory,
    LocationTranslationFactory,
    SpaceFactory,
    SpaceTranslationFactory,
)


class TestLocationSerializerFields(TestCase):
    """Field exposure for LocationSerializer."""

    def setUp(self):
        self.location = LocationFactory()

    def test_expected_fields_present(self):
        data = LocationSerializer(self.location).data
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "street",
                "number",
                "postal_code",
                "city",
                "country",
                "phone_1",
                "phone_2",
                "is_own_location",
                "name",
                "display_name",
            },
        )


class TestLocationSerializerTranslations(TestCase):
    """Translation rendering for LocationSerializer."""

    def setUp(self):
        self.lang_en = LanguageFactory(code="en", name="English")
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")
        self.location = LocationFactory()
        LocationTranslationFactory(location=self.location, language=self.lang_en, name="Main Hall")
        LocationTranslationFactory(location=self.location, language=self.lang_nl, name="Hoofdzaal")

    def test_translated_name_dict(self):
        data = LocationSerializer(self.location).data
        self.assertEqual(data["name"], {"en": "Main Hall", "nl": "Hoofdzaal"})

    def test_queryset_serialization_many(self):
        data = LocationSerializer(Location.objects.all(), many=True).data
        self.assertIsInstance(data, list)
        self.assertIsInstance(data[0]["name"], dict)


class TestSpaceSerializerFields(TestCase):
    """Field exposure for SpaceSerializer."""

    def setUp(self):
        self.space = SpaceFactory()

    def test_expected_fields_present(self):
        data = SpaceSerializer(self.space).data
        self.assertEqual(set(data.keys()), {"id", "location", "name", "display_name"})


class TestSpaceSerializerTranslations(TestCase):
    """Translation rendering for SpaceSerializer."""

    def setUp(self):
        self.lang = LanguageFactory(code="en")
        self.space = SpaceFactory()
        SpaceTranslationFactory(space=self.space, language=self.lang, name="Room A")

    def test_translated_name_dict(self):
        data = SpaceSerializer(self.space).data
        self.assertEqual(data["name"], {"en": "Room A"})


class TestHallSerializerFields(TestCase):
    """Field exposure for HallSerializer."""

    def setUp(self):
        self.hall = HallFactory()

    def test_expected_fields_present(self):
        data = HallSerializer(self.hall).data
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "space",
                "seat_selection",
                "open_seating",
                "name",
                "display_name",
                "remark",
            },
        )


class TestHallSerializerTranslations(TestCase):
    """Translation rendering for HallSerializer."""

    def setUp(self):
        self.lang_en = LanguageFactory(code="en")
        self.lang_fr = LanguageFactory(code="fr")
        self.hall = HallFactory()
        HallTranslationFactory(
            hall=self.hall,
            language=self.lang_en,
            name="Blue Hall",
            remark="Front stage",
        )
        HallTranslationFactory(
            hall=self.hall,
            language=self.lang_fr,
            name="Salle Bleue",
            remark="Avant scène",
        )

    def test_translated_name_and_remark_dicts(self):
        data = HallSerializer(self.hall).data
        self.assertEqual(data["name"], {"en": "Blue Hall", "fr": "Salle Bleue"})
        self.assertEqual(data["remark"], {"en": "Front stage", "fr": "Avant scène"})


def _make_hall():
    loc = Location.objects.create(
        street="Main St",
        number="1",
        postal_code="9000",
        city="Ghent",
        country="BE",
        phone_1=None,
        phone_2=None,
        is_own_location=False,
    )
    space = Space.objects.create(location=loc)
    return Hall.objects.create(space=space, seat_selection=False, open_seating=True)


def _display_ctx():
    factory = APIRequestFactory()
    return {"request": factory.get("/dummy")}


class TestHallDisplayNameBaseLanguage:
    """Verify whether Hall's display_name uses base language."""

    @pytest.mark.django_db
    @override_settings(LANGUAGE_CODE="en-us")
    def test_uses_base_language_when_present(self):
        en = Language.objects.create(code="en", name="English")
        nl = Language.objects.create(code="nl", name="Dutch")

        hall = _make_hall()
        HallTranslation.objects.create(hall=hall, language=nl, name="Grote Zaal", remark="Opmerking NL")
        HallTranslation.objects.create(hall=hall, language=en, name="Main Hall", remark="Remark EN")

        data = HallSerializer(hall, context=_display_ctx()).data
        assert data["display_name"] == "Main Hall"
