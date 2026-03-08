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
from apps.locations.models import Location, Space, Hall
from apps.pricing.models import PriceRank
from apps.productions.models import Production

pytestmark = pytest.mark.django_db(transaction=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_hall() -> Hall:
    """Create a minimal Hall with required Location/Space dependencies."""
    loc = Location.objects.create(
        street="Main Street",
        number="1",
        postal_code="9000",
        city="Ghent",
        country="BE",
        phone_1=None,
        phone_2=None,
        is_own_location=False,
    )
    space = Space.objects.create(location=loc)
    return Hall.objects.create(space=space, seat_selection=False, open_seating=False)


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

def test_event_meta_ordering_by_starts_at():
    """Test case for test_event_meta_ordering_by_starts_at."""
    prod = Production.objects.create()
    hall = make_hall()

    now = timezone.now()
    e2 = Event.objects.create(production=prod, hall=hall, starts_at=now + timedelta(days=1))
    e1 = Event.objects.create(production=prod, hall=hall, starts_at=now)

    events = list(Event.objects.all())
    assert [e.id for e in events] == [e1.id, e2.id] 


def test_event_constraint_name_present():
    """Test case for test_event_constraint_name_present."""
    names = {c.name for c in Event._meta.constraints}
    assert "event_ends_after_starts" in names


def test_event_clean_raises_when_ends_before_or_equal_starts():
    """Test case for test_event_clean_raises_when_ends_before_or_equal_starts."""
    prod = Production.objects.create()
    hall = make_hall()
    now = timezone.now()

    e = Event(
        production=prod,
        hall=hall,
        starts_at=now,
        ends_at=now,
        ticketing_url="",
    )
    with pytest.raises(ValidationError):
        e.full_clean() 


def test_event_allows_null_starts_or_ends():
    """Test case for test_event_allows_null_starts_or_ends."""
    prod = Production.objects.create()
    hall = make_hall()

    e1 = Event(production=prod, hall=hall, starts_at=None, ends_at=None, ticketing_url="")
    e1.full_clean()
    e1.save()
    assert e1.id is not None

    e2 = Event(production=prod, hall=hall, starts_at=timezone.now(), ends_at=None, ticketing_url="")
    e2.full_clean()
    e2.save()
    assert e2.id is not None


# ---------------------------------------------------------------------------
# EventPrice
# ---------------------------------------------------------------------------

def test_event_price_unique_per_event_and_price_rank():
    """Test case for test_event_price_unique_per_event_and_price_rank."""
    prod = Production.objects.create()
    hall = make_hall()
    now = timezone.now()

    event = Event.objects.create(production=prod, hall=hall, starts_at=now)
    rank = PriceRank.objects.create(position=1, sold_out_buffer=0)

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
    prod = Production.objects.create()
    hall = make_hall()
    event = Event.objects.create(production=prod, hall=hall, starts_at=timezone.now())
    rank1 = PriceRank.objects.create(position=1, sold_out_buffer=0)
    rank2 = PriceRank.objects.create(position=2, sold_out_buffer=0)

    p1 = EventPrice.objects.create(event=event, price_rank=rank1, amount="10.00", available=10)
    p2 = EventPrice.objects.create(event=event, price_rank=rank2, amount="12.00", available=5)

    assert event.prices.count() == 2
    assert set(event.prices.values_list("id", flat=True)) == {p1.id, p2.id}


def test_event_price_cascade_delete_event_deletes_prices():
    """Test case for test_event_price_cascade_delete_event_deletes_prices."""
    prod = Production.objects.create()
    hall = make_hall()
    event = Event.objects.create(production=prod, hall=hall, starts_at=timezone.now())
    rank = PriceRank.objects.create(position=1, sold_out_buffer=0)

    EventPrice.objects.create(event=event, price_rank=rank, amount="10.00", available=10)
    EventPrice.objects.create(event=event, price_rank=None, amount="8.00", available=3)

    event.delete()
    assert EventPrice.objects.count() == 0 


def test_event_price_set_null_when_price_rank_deleted():
    """Test case for test_event_price_set_null_when_price_rank_deleted."""
    prod = Production.objects.create()
    hall = make_hall()
    event = Event.objects.create(production=prod, hall=hall, starts_at=timezone.now())
    rank = PriceRank.objects.create(position=1, sold_out_buffer=0)

    ep = EventPrice.objects.create(event=event, price_rank=rank, amount="10.00", available=10)
    rank.delete()

    ep.refresh_from_db()
    assert ep.price_rank_id is None


def test_event_price_str_representation():
    """Test case for test_event_price_str_representation."""
    prod = Production.objects.create()
    hall = make_hall()
    event = Event.objects.create(production=prod, hall=hall, starts_at=timezone.now())
    rank = PriceRank.objects.create(position=1, sold_out_buffer=0)
    event_price = EventPrice.objects.create(event=event, price_rank=rank, amount="10.00", available=10)

    assert str(event_price) == f"EventPrice {event_price.id} - Event {event.id} / Rank {rank.id}"