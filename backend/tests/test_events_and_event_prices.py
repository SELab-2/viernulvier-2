from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.events.models import Event, EventPrice

# from apps.productions.models import Production
# from apps.halls.models import Hall
# from apps.priceranks.models import PriceRank


class EventModelTests(TestCase):
    def setUp(self):
        # Maak minimale geldige related objects
        self.production = Production.objects.create(
            # TODO: fill in necessary fields for production object
            # example: title="Hamlet"
        )
        self.hall = Hall.objects.create(
            # TODO: fill in necessary fields for hall object
        )

    def test_event_check_constraint_ends_after_starts(self):
        starts = timezone.now()
        ends = starts - timedelta(hours=1)

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Event.objects.create(
                    production=self.production,
                    hall=self.hall,
                    starts_at=starts,
                    ends_at=ends,
                    ticketing_url="https://example.com/tickets",
                )

    def test_event_allows_null_datetimes(self):
        e = Event.objects.create(
            production=self.production,
            hall=self.hall,
            starts_at=None,
            ends_at=None,
            ticketing_url="https://example.com/tickets",
        )
        self.assertIsNotNone(e.pk)

    def test_event_default_ordering_by_starts_at(self):
        t0 = timezone.now()
        e2 = Event.objects.create(production=self.production, starts_at=t0 + timedelta(days=1), ends_at=t0 + timedelta(days=1, hours=2))
        e1 = Event.objects.create(production=self.production, starts_at=t0, ends_at=t0 + timedelta(hours=2))

        events = list(Event.objects.all())
        self.assertEqual(events, [e1, e2])

    def test_event_hall_set_null_on_delete(self):
        e = Event.objects.create(
            production=self.production,
            hall=self.hall,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=2),
        )
        self.hall.delete()
        e.refresh_from_db()
        self.assertIsNone(e.hall)

    def test_event_deleted_when_production_deleted(self):
        e = Event.objects.create(
            production=self.production,
            hall=self.hall,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=2),
        )
        self.production.delete()
        self.assertFalse(Event.objects.filter(pk=e.pk).exists())


class EventPriceModelTests(TestCase):
    def setUp(self):
        self.production = Production.objects.create(
            # TODO: fill in production fields
        )
        self.event = Event.objects.create(
            production=self.production,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=2),
        )
        self.rank = PriceRank.objects.create(
            # TODO: fill in price rank fields
        )

    def test_eventprice_unique_constraint_event_and_price_rank(self):
        EventPrice.objects.create(
            event=self.event,
            price_rank=self.rank,
            amount=Decimal("12.50"),
            available=100,
        )

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                EventPrice.objects.create(
                    event=self.event,
                    price_rank=self.rank,  # zelfde combo => moet falen
                    amount=Decimal("15.00"),
                    available=50,
                )

    def test_eventprice_allows_null_price_rank_but_unique_constraint_behaviour(self):
        EventPrice.objects.create(
            event=self.event,
            price_rank=None,
            amount=Decimal("10.00"),
            available=10,
        )
        EventPrice.objects.create(
            event=self.event,
            price_rank=None,
            amount=Decimal("11.00"),
            available=11,
        )
        self.assertEqual(EventPrice.objects.filter(event=self.event, price_rank__isnull=True).count(), 2)

    def test_eventprice_price_rank_set_null_on_delete(self):
        ep = EventPrice.objects.create(
            event=self.event,
            price_rank=self.rank,
            amount=Decimal("12.50"),
            available=100,
        )
        self.rank.delete()
        ep.refresh_from_db()
        self.assertIsNone(ep.price_rank)

    def test_eventprice_deleted_when_event_deleted(self):
        ep = EventPrice.objects.create(
            event=self.event,
            price_rank=self.rank,
            amount=Decimal("12.50"),
            available=100,
        )
        self.event.delete()
        self.assertFalse(EventPrice.objects.filter(pk=ep.pk).exists())