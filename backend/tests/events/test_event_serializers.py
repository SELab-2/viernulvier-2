"""
Covers:
- EventSerializer field exposure (no extra fields)
- EventSerializer serialization (model -> dict)
- Nested prices (EventPriceSerializer) output inside EventSerializer
- EventSerializer deserialization / validation (dict -> model)
- Read-only field behavior for `id` and `prices`
- Basic invalid data handling
- Partial updates
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.events.models import Event, EventPrice
from apps.events.serializers import EventPriceSerializer, EventSerializer
from tests.factories.event import EventFactory, EventPriceFactory
from tests.factories.language import LanguageFactory
from tests.factories.location import HallFactory
from tests.factories.pricing import (
    PriceFactory,
    PriceRankFactory,
    PriceTranslationFactory,
)
from tests.factories.production import ProductionFactory


def _drf_request(factory: APIRequestFactory, path: str) -> Request:
    django_req = factory.get(path)
    return Request(django_req)


class TestEventSerializerFields(TestCase):
    """Verify that the correct fields are exposed."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.production = ProductionFactory()
        cls.hall = HallFactory()

        now = timezone.now()
        cls.event = EventFactory(
            production=cls.production,
            hall=cls.hall,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            ticketing_url="https://example.com/tickets",
        )

    def test_expected_fields_are_present(self):
        """EventSerializer exposes the expected fields."""
        serializer = EventSerializer(self.event, context={"request": _drf_request(self.factory, "/dummy")})
        data = serializer.data

        expected = {
            "id",
            "production",
            "production_display",
            "hall",
            "hall_display",
            "starts_at",
            "ends_at",
            "ticketing_url",
            "prices",
        }
        for f in expected:
            self.assertIn(f, data)

    def test_no_extra_fields_are_exposed(self):
        """EventSerializer should not expose extra fields."""
        serializer = EventSerializer(self.event, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "production",
                "production_display",
                "hall",
                "hall_display",
                "starts_at",
                "ends_at",
                "ticketing_url",
                "prices",
            },
        )


