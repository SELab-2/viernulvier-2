"""
Covers:
- Meta ordering
- constraint names present
- Event.clean validation (ends_at > starts_at)
- EventPrice uniqueness constraint (event + price_rank + price)
- indexes presence (by fields)
- reverse relations (event.prices)
- cascade delete behavior (Event -> EventPrice)
- set_null behavior (PriceRank -> EventPrice.price_rank)
- set_null behavior (Price -> EventPrice.price)
- price FK inclusion in uniqueness and indexes
"""

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone
import pytest

from apps.events.models import Event, EventPrice
from tests.factories.event import EventFactory, EventPriceFactory
from tests.factories.location import HallFactory
from tests.factories.pricing import PriceFactory, PriceRankFactory
from tests.factories.production import ProductionFactory

pytestmark = pytest.mark.django_db(transaction=True)


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


def test_event_meta_ordering_by_starts_at() -> None:
    """Events are returned ordered by starts_at ascending."""
    prod = ProductionFactory()
    hall = HallFactory()

    now = timezone.now()
    e2 = EventFactory(production=prod, hall=hall, starts_at=now + timedelta(days=1))
    e1 = EventFactory(production=prod, hall=hall, starts_at=now)

    events = list(Event.objects.all())
    assert [e.id for e in events] == [e1.id, e2.id]


def test_event_constraint_name_present() -> None:
    """The check constraint 'event_ends_after_starts' must be declared on the model."""
    names = {c.name for c in Event._meta.constraints}
    assert "event_ends_after_starts" in names


def test_event_clean_raises_when_ends_before_starts() -> None:
    """full_clean() must raise ValidationError when ends_at < starts_at."""
    prod = ProductionFactory()
    hall = HallFactory()
    now = timezone.now()

    e = Event(
        production=prod,
        hall=hall,
        starts_at=now,
        ends_at=now - timedelta(minutes=1),
    )
    with pytest.raises(ValidationError):
        e.full_clean()


def test_event_allows_equal_start_and_end() -> None:
    """Equal start/end timestamps are allowed."""
    prod = ProductionFactory()
    hall = HallFactory()
    now = timezone.now()

    e = Event(
        production=prod,
        hall=hall,
        starts_at=now,
        ends_at=now,
    )
    e.full_clean()
    e.save()
    assert e.id is not None


def test_event_allows_null_starts_or_ends() -> None:
    """Events with both timestamps null, or only starts_at set, are valid."""
    prod = ProductionFactory()
    hall = HallFactory()

    e1 = Event(production=prod, hall=hall, starts_at=None, ends_at=None)
    e1.full_clean()
    e1.save()
    assert e1.id is not None

    e2 = Event(
        production=prod,
        hall=hall,
        starts_at=timezone.now(),
        ends_at=None,
    )
    e2.full_clean()
    e2.save()
    assert e2.id is not None


def test_event_allows_end_without_start() -> None:
    """An ends_at without a starts_at is valid."""
    prod = ProductionFactory()
    hall = HallFactory()

    e3 = Event(
        production=prod,
        hall=hall,
        starts_at=None,
        ends_at=timezone.now(),
    )
    e3.full_clean()
    e3.save()
    assert e3.id is not None


# ---------------------------------------------------------------------------
# EventPrice - constraint / index metadata
# ---------------------------------------------------------------------------


def test_event_price_constraint_name_present() -> None:
    """The unique constraint 'uniq_event_rank_price' must be declared on EventPrice."""
    names = {c.name for c in EventPrice._meta.constraints}
    assert "uniq_event_rank_price" in names


def test_event_price_indexes_present_by_fields() -> None:
    """Required indexes on EventPrice must cover (event,) and (event, price_rank, price)."""
    idx_fields = [tuple(idx.fields) for idx in EventPrice._meta.indexes]
    assert ("event",) in idx_fields
    assert ("event", "price_rank", "price") in idx_fields


# ---------------------------------------------------------------------------
# EventPrice - uniqueness enforcement
# ---------------------------------------------------------------------------


def test_event_price_unique_per_event_price_rank_and_price() -> None:
    """Two EventPrices with the same (event, price_rank, price) must fail validation."""
    event = EventFactory(starts_at=timezone.now())
    rank = PriceRankFactory(position=1, sold_out_buffer=0)
    price = PriceFactory()

    ep1 = EventPrice(event=event, price_rank=rank, price=price, amount=Decimal("10.00"), available=10)
    ep1.full_clean()
    ep1.save()

    ep2 = EventPrice(event=event, price_rank=rank, price=price, amount=Decimal("12.00"), available=5)
    with pytest.raises(ValidationError):
        ep2.full_clean()


