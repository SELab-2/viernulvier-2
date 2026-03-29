from django.forms import ValidationError
import pytest

from apps.locations.models import (
    Hall,
    HallTranslation,
    LocationTranslation,
    Space,
    SpaceTranslation,
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

pytestmark = pytest.mark.django_db

# =====================================================
# LOCATION
# =====================================================


class TestLocation:
    def test_all_address_fields_are_optional(self) -> None:
        """All address fields are nullable/blank - a bare Location must pass full_clean."""
        loc = LocationFactory.build(street="", number="", postal_code="", city="")
        loc.full_clean()  # must not raise

    def test_str_without_translation_shows_address(self) -> None:
        """Without a translation the __str__ returns the address parts only."""
        loc = LocationFactory(street="Main St", number="123", city="Gotham", postal_code=None)
        assert str(loc) == "Main St 123, Gotham"

    def test_str_with_translation_shows_name_and_address(self) -> None:
        """With a translation the __str__ returns '<name> - <address>'."""
        loc = LocationFactory(street="Main St", number="123", city="Gotham", postal_code="1000")
        LocationTranslationFactory(location=loc, name="HQ")
        assert str(loc) == "HQ - Main St 123, 1000 Gotham"

    def test_str_omits_empty_parts(self) -> None:
        """Parts that are empty/None are omitted gracefully."""
        loc = LocationFactory(street=None, number=None, postal_code=None, city="Gotham")
        assert str(loc) == "Gotham"

    def test_str_fallback_when_no_address(self) -> None:
        """A location with no address fields at all returns '/'."""
        loc = LocationFactory(street=None, number=None, postal_code=None, city=None)
        assert str(loc) == "/"

    def test_reverse_relation_spaces(self) -> None:
        loc = LocationFactory()
        SpaceFactory.create_batch(3, location=loc)
        assert loc.spaces.count() == 3


class TestLocationTranslation:
    def test_requires_unique_location_language(self) -> None:
        loc = LocationFactory()
        lang = LanguageFactory()
        LocationTranslationFactory(location=loc, language=lang)
        with pytest.raises(ValidationError):
            LocationTranslationFactory(location=loc, language=lang)

    def test_str(self) -> None:
        trans = LocationTranslationFactory(name="HQ", language__code="en")
        assert str(trans) == "en - HQ"

    def test_language_reverse_relation(self) -> None:
        lang = LanguageFactory()
        LocationTranslationFactory.create_batch(2, language=lang)
        assert lang.location_translations.count() == 2

    def test_cascade_delete_location(self) -> None:
        loc = LocationFactory()
        LocationTranslationFactory(location=loc)
        loc.delete()
        assert LocationTranslation.objects.count() == 0


# =====================================================
# SPACE
# =====================================================


class TestSpace:
    def test_str_without_translation_shows_fallback_with_city(self) -> None:
        """Without a translation the __str__ uses the fallback id and appends the city."""
        loc = LocationFactory(city="Gotham")
        space = SpaceFactory(location=loc)
        assert str(space) == f"Space {space.id} (Gotham)"

    def test_str_with_translation_shows_name_with_city(self) -> None:
        """With a translation the __str__ uses the translation name and appends the city."""
        loc = LocationFactory(city="Gotham")
        space = SpaceFactory(location=loc)
        SpaceTranslationFactory(space=space, name="Main Hall")
        assert str(space) == "Main Hall (Gotham)"

    def test_str_without_city_omits_parentheses(self) -> None:
        """When the location has no city, __str__ returns only the name/fallback."""
        loc = LocationFactory(city=None)
        space = SpaceFactory(location=loc)
        assert str(space) == f"Space {space.id}"

    def test_reverse_relation_translations(self) -> None:
        space = SpaceFactory()
        SpaceTranslationFactory.create_batch(3, space=space)
        assert space.translations.count() == 3

    def test_cascade_delete_location_cascades_to_space(self) -> None:
        loc = LocationFactory()
        SpaceFactory(location=loc)
        loc.delete()
        assert Space.objects.count() == 0

    def test_str_falls_back_to_name_when_location_raises(self) -> None:
        """When location is None in memory, __str__ returns only the fallback name."""
        space = SpaceFactory()
        space.location = None
        assert str(space) == f"Space {space.id}"


class TestSpaceTranslation:
    def test_str(self) -> None:
        trans = SpaceTranslationFactory(name="Main Hall", language__code="en")
        assert str(trans) == "en - Main Hall"

    def test_language_reverse_relation(self) -> None:
        lang = LanguageFactory()
        SpaceTranslationFactory.create_batch(2, language=lang)
        assert lang.space_translations.count() == 2

    def test_cascade_delete_space(self) -> None:
        space = SpaceFactory()
        SpaceTranslationFactory(space=space)
        space.delete()
        assert SpaceTranslation.objects.count() == 0


# =====================================================
# HALL
# =====================================================


class TestHall:
    def test_space_is_optional(self) -> None:
        """space FK is nullable - a Hall without a space must pass full_clean."""
        hall = HallFactory.build(space=None)
        hall.full_clean()  # must not raise

    def test_str_without_translation_shows_fallback_with_city(self) -> None:
        """Without a translation the __str__ uses the fallback id and appends the city."""
        loc = LocationFactory(city="Gotham")
        space = SpaceFactory(location=loc)
        hall = HallFactory(space=space)
        assert str(hall) == f"Hall {hall.id} (Gotham)"

    def test_str_with_translation_shows_name_with_city(self) -> None:
        """With a translation the __str__ uses the translation name and appends the city."""
        loc = LocationFactory(city="Gotham")
        space = SpaceFactory(location=loc)
        hall = HallFactory(space=space)
        HallTranslationFactory(hall=hall, name="Grand Hall")
        assert str(hall) == "Grand Hall (Gotham)"

    def test_str_without_city_omits_parentheses(self) -> None:
        """When the parent space has no city, __str__ returns only the name/fallback."""
        loc = LocationFactory(city=None)
        space = SpaceFactory(location=loc)
        hall = HallFactory(space=space)
        assert str(hall) == f"Hall {hall.id}"

    def test_reverse_relation_translations(self) -> None:
        hall = HallFactory()
        HallTranslationFactory.create_batch(3, hall=hall)
        assert hall.translations.count() == 3

    def test_cascade_delete_space_cascades_to_hall(self) -> None:
        space = SpaceFactory()
        HallFactory(space=space)
        space.delete()
        assert Hall.objects.count() == 0

    def test_str_falls_back_to_name_when_space_raises(self) -> None:
        """When space is None, __str__ returns only the fallback name."""
        hall = HallFactory(space=None)
        assert str(hall) == f"Hall {hall.id}"


class TestHallTranslation:
    def test_str(self) -> None:
        trans = HallTranslationFactory(name="Grand Hall", language__code="en")
        assert str(trans) == "en - Grand Hall"

    def test_language_reverse_relation(self) -> None:
        lang = LanguageFactory()
        HallTranslationFactory.create_batch(2, language=lang)
        assert lang.hall_translations.count() == 2

    def test_cascade_delete_hall(self) -> None:
        hall = HallFactory()
        HallTranslationFactory(hall=hall)
        hall.delete()
        assert HallTranslation.objects.count() == 0
