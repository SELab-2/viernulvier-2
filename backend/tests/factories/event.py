from datetime import timedelta

import factory
from factory.declarations import LazyAttribute, LazyFunction, SubFactory
from django.utils import timezone
from faker import Faker

from apps.events.models import Event, EventPrice
from tests.factories.production import ProductionFactory
from tests.factories.pricing import PriceRankFactory
from tests.factories.location import HallFactory

faker = Faker()


class EventFactory(factory.django.DjangoModelFactory):
	"""Factory for Event model."""

	class Meta:
		model = Event

	production = SubFactory(ProductionFactory)
	hall = SubFactory(HallFactory)
	starts_at = LazyFunction(timezone.now)
	ends_at = LazyAttribute(
		lambda obj: (obj.starts_at + timedelta(hours=2)) if obj.starts_at else None
	)
	ticketing_url = LazyFunction(lambda: faker.url())


class EventPriceFactory(factory.django.DjangoModelFactory):
	"""Factory for EventPrice model."""

	class Meta:
		model = EventPrice

	event = SubFactory(EventFactory)
	price_rank = SubFactory(PriceRankFactory)
	amount = LazyFunction(lambda: faker.pydecimal(left_digits=2, right_digits=2, positive=True))
	available = LazyFunction(lambda: faker.random_int(min=1, max=500))
