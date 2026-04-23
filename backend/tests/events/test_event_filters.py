"""
Tests for apps/events/filters.py and apps/events/views.py.
"""

from django.test import override_settings
from django.utils import timezone
import pytest

from apps.events.filters import EventFilter
from apps.events.models import Event
from tests.factories.event import EventFactory
from tests.factories.language import LanguageFactory
from tests.factories.location import HallFactory, LocationFactory, SpaceFactory
from tests.factories.production import ProductionFactory, ProductionTranslationFactory
from tests.helpers.api import INTERNAL_API_KEY, PUBLIC_API_KEY, BaseViewSetTestCase, paginated_results
from tests.helpers.api import public_headers as pub_headers

pytestmark = pytest.mark.django_db


def _dt(days_offset=0):
    return timezone.now() + timezone.timedelta(days=days_offset)


# =====================================================
# EventFilter
# =====================================================


class TestEventFilter:
    def _qs(self, params):
        return EventFilter(params, queryset=Event.objects.all()).qs

    # --- production ---

    def test_filter_by_production(self):
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        EventFactory(production=prod_a)
        EventFactory(production=prod_b)

        assert self._qs({"production": prod_a.id}).count() == 1

    # --- hall ---

    def test_filter_by_hall(self):
        hall_a = HallFactory()
        hall_b = HallFactory()
        EventFactory(hall=hall_a)
        EventFactory(hall=hall_b)

        assert self._qs({"hall": hall_a.id}).count() == 1

    # --- location (FK chain) ---

    def test_filter_by_location_traverses_fk_chain(self):
        loc_a = LocationFactory()
        loc_b = LocationFactory()
        hall_a = HallFactory(space=SpaceFactory(location=loc_a))
        hall_b = HallFactory(space=SpaceFactory(location=loc_b))
        EventFactory(hall=hall_a)
        EventFactory(hall=hall_b)

        assert self._qs({"location": loc_a.id}).count() == 1

    # --- starts_at range ---

    def test_starts_at_after(self):
        EventFactory(starts_at=_dt(10), ends_at=_dt(11))
        EventFactory(starts_at=_dt(-10), ends_at=_dt(-9))

        assert self._qs({"starts_at_after": _dt(1).isoformat()}).count() == 1

    def test_starts_at_before(self):
        EventFactory(starts_at=_dt(10), ends_at=_dt(11))
        EventFactory(starts_at=_dt(-10), ends_at=_dt(-9))

        assert self._qs({"starts_at_before": _dt(1).isoformat()}).count() == 1

    def test_starts_at_range(self):
        EventFactory(starts_at=_dt(1), ends_at=_dt(2))
        EventFactory(starts_at=_dt(5), ends_at=_dt(6))
        EventFactory(starts_at=_dt(10), ends_at=_dt(11))

        result = self._qs(
            {
                "starts_at_after": _dt(0).isoformat(),
                "starts_at_before": _dt(7).isoformat(),
            }
        )

        assert result.count() == 2

    # --- ends_at range ---

    def test_ends_at_after(self):
        EventFactory(starts_at=_dt(-2), ends_at=_dt(-1))
        EventFactory(starts_at=_dt(1), ends_at=_dt(5))

        assert self._qs({"ends_at_after": _dt(0).isoformat()}).count() == 1

    def test_ends_at_before(self):
        EventFactory(starts_at=_dt(-2), ends_at=_dt(-1))
        EventFactory(starts_at=_dt(1), ends_at=_dt(5))

        assert self._qs({"ends_at_before": _dt(0).isoformat()}).count() == 1

    # --- external_id ---

    def test_external_id_iexact(self):
        EventFactory(external_id="EVT-001")
        EventFactory(external_id="EVT-002")

        assert self._qs({"external_id": "evt-001"}).count() == 1

    # --- combined ---

    def test_production_and_date_range_combined(self):
        prod = ProductionFactory()
        EventFactory(production=prod, starts_at=_dt(1), ends_at=_dt(2))
        EventFactory(production=prod, starts_at=_dt(10), ends_at=_dt(11))
        EventFactory(production=ProductionFactory(), starts_at=_dt(1), ends_at=_dt(2))

        result = self._qs(
            {
                "production": prod.id,
                "starts_at_before": _dt(5).isoformat(),
            }
        )

        assert result.count() == 1

    def test_no_params_returns_all(self):
        EventFactory.create_batch(3)

        assert self._qs({}).count() == 3


