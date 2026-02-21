from datetime import timedelta

import factory
from django.utils import timezone
from faker import Faker

from apps.events.models import Event, EventPrice

faker = Faker()


class EventFactory(factory.django.DjangoModelFactory):
	"""Factory for Event model."""

	class Meta:
		model = Event

    # TODO: voorlopig None, maar hier moeten nog Factories voor gemaakt worden
	production = None
	hall = None
	starts_at = factory.LazyFunction(timezone.now)
	ends_at = factory.LazyAttribute(lambda obj: obj.starts_at + timedelta(hours=2))
	ticketing_url = factory.LazyFunction(lambda: faker.url())


class EventPriceFactory(factory.django.DjangoModelFactory):
	"""Factory for EventPrice model."""

	class Meta:
		model = EventPrice

	event = factory.SubFactory(EventFactory)
    # TODO: voorlopig None, maar hier moeten nog Factories voor gemaakt worden
	price_rank = None
	amount = factory.LazyFunction(lambda: faker.pydecimal(left_digits=2, right_digits=2, positive=True))
	available = factory.LazyFunction(lambda: faker.random_int(min=1, max=500))
