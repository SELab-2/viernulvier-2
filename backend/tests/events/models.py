import pytest
from django.core.exceptions import ValidationError

from apps.events.models import Event, EventPrice
from tests.factories.event import EventFactory, EventPriceFactory

pytestmark = pytest.mark.django_db


# =====================================================
# Event
# =====================================================

class TestEventModel:
    def test_event_creation(self):
        """Test that an Event can be created successfully."""
        event = EventFactory.create()

        assert event.pk is not None
        assert event.ends_at > event.starts_at
        # TODO: check production and hall

    def test_event_ends_after_starts_constraint():
        starts = timezone.now()
        ends = starts - timedelta(hours=1)

        with pytest.raises(IntegrityError):
            Event.objects.create(
                production=EventFactory().production,
                starts_at=starts,
                ends_at=ends,
            )
    
    def test_event_ordering():
        now = timezone.now()

        e1 = EventFactory.create(starts_at=now + timedelta(days=1))
        e2 = EventFactory.create(starts_at=now)

        events = list(Event.objects.all())

        assert events[0] == e2
        assert events[1] == e1

    def test_event_hall_nullable():
        event = EventFactory.create(hall=None)

        assert event.hall is None
    
    def test_eventprice_cascade_on_event_delete():
        event = EventFactory.create()
        price = EventPriceFactory.create(event=event)

        event.delete()

        assert EventPrice.objects.count() == 0

# =====================================================
# EventPrice
# =====================================================

class TestEventPriceModel:
    pass # TODO
