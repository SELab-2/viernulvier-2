import pytest
from django.core.exceptions import ValidationError
from apps.languages.models import Language
from apps.locations.models import Location, LocationTranslation, Space, SpaceTranslation, Hall, HallTranslation

from tests.factories.language import LanguageFactory
from tests.factories.location import LocationFactory, LocationTranslationFactory, SpaceFactory, SpaceTranslationFactory, HallFactory, HallTranslationFactory

pytestmark = pytest.mark.django_db

# =====================================================
# LOCATION
# =====================================================

class TestLocation:

    def test_requires_mandatory_fields(self):
        loc = LocationFactory.build(street="", number="", postal_code="", city="", country="")
        with pytest.raises(ValidationError):
            loc.full_clean()

    def test_str_representation(self):
        loc = LocationFactory(street="Main St", number="123", city="Gotham")
        assert str(loc) == "Gotham - Main St 123"

    def test_reverse_relation_spaces(self):
        loc = LocationFactory()
        SpaceFactory.create_batch(3, location=loc)
        assert loc.spaces.count() == 3


class TestLocationTranslation:

    def test_requires_unique_location_language(self):
        loc = LocationFactory()
        lang = LanguageFactory()
        LocationTranslationFactory(location=loc, language=lang)
        # Trying to create duplicate should raise IntegrityError at save()
        with pytest.raises(Exception):
            LocationTranslationFactory(location=loc, language=lang)

    def test_str(self):
        trans = LocationTranslationFactory(name="HQ", language__code="en")
        assert str(trans) == "en - HQ"

    def test_language_reverse_relation(self):
        lang = LanguageFactory()
        LocationTranslationFactory.create_batch(2, language=lang)
        assert lang.location_translations.count() == 2

    def test_cascade_delete_location(self):
        loc = LocationFactory()
        LocationTranslationFactory(location=loc)
        loc.delete()
        assert LocationTranslation.objects.count() == 0


# =====================================================
# SPACE
# =====================================================

class TestSpace:

    def test_requires_location(self):
        space = SpaceFactory.build(location=None)
        with pytest.raises(ValidationError):
            space.full_clean()

    def test_str_representation(self):
        loc = LocationFactory(city="Gotham", street="Main St", number="1")
        space = SpaceFactory(location=loc)
        assert str(space) == f"Space {space.id} - {loc}"

    def test_reverse_relation_translations(self):
        space = SpaceFactory()
        SpaceTranslationFactory.create_batch(3, space=space)
        assert space.translations.count() == 3

    def test_cascade_delete_location_cascades_to_space(self):
        loc = LocationFactory()
        SpaceFactory(location=loc)
        loc.delete()
        assert Space.objects.count() == 0


class TestSpaceTranslation:

    def test_str(self):
        trans = SpaceTranslationFactory(name="Main Hall", language__code="en")
        assert str(trans) == f"Space - en - Main Hall"

    def test_language_reverse_relation(self):
        lang = LanguageFactory()
        SpaceTranslationFactory.create_batch(2, language=lang)
        assert lang.space_translations.count() == 2

    def test_cascade_delete_space(self):
        space = SpaceFactory()
        SpaceTranslationFactory(space=space)
        space.delete()
        assert SpaceTranslation.objects.count() == 0


# =====================================================
# HALL
# =====================================================

class TestHall:

    def test_requires_space(self):
        hall = HallFactory.build(space=None)
        with pytest.raises(ValidationError):
            hall.full_clean()

    def test_str_representation(self):
        space = SpaceFactory()
        hall = HallFactory(space=space)
        assert str(hall) == f"Hall {hall.id} @ {space}"

    def test_reverse_relation_translations(self):
        hall = HallFactory()
        HallTranslationFactory.create_batch(3, hall=hall)
        assert hall.translations.count() == 3

    def test_cascade_delete_space_cascades_to_hall(self):
        space = SpaceFactory()
        HallFactory(space=space)
        space.delete()
        assert Hall.objects.count() == 0


class TestHallTranslation:

    def test_str(self):
        trans = HallTranslationFactory(name="Grand Hall", language__code="en")
        assert str(trans) == "en - Grand Hall"

    def test_language_reverse_relation(self):
        lang = LanguageFactory()
        HallTranslationFactory.create_batch(2, language=lang)
        assert lang.hall_translations.count() == 2

    def test_cascade_delete_hall(self):
        hall = HallFactory()
        HallTranslationFactory(hall=hall)
        hall.delete()
        assert HallTranslation.objects.count() == 0