class TestEventSerializerSerialization(TestCase):
    """Model → dict serialization, including nested prices."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.production = ProductionFactory()
        cls.hall = HallFactory()

        now = timezone.now()
        cls.event = EventFactory(
            production=cls.production,
            hall=cls.hall,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            ticketing_url="https://example.com/tickets",
        )

        cls.rank_1 = PriceRankFactory(position=1, sold_out_buffer=0)
        cls.rank_2 = PriceRankFactory(position=2, sold_out_buffer=0)

        cls.ep_1 = EventPriceFactory(
            event=cls.event,
            price_rank=cls.rank_1,
            amount=Decimal("12.50"),
            available=100,
        )
        cls.ep_2 = EventPriceFactory(
            event=cls.event,
            price_rank=cls.rank_2,
            amount=Decimal("9.00"),
            available=50,
        )

    def test_serializes_event_core_fields(self):
        """Event core fields serialize correctly."""
        serializer = EventSerializer(self.event, context={"request": _drf_request(self.factory, "/dummy")})
        data = serializer.data

        self.assertEqual(data["production"], self.production.id)
        self.assertEqual(data["hall"], self.hall.id)
        self.assertIsInstance(data["ticketing_url"], str)

        self.assertIsInstance(data["starts_at"], str)
        self.assertIsInstance(data["ends_at"], str)

    def test_prices_is_list(self):
        """Nested prices field is a list."""
        serializer = EventSerializer(self.event, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertIsInstance(serializer.data["prices"], list)

    def test_prices_contains_expected_items(self):
        """Nested EventPrice items include expected keys/values."""
        serializer = EventSerializer(self.event, context={"request": _drf_request(self.factory, "/dummy")})
        prices = serializer.data["prices"]

        by_rank = {p["price_rank"]: p for p in prices}
        self.assertIn(self.rank_1.id, by_rank)
        self.assertIn(self.rank_2.id, by_rank)

        item = by_rank[self.rank_1.id]
        self.assertEqual(item["event"], self.event.id)
        self.assertEqual(item["price_rank"], self.rank_1.id)
        self.assertEqual(item["available"], 100)

        self.assertIn(str(item["amount"]), {"12.50", "12.5"})

    def test_hall_display_is_none_when_event_has_no_hall(self):
        event = EventFactory(
            production=self.production,
            hall=None,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=1),
            ticketing_url="https://example.com/tickets",
        )

        data = EventSerializer(event, context={"request": _drf_request(self.factory, "/dummy")}).data
        self.assertIsNone(data["hall_display"])

    def test_price_rank_display_is_none_when_price_rank_is_null(self):
        event = EventFactory(
            production=self.production,
            hall=self.hall,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=1),
            ticketing_url="https://example.com/tickets",
        )
        EventPriceFactory(
            event=event,
            price_rank=None,
            amount=Decimal("12.50"),
            available=10,
        )

        data = EventSerializer(event, context={"request": _drf_request(self.factory, "/dummy")}).data
        self.assertEqual(len(data["prices"]), 1)
        self.assertIsNone(data["prices"][0]["price_rank_display"])


class TestEventSerializerDeserialization(TestCase):
    """dict → model (create / update)."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.production = ProductionFactory()
        self.hall = HallFactory()
        self.now = timezone.now()

    def test_valid_data_is_valid(self):
        """Valid payload validates."""
        data = {
            "production": self.production.id,
            "hall": self.hall.id,
            "starts_at": self.now.isoformat(),
            "ends_at": (self.now + timedelta(hours=2)).isoformat(),
            "ticketing_url": "https://example.com/tickets",
        }
        serializer = EventSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_data_saves_to_db(self):
        """Valid payload saves an Event."""
        data = {
            "production": self.production.id,
            "hall": self.hall.id,
            "starts_at": self.now.isoformat(),
            "ends_at": (self.now + timedelta(hours=2)).isoformat(),
            "ticketing_url": "https://example.com/tickets",
        }
        serializer = EventSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        event = serializer.save()
        self.assertTrue(Event.objects.filter(id=event.id).exists())
        self.assertEqual(event.production_id, self.production.id)
        self.assertEqual(event.hall_id, self.hall.id)

    def test_prices_is_read_only(self):
        """
        `prices` is read-only on EventSerializer; providing it in input should not create prices.
        """
        rank = PriceRankFactory(position=1, sold_out_buffer=0)

        data = {
            "production": self.production.id,
            "hall": self.hall.id,
            "starts_at": self.now.isoformat(),
            "ends_at": (self.now + timedelta(hours=2)).isoformat(),
            "ticketing_url": "https://example.com/tickets",
            "prices": [
                {
                    "event": 999,
                    "price_rank": rank.id,
                    "amount": "10.00",
                    "available": 1,
                },
            ],
        }
        serializer = EventSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        event = serializer.save()
        self.assertEqual(EventPrice.objects.filter(event=event).count(), 0)

        out = EventSerializer(event, context={"request": _drf_request(self.factory, "/dummy")}).data
        self.assertEqual(out["prices"], [])

    def test_missing_production_is_invalid(self):
        """Missing required production should be invalid."""
        data = {
            "hall": self.hall.id,
            "starts_at": self.now.isoformat(),
            "ends_at": (self.now + timedelta(hours=2)).isoformat(),
            "ticketing_url": "https://example.com/tickets",
        }
        serializer = EventSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertFalse(serializer.is_valid())
        self.assertIn("production", serializer.errors)

    def test_missing_hall_is_valid(self):
        """Missing hall is valid when the model/serializer allows hall to be null."""
        data = {
            "production": self.production.id,
            "starts_at": self.now.isoformat(),
            "ends_at": (self.now + timedelta(hours=2)).isoformat(),
            "ticketing_url": "https://example.com/tickets",
        }
        serializer = EventSerializer(data=data, context={"request": _drf_request(self.factory, "/dummy")})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_partial_update_ticketing_url_only(self):
        """Partial update updates only provided fields."""
        event = Event.objects.create(
            production=self.production,
            hall=self.hall,
            starts_at=self.now,
            ends_at=self.now + timedelta(hours=2),
            ticketing_url="https://example.com/old",
        )
        serializer = EventSerializer(
            event,
            data={"ticketing_url": "https://example.com/new"},
            partial=True,
            context={"request": _drf_request(self.factory, "/dummy")},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.ticketing_url, "https://example.com/new")
        self.assertEqual(updated.production_id, self.production.id)
        self.assertEqual(updated.hall_id, self.hall.id)


