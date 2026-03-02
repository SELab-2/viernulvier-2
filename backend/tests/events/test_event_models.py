"""
Covers:
- Meta ordering
- constraint names present
- Event.clean validation (ends_at > starts_at)
- EventPrice uniqueness constraint (event + price_rank)
- indexes presence (by fields)
- reverse relations (event.prices)
- cascade delete behavior (Event -> EventPrice)
- set_null behavior (PriceRank -> EventPrice.price_rank)
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.events.models import Event, EventPrice
from tests.factories.event import EventFactory, EventPriceFactory
from tests.factories.location import HallFactory
from tests.factories.pricing import PriceRankFactory
from tests.factories.production import ProductionFactory

pytestmark = pytest.mark.django_db(transaction=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

def test_event_meta_ordering_by_starts_at():
    """Test case for test_event_meta_ordering_by_starts_at."""
    prod = ProductionFactory()
    hall = HallFactory()

    now = timezone.now()
    e2 = EventFactory(production=prod, hall=hall, starts_at=now + timedelta(days=1))
    e1 = EventFactory(production=prod, hall=hall, starts_at=now)

    events = list(Event.objects.all())
    assert [e.id for e in events] == [e1.id, e2.id] 


def test_event_constraint_name_present():
    """Test case for test_event_constraint_name_present."""
    names = {c.name for c in Event._meta.constraints}
    assert "event_ends_after_starts" in names


def test_event_clean_raises_when_ends_before_starts():
    """Test case for test_event_clean_raises_when_ends_before_starts."""
    prod = ProductionFactory()
    hall = HallFactory()
    now = timezone.now()

    e = Event(
        production=prod,
        hall=hall,
        starts_at=now,
        ends_at=now - timedelta(minutes=1),
        ticketing_url="",
    )
    with pytest.raises(ValidationError):
        e.full_clean()


def test_event_allows_equal_start_and_end():
    """Equal start/end timestamps are allowed."""
    prod = ProductionFactory()
    hall = HallFactory()
    now = timezone.now()

    e = Event(
        production=prod,
        hall=hall,
        starts_at=now,
        ends_at=now,
        ticketing_url="",
    )
    e.full_clean()
    e.save()
    assert e.id is not None


def test_event_allows_null_starts_or_ends():
    """Test case for test_event_allows_null_starts_or_ends."""
    prod = ProductionFactory()
    hall = HallFactory()

    e1 = Event(production=prod, hall=hall, starts_at=None, ends_at=None, ticketing_url="")
    e1.full_clean()
    e1.save()
    assert e1.id is not None

    e2 = Event(production=prod, hall=hall, starts_at=timezone.now(), ends_at=None, ticketing_url="")
    e2.full_clean()
    e2.save()
    assert e2.id is not None


def test_event_allows_end_without_start():
    """Test case for allowing an end time without a start time."""
    prod = ProductionFactory()
    hall = HallFactory()

    e3 = Event(production=prod, hall=hall, starts_at=None, ends_at=timezone.now(), ticketing_url="")
    e3.full_clean()
    e3.save()
    assert e3.id is not None


# ---------------------------------------------------------------------------
# EventPrice
# ---------------------------------------------------------------------------

def test_event_price_unique_per_event_and_price_rank():
    """Test case for test_event_price_unique_per_event_and_price_rank."""
    prod = ProductionFactory()
    hall = HallFactory()
    now = timezone.now()

    event = EventFactory(production=prod, hall=hall, starts_at=now)
    rank = PriceRankFactory(position=1, sold_out_buffer=0)

    ep1 = EventPrice(event=event, price_rank=rank, amount=Decimal("10.00"), available=10)
    ep1.full_clean()
    ep1.save()

    ep2 = EventPrice(event=event, price_rank=rank, amount=Decimal("12.00"), available=5)
    with pytest.raises(ValidationError):
        ep2.full_clean()


def test_event_price_constraint_name_present():
    """Test case for test_event_price_constraint_name_present."""
    names = {c.name for c in EventPrice._meta.constraints}
    assert "uniq_event_price_rank" in names


def test_event_price_indexes_present_by_fields():
    """Test case for test_event_price_indexes_present_by_fields."""
    idx_fields = [tuple(idx.fields) for idx in EventPrice._meta.indexes]
    assert ("event",) in idx_fields
    assert ("event", "price_rank") in idx_fields


def test_event_price_reverse_relation_from_event():
    """Test case for test_event_price_reverse_relation_from_event."""
    prod = ProductionFactory()
    hall = HallFactory()
    event = EventFactory(production=prod, hall=hall, starts_at=timezone.now())
    rank1 = PriceRankFactory(position=1, sold_out_buffer=0)
    rank2 = PriceRankFactory(position=2, sold_out_buffer=0)

    p1 = EventPriceFactory(event=event, price_rank=rank1, amount="10.00", available=10)
    p2 = EventPriceFactory(event=event, price_rank=rank2, amount="12.00", available=5)

    assert event.prices.count() == 2
    assert set(event.prices.values_list("id", flat=True)) == {p1.id, p2.id}


def test_event_price_cascade_delete_event_deletes_prices():
    """Test case for test_event_price_cascade_delete_event_deletes_prices."""
    prod = ProductionFactory()
    hall = HallFactory()
    event = EventFactory(production=prod, hall=hall, starts_at=timezone.now())
    rank = PriceRankFactory(position=1, sold_out_buffer=0)

    EventPriceFactory(event=event, price_rank=rank, amount="10.00", available=10)
    EventPriceFactory(event=event, price_rank=None, amount="8.00", available=3)

    event.delete()
    assert EventPrice.objects.count() == 0 


def test_event_price_set_null_when_price_rank_deleted():
    """Test case for test_event_price_set_null_when_price_rank_deleted."""
    prod = ProductionFactory()
    hall = HallFactory()
    event = EventFactory(production=prod, hall=hall, starts_at=timezone.now())
    rank = PriceRankFactory(position=1, sold_out_buffer=0)

    ep = EventPriceFactory(event=event, price_rank=rank, amount="10.00", available=10)
    rank.delete()

    ep.refresh_from_db()
    assert ep.price_rank_id is None


def test_event_price_str_representation():
    """__str__ must include the id, event id, and price rank id."""
    price = EventPriceFactory(amount="10.00", available=10)

    expected = f"EventPrice {price.id} - Event {price.event_id} / Rank {price.price_rank_id}"

    assert str(price) == expected