from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.events.models import Event, EventPrice
from tests.factories.event import EventFactory, EventPriceFactory
from tests.factories.pricing import PriceRankFactory

pytestmark = pytest.mark.django_db


# =====================================================
# Event
# =====================================================

class TestEventModel:
    """Tests for the Event model behavior and constraints."""

    def test_event_creation(self):
        """Test that an Event can be created successfully."""
        event = EventFactory.create()

        assert event.pk is not None
        assert event.production is not None
        assert event.hall is not None
        assert event.ends_at > event.starts_at

    def test_event_ends_after_starts_constraint(self):
        """Reject events where end time is before start time."""
        starts = timezone.now()
        ends = starts - timedelta(hours=1)

        with pytest.raises(ValidationError):
            EventFactory.create(starts_at=starts, ends_at=ends)

    def test_event_allows_null_times(self):
        """Allow events without explicit start and end timestamps."""
        event = EventFactory.create(starts_at=None, ends_at=None)

        assert event.starts_at is None
        assert event.ends_at is None

    def test_event_clean_raises_when_ends_before_starts(self):
        """Model clean should raise when end time is before start time."""
        starts = timezone.now()
        event = EventFactory.build(
            starts_at=starts, ends_at=starts - timedelta(minutes=1)
        )

        with pytest.raises(ValidationError):
            event.clean()

    def test_event_clean_raises_when_ends_equals_starts(self):
        """Model clean should raise when end and start time are equal."""
        starts = timezone.now()
        event = EventFactory.build(starts_at=starts, ends_at=starts)

        with pytest.raises(ValidationError):
            event.clean()

    def test_event_clean_passes_when_ends_after_starts(self):
        """Model clean should pass when end time is after start time."""
        event = EventFactory.create()
        event.ends_at = event.starts_at + timedelta(minutes=30)

        event.clean()
    
    def test_event_ordering(self):
        """Events are ordered by starts_at ascending by default."""
        now = timezone.now()

        e1 = EventFactory.create(starts_at=now)
        e2 = EventFactory.create(starts_at=now + timedelta(days=1))
        e3 = EventFactory.create(starts_at=now + timedelta(days=2))

        events = list(Event.objects.all())

        assert events[0] == e1
        assert events[1] == e2
        assert events[2] == e3

    def test_event_hall_nullable(self):
        """Hall relation can be null."""
        event = EventFactory.create(hall=None)

        assert event.hall is None

    def test_eventprice_cascade_on_event_delete(self):
        """Deleting an event should cascade and delete linked EventPrice rows."""
        event = EventFactory.create()
        EventPriceFactory.create(event=event)

        event.delete()

        assert EventPrice.objects.count() == 0

    def test_event_allows_blank_ticketing_url(self):
        """Ticketing URL can be stored as an empty string."""
        event = EventFactory.create(ticketing_url="")

        assert event.ticketing_url == ""

# =====================================================
# EventPrice
# =====================================================

class TestEventPriceModel:
    """Tests for EventPrice model behavior and constraints."""

    def test_eventprice_creation(self):
        """Create an EventPrice with valid defaults from the factory."""
        price = EventPriceFactory.create()

        assert price.pk is not None
        assert price.event is not None
        assert price.price_rank is not None
        assert price.available >= 0

    def test_unique_event_price_rank_constraint(self):
        """Prevent duplicate (event, price_rank) combinations."""
        event = EventFactory.create()
        rank = PriceRankFactory.create()
        EventPriceFactory.create(event=event, price_rank=rank)

        with pytest.raises(ValidationError):
            EventPriceFactory.create(event=event, price_rank=rank)

    def test_same_rank_allowed_for_different_events(self):
        """Allow reusing the same rank across different events."""
        rank = PriceRankFactory.create()

        first = EventPriceFactory.create(price_rank=rank)
        second = EventPriceFactory.create(price_rank=rank)

        assert first.event_id != second.event_id

    def test_different_ranks_allowed_for_same_event(self):
        """Allow multiple ranks for a single event."""
        event = EventFactory.create()
        first = EventPriceFactory.create(
            event=event, price_rank=PriceRankFactory.create()
        )
        second = EventPriceFactory.create(
            event=event, price_rank=PriceRankFactory.create()
        )

        assert first.pk != second.pk

    def test_price_rank_set_null_on_delete(self):
        """Deleting a rank should set price_rank to null on EventPrice."""
        rank = PriceRankFactory.create()
        price = EventPriceFactory.create(price_rank=rank)

        rank.delete()
        price.refresh_from_db()

        assert price.price_rank is None

    def test_available_must_be_positive_or_zero(self):
        """Reject negative available ticket counts."""
        price = EventPriceFactory.build(available=-1)

        with pytest.raises(ValidationError):
            price.full_clean()