class TestEventPriceSerializerDisplayFields(TestCase):
    """Test EventPriceSerializer display fields: price_rank_display & price_display."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.production = ProductionFactory()
        cls.hall = HallFactory()
        cls.event = EventFactory(
            production=cls.production,
            hall=cls.hall,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=1),
        )
        cls.rank = PriceRankFactory(position=1)
        cls.price = None  # simulate deleted price
        cls.ep = EventPriceFactory(
            event=cls.event,
            price_rank=cls.rank,
            price=cls.price,
            amount="15.00",
            available=10,
        )

    def test_price_rank_display_and_price_display(self):
        serializer = EventPriceSerializer(self.ep, context={"request": _drf_request(APIRequestFactory(), "/dummy")})
        data = serializer.data

        # price_rank_display should fallback to ID if translations are missing
        self.assertEqual(data["price_rank_display"], str(self.rank.id))
        # price_display should fallback to None since price is None
        self.assertIsNone(data["price_display"])

    def test_price_display_falls_back_to_id_when_no_translation(self):
        """When price exists but has no translations, price_display falls back to the price PK."""
        price = PriceFactory()
        ep = EventPriceFactory(
            event=self.event,
            price_rank=self.rank,
            price=price,
            amount="15.00",
            available=10,
        )
        serializer = EventPriceSerializer(ep, context={"request": _drf_request(APIRequestFactory(), "/dummy")})
        self.assertEqual(serializer.data["price_display"], str(price.id))

    def test_price_display_returns_translated_description(self):
        """When price has a translation, price_display returns the translated description."""
        price = PriceFactory()
        lang = LanguageFactory()
        PriceTranslationFactory(price=price, language=lang, description="Student")

        ep = EventPriceFactory(
            event=self.event,
            price_rank=self.rank,
            price=price,
            amount="15.00",
            available=10,
        )
        serializer = EventPriceSerializer(ep, context={"request": _drf_request(APIRequestFactory(), "/dummy")})
        self.assertEqual(serializer.data["price_display"], "Student")


class TestEventSerializerNestedPricesReadOnly(TestCase):
    """Test that EventSerializer nested prices remain read-only even on update."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.production = ProductionFactory()
        cls.hall = HallFactory()
        cls.rank = PriceRankFactory(position=1)
        cls.event = EventFactory(
            production=cls.production,
            hall=cls.hall,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=1),
        )
        cls.ep = EventPriceFactory(event=cls.event, price_rank=cls.rank, amount="10.00", available=5)

    def test_nested_prices_read_only_on_partial_update(self):
        # Attempt to update prices via EventSerializer (read-only)
        payload = {
            "ticketing_url": "https://example.com/updated",
            "prices": [{"price_rank": self.rank.id, "amount": "20.00", "available": 1}],
        }
        serializer = EventSerializer(
            self.event,
            data=payload,
            partial=True,
            context={"request": _drf_request(self.factory, "/dummy")},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_event = serializer.save()

        # ticketing_url is updated
        self.assertEqual(updated_event.ticketing_url, payload["ticketing_url"])
        # prices are unchanged
        self.assertEqual(updated_event.prices.count(), 1)
        price_obj = updated_event.prices.first()
        self.assertEqual(price_obj.amount, Decimal("10.00"))
        self.assertEqual(price_obj.available, 5)
