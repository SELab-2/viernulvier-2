"""Factory Boy factories for location, space, and hall test data."""

import factory
from faker import Faker

from apps.locations.models import (
    Hall,
    HallTranslation,
    Location,
    LocationTranslation,
    Space,
    SpaceTranslation,
)
from tests.factories.language import LanguageFactory

faker = Faker()

# ==============================
# LOCATION
# ==============================


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    street = factory.LazyFunction(faker.street_name)
    number = factory.LazyFunction(lambda: str(faker.building_number()))
    postal_code = factory.LazyFunction(faker.postcode)
    city = factory.LazyFunction(faker.city)
    country = factory.LazyFunction(faker.country)
    phone_1 = factory.LazyFunction(faker.phone_number)
    phone_2 = factory.LazyFunction(faker.phone_number)
    is_own_location = factory.LazyFunction(lambda: faker.boolean(chance_of_getting_true=50))


class LocationTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LocationTranslation

    location = factory.SubFactory(LocationFactory)
    language = factory.SubFactory(LanguageFactory)
    name = factory.LazyAttribute(lambda o: f"{o.location.city} {o.location.street} ({o.language.code})")


# ==============================
# SPACE
# ==============================


class SpaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Space

    location = factory.SubFactory(LocationFactory)


class SpaceTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SpaceTranslation

    space = factory.SubFactory(SpaceFactory)
    language = factory.SubFactory(LanguageFactory)
    name = factory.LazyAttribute(lambda o: f"Space {o.space.id} ({o.language.code})")


# ==============================
# HALL
# ==============================


class HallFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hall

    space = factory.SubFactory(SpaceFactory)
    seat_selection = factory.LazyFunction(lambda: faker.boolean(chance_of_getting_true=50))
    open_seating = factory.LazyFunction(lambda: faker.boolean(chance_of_getting_true=50))


class HallTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HallTranslation

    hall = factory.SubFactory(HallFactory)
    language = factory.SubFactory(LanguageFactory)
    name = factory.LazyAttribute(lambda o: f"Hall {o.hall.id} ({o.language.code})")
    remark = factory.LazyFunction(faker.sentence)
