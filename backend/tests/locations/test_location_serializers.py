"""
Tests for apps/locations/serializers.py

Covers:
- Field exposure for LocationSerializer, SpaceSerializer, HallSerializer
- Translation rendering via TranslatableSerializerMixin
- Queryset serialization for many=True
"""

from django.test import TestCase, override_settings
import pytest
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

    def setUp(self) -> None:
        self.location = LocationFactory()

    def test_expected_fields_present(self) -> None:
        data = LocationSerializer(self.location).data
        assert set(data.keys()) == {
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
        }


class TestLocationSerializerTranslations(TestCase):
    """Translation rendering for LocationSerializer."""

    def setUp(self) -> None:
        self.lang_en = LanguageFactory(code="en", name="English")
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")
        self.location = LocationFactory()
        LocationTranslationFactory(location=self.location, language=self.lang_en, name="Main Hall")
        LocationTranslationFactory(location=self.location, language=self.lang_nl, name="Hoofdzaal")

    def test_translated_name_dict(self) -> None:
        data = LocationSerializer(self.location).data
        assert data["name"] == {"en": "Main Hall", "nl": "Hoofdzaal"}

    def test_queryset_serialization_many(self) -> None:
        data = LocationSerializer(Location.objects.all(), many=True).data
        assert isinstance(data, list)
        assert isinstance(data[0]["name"], dict)


class TestSpaceSerializerFields(TestCase):
    """Field exposure for SpaceSerializer."""

    def setUp(self) -> None:
        self.space = SpaceFactory()

    def test_expected_fields_present(self) -> None:
        data = SpaceSerializer(self.space).data
        assert set(data.keys()) == {"id", "location", "name", "display_name", "halls"}
        assert isinstance(data["location"], dict)
        assert isinstance(data["halls"], list)


class TestSpaceSerializerTranslations(TestCase):
    """Translation rendering for SpaceSerializer."""

    def setUp(self) -> None:
        self.lang = LanguageFactory(code="en")
        self.space = SpaceFactory()
        SpaceTranslationFactory(space=self.space, language=self.lang, name="Room A")

    def test_translated_name_dict(self) -> None:
        data = SpaceSerializer(self.space).data
        assert data["name"] == {"en": "Room A"}

    def test_nested_halls_include_translated_fields(self) -> None:
        hall = HallFactory(space=self.space)
        HallTranslationFactory(
            hall=hall,
            language=self.lang,
            name="Blue Hall",
            remark="Front stage",
        )

        data = SpaceSerializer(self.space).data

        assert len(data["halls"]) == 1
        assert data["halls"][0]["name"] == {"en": "Blue Hall"}
        assert data["halls"][0]["display_name"] == "Blue Hall"
        assert data["halls"][0]["remark"] == {"en": "Front stage"}


class TestHallSerializerFields(TestCase):
    """Field exposure for HallSerializer."""

    def setUp(self) -> None:
        self.hall = HallFactory()

    def test_expected_fields_present(self) -> None:
        data = HallSerializer(self.hall).data
        assert set(data.keys()) == {"id", "space", "seat_selection", "open_seating", "name", "display_name", "remark"}
        assert isinstance(data["space"], dict)


class TestHallSerializerTranslations(TestCase):
    """Translation rendering for HallSerializer."""

    def setUp(self) -> None:
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

    def test_translated_name_and_remark_dicts(self) -> None:
        data = HallSerializer(self.hall).data
        assert data["name"] == {"en": "Blue Hall", "fr": "Salle Bleue"}
        assert data["remark"] == {"en": "Front stage", "fr": "Avant scène"}


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
    def test_uses_base_language_when_present(self) -> None:
        en = Language.objects.create(code="en", name="English")
        nl = Language.objects.create(code="nl", name="Dutch")

        hall = _make_hall()
        HallTranslation.objects.create(hall=hall, language=nl, name="Grote Zaal", remark="Opmerking NL")
        HallTranslation.objects.create(hall=hall, language=en, name="Main Hall", remark="Remark EN")

        data = HallSerializer(hall, context=_display_ctx()).data
        assert data["display_name"] == "Main Hall"


class TestHallSerializerSpaceFallback(TestCase):
    """Fallback behaviour for HallSerializer.get_space()."""

    def test_get_space_returns_none_when_hall_has_no_space(self) -> None:
        """A hall-like object without a parent space serializes space as None."""

        class HallWithoutSpace:
            space = None

        assert HallSerializer().get_space(HallWithoutSpace()) is None