# =====================================================
# EventViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUBLIC_API_KEY, INTERNAL_API_KEY=INTERNAL_API_KEY)
class TestEventViewSet(BaseViewSetTestCase):
    resource_name = "event"

    def setUp(self):
        super().setUp()
        Event.objects.all().delete()

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        assert response.status_code in (401, 403)

    def test_public_can_list(self):
        EventFactory.create_batch(2)
        response = self.client.get(self.list_url(), **self.pub_headers())
        assert response.status_code == 200
        results = paginated_results(response)
        assert len(results) == 2

    def test_public_can_retrieve(self):
        event = EventFactory()
        response = self.client.get(self.detail_url(pk=event.pk), **self.pub_headers())
        assert response.status_code == 200

    def test_public_cannot_create(self):
        response = self.client.post(self.list_url(), {}, format="json", **self.pub_headers())
        assert response.status_code == 403

    def test_public_cannot_update(self):
        event = EventFactory()
        response = self.client.patch(self.detail_url(pk=event.pk), {}, format="json", **self.pub_headers())
        assert response.status_code == 403

    def test_public_cannot_delete(self):
        event = EventFactory()
        response = self.client.delete(self.detail_url(pk=event.pk), **self.pub_headers())
        assert response.status_code == 403

    def test_internal_can_delete(self):
        event = EventFactory()
        response = self.client.delete(self.detail_url(pk=event.pk), **self.int_headers())
        assert response.status_code == 204
        assert not Event.objects.filter(pk=event.pk).exists()

    # --- filtering ---

    def test_filter_by_production(self):
        prod = ProductionFactory()
        EventFactory(production=prod)
        EventFactory()
        response = self.client.get(self.list_url(), {"production": prod.id}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_filter_by_hall(self):
        hall = HallFactory()
        EventFactory(hall=hall)
        EventFactory()
        response = self.client.get(self.list_url(), {"hall": hall.id}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_filter_by_location(self):
        location = LocationFactory()
        hall = HallFactory(space=SpaceFactory(location=location))
        EventFactory(hall=hall)
        EventFactory()
        response = self.client.get(self.list_url(), {"location": location.id}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_filter_starts_at_after(self):
        EventFactory(starts_at=_dt(5), ends_at=_dt(6))
        EventFactory(starts_at=_dt(-5), ends_at=_dt(-4))
        response = self.client.get(self.list_url(), {"starts_at_after": _dt(1).isoformat()}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_starts_at_before(self):
        EventFactory(starts_at=_dt(5), ends_at=_dt(6))
        EventFactory(starts_at=_dt(-5), ends_at=_dt(-4))
        response = self.client.get(self.list_url(), {"starts_at_before": _dt(1).isoformat()}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    # --- ordering ---

    def test_default_ordering_ascending_by_starts_at(self):
        EventFactory(starts_at=_dt(5), ends_at=_dt(6))
        EventFactory(starts_at=_dt(1), ends_at=_dt(2))
        response = self.client.get(self.list_url(), **pub_headers())
        dates = [r["starts_at"] for r in response.data.get("results", response.data)]
        assert dates == sorted(dates)

    def test_ordering_by_starts_at_descending(self):
        EventFactory(starts_at=_dt(1), ends_at=_dt(2))
        EventFactory(starts_at=_dt(5), ends_at=_dt(6))
        response = self.client.get(self.list_url(), {"ordering": "-starts_at"}, **pub_headers())
        dates = [r["starts_at"] for r in response.data.get("results", response.data)]
        assert dates == sorted(dates, reverse=True)

    # --- search ---

    def test_search_by_production_title(self):
        lang = LanguageFactory(code="en")
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTranslationFactory(production=prod_a, language=lang, title="Hamlet")
        ProductionTranslationFactory(production=prod_b, language=lang, title="Macbeth")
        EventFactory(production=prod_a)
        EventFactory(production=prod_b)
        response = self.client.get(self.list_url(), {"search": "Hamlet"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1