def test_event_price_same_rank_different_price_is_allowed() -> None:
    """Same (event, price_rank) but different price FK is a distinct, valid entry."""
    event = EventFactory(starts_at=timezone.now())
    rank = PriceRankFactory(position=1, sold_out_buffer=0)
    price_a = PriceFactory()
    price_b = PriceFactory()

    ep1 = EventPrice(
        event=event,
        price_rank=rank,
        price=price_a,
        amount=Decimal("10.00"),
        available=10,
    )
    ep1.full_clean()
    ep1.save()

    ep2 = EventPrice(
        event=event,
        price_rank=rank,
        price=price_b,
        amount=Decimal("12.00"),
        available=5,
    )
    ep2.full_clean()
    ep2.save()

    assert EventPrice.objects.filter(event=event).count() == 2


def test_event_price_same_price_different_rank_is_allowed() -> None:
    """Same (event, price) but different price_rank is a distinct, valid entry."""
    event = EventFactory(starts_at=timezone.now())
    rank_a = PriceRankFactory(position=1, sold_out_buffer=0)
    rank_b = PriceRankFactory(position=2, sold_out_buffer=0)
    price = PriceFactory()

    ep1 = EventPrice(
        event=event,
        price_rank=rank_a,
        price=price,
        amount=Decimal("10.00"),
        available=10,
    )
    ep1.full_clean()
    ep1.save()

    ep2 = EventPrice(event=event, price_rank=rank_b, price=price, amount=Decimal("9.00"), available=8)
    ep2.full_clean()
    ep2.save()

    assert EventPrice.objects.filter(event=event).count() == 2


# ---------------------------------------------------------------------------
# EventPrice - reverse relation & cascade behaviour
# ---------------------------------------------------------------------------


def test_event_price_reverse_relation_from_event() -> None:
    """event.prices must return all EventPrice rows linked to that event."""
    event = EventFactory(starts_at=timezone.now())
    rank1 = PriceRankFactory(position=1, sold_out_buffer=0)
    rank2 = PriceRankFactory(position=2, sold_out_buffer=0)

    p1 = EventPriceFactory(event=event, price_rank=rank1, amount="10.00", available=10)
    p2 = EventPriceFactory(event=event, price_rank=rank2, amount="12.00", available=5)

    assert event.prices.count() == 2
    assert set(event.prices.values_list("id", flat=True)) == {p1.id, p2.id}


def test_event_price_cascade_delete_event_deletes_prices() -> None:
    """Deleting an Event must cascade-delete all its EventPrice rows."""
    event = EventFactory(starts_at=timezone.now())
    rank = PriceRankFactory(position=1, sold_out_buffer=0)

    EventPriceFactory(event=event, price_rank=rank, amount="10.00", available=10)
    EventPriceFactory(event=event, price_rank=None, amount="8.00", available=3)

    event.delete()
    assert EventPrice.objects.count() == 0


def test_event_price_set_null_when_price_rank_deleted() -> None:
    """Deleting a PriceRank must set EventPrice.price_rank to NULL (not cascade)."""
    event = EventFactory(starts_at=timezone.now())
    rank = PriceRankFactory(position=1, sold_out_buffer=0)

    ep = EventPriceFactory(event=event, price_rank=rank, amount="10.00", available=10)
    rank.delete()

    ep.refresh_from_db()
    assert ep.price_rank_id is None


def test_event_price_set_null_when_price_deleted() -> None:
    """Deleting a Price must set EventPrice.price to NULL (not cascade)."""
    event = EventFactory(starts_at=timezone.now())
    price = PriceFactory()

    ep = EventPriceFactory(event=event, price=price, amount="15.00", available=20)
    price.delete()

    ep.refresh_from_db()
    assert ep.price_id is None


# ---------------------------------------------------------------------------
# EventPrice - price FK presence
# ---------------------------------------------------------------------------


def test_event_price_stores_price_fk() -> None:
    """EventPrice correctly stores and retrieves the price FK."""
    event = EventFactory(starts_at=timezone.now())
    price = PriceFactory()

    ep = EventPriceFactory(event=event, price=price, amount="20.00", available=15)
    ep.refresh_from_db()

    assert ep.price_id == price.id


def test_event_price_price_fk_can_be_null() -> None:
    """EventPrice.price is optional; a NULL value must be accepted."""
    event = EventFactory(starts_at=timezone.now())

    ep = EventPriceFactory(event=event, price=None, amount="5.00", available=50)
    ep.refresh_from_db()

    assert ep.price_id is None


# ---------------------------------------------------------------------------
# EventPrice - __str__
# ---------------------------------------------------------------------------


def test_event_price_str_representation() -> None:
    """__str__ must follow the pattern '<event> - <rank> (€<amount>)'."""
    price = EventPriceFactory(amount="10.00", available=10)
    rank = str(price.price_rank) if price.price_rank else "No rank"
    expected = f"{price.event} - {rank} (€{price.amount})"

    assert str(price) == expected
