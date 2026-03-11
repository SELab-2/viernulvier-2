"""
Tests for apps/locations/filters.py and apps/locations/views.py.
"""

import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.filters import HallFilter, LocationFilter, SpaceFilter
from apps.locations.models import Hall, Location, Space
from tests.factories.language import LanguageFactory
from tests.factories.location import (
    HallFactory,
    HallTranslationFactory,
    LocationFactory,
    LocationTranslationFactory,
    SpaceFactory,
    SpaceTranslationFactory,
)

pytestmark = pytest.mark.django_db

PUB_KEY = "pub-location-filter-test-key"
INT_KEY = "int-location-filter-test-key"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


# =====================================================
# LocationFilter
# =====================================================


class TestLocationFilter:
    def _qs(self, params):
        return LocationFilter(params, queryset=Location.objects.all()).qs

    def test_city_icontains(self):
        LocationFactory(city="Gent")
        LocationFactory(city="Brussel")

        assert self._qs({"city": "gent"}).count() == 1
        assert self._qs({"city": "ent"}).count() == 1

    def test_country_iexact(self):
        LocationFactory(country="BE")
        LocationFactory(country="NL")

        assert self._qs({"country": "be"}).count() == 1
        assert self._qs({"country": "BE"}).count() == 1

    def test_country_no_partial_match(self):
        LocationFactory(country="BE")

        assert self._qs({"country": "B"}).count() == 0

    def test_postal_code_exact(self):
        LocationFactory(postal_code="9000")
        LocationFactory(postal_code="1000")

        assert self._qs({"postal_code": "9000"}).count() == 1

    def test_is_own_location_true(self):
        LocationFactory(is_own_location=True)
        LocationFactory(is_own_location=False)

        assert self._qs({"is_own_location": "true"}).count() == 1

    def test_is_own_location_false(self):
        LocationFactory(is_own_location=True)
        LocationFactory(is_own_location=False)

        assert self._qs({"is_own_location": "false"}).count() == 1

    def test_name_filter_across_translations(self):
        lang = LanguageFactory(code="nl")
        loc_a = LocationFactory()
        loc_b = LocationFactory()
        LocationTranslationFactory(location=loc_a, language=lang, name="Stadsschouwburg")
        LocationTranslationFactory(location=loc_b, language=lang, name="Vooruit")

        result = self._qs({"name": "stads"})

        assert result.count() == 1
        assert result.first() == loc_a

    def test_name_filter_distinct_no_duplicates(self):
        lang_nl = LanguageFactory(code="nl")
        lang_fr = LanguageFactory(code="fr")
        loc = LocationFactory()
        LocationTranslationFactory(location=loc, language=lang_nl, name="Theater")
        LocationTranslationFactory(location=loc, language=lang_fr, name="Theatre")

        assert self._qs({"name": "theat"}).count() == 1

    def test_combined_city_and_is_own(self):
        LocationFactory(city="Gent", is_own_location=True)
        LocationFactory(city="Gent", is_own_location=False)
        LocationFactory(city="Brussel", is_own_location=True)

        assert self._qs({"city": "gent", "is_own_location": "true"}).count() == 1

    def test_no_params_returns_all(self):
        LocationFactory.create_batch(3)

        assert self._qs({}).count() == 3


# =====================================================
# SpaceFilter
# =====================================================


class TestSpaceFilter:
    def _qs(self, params):
        return SpaceFilter(params, queryset=Space.objects.all()).qs

    def test_filter_by_location(self):
        loc_a = LocationFactory()
        loc_b = LocationFactory()
        SpaceFactory(location=loc_a)
        SpaceFactory(location=loc_b)

        assert self._qs({"location": loc_a.id}).count() == 1

    def test_name_filter_across_translations(self):
        lang = LanguageFactory(code="nl")
        space_a = SpaceFactory()
        space_b = SpaceFactory()
        SpaceTranslationFactory(space=space_a, language=lang, name="Foyer")
        SpaceTranslationFactory(space=space_b, language=lang, name="Studio")

        assert self._qs({"name": "foyer"}).count() == 1

    def test_no_params_returns_all(self):
        SpaceFactory.create_batch(3)

        assert self._qs({}).count() == 3


# =====================================================
# HallFilter
# =====================================================


class TestHallFilter:
    def _qs(self, params):
        return HallFilter(params, queryset=Hall.objects.all()).qs

    def test_filter_by_space(self):
        space_a = SpaceFactory()
        space_b = SpaceFactory()
        HallFactory(space=space_a)
        HallFactory(space=space_b)

        assert self._qs({"space": space_a.id}).count() == 1

    def test_filter_by_location_traverses_chain(self):
        loc_a = LocationFactory()
        loc_b = LocationFactory()
        HallFactory(space=SpaceFactory(location=loc_a))
        HallFactory(space=SpaceFactory(location=loc_b))

        assert self._qs({"location": loc_a.id}).count() == 1

    def test_seat_selection_true(self):
        HallFactory(seat_selection=True)
        HallFactory(seat_selection=False)

        assert self._qs({"seat_selection": "true"}).count() == 1

    def test_seat_selection_false(self):
        HallFactory(seat_selection=True)
        HallFactory(seat_selection=False)

        assert self._qs({"seat_selection": "false"}).count() == 1

    def test_open_seating_true(self):
        HallFactory(open_seating=True)
        HallFactory(open_seating=False)

        assert self._qs({"open_seating": "true"}).count() == 1

    def test_name_filter_across_translations(self):
        lang = LanguageFactory(code="nl")
        hall_a = HallFactory()
        hall_b = HallFactory()
        HallTranslationFactory(hall=hall_a, language=lang, name="Grote Zaal")
        HallTranslationFactory(hall=hall_b, language=lang, name="Studio")

        assert self._qs({"name": "grote"}).count() == 1

    def test_combined_seat_selection_and_space(self):
        space = SpaceFactory()
        HallFactory(space=space, seat_selection=True)
        HallFactory(space=space, seat_selection=False)

        assert self._qs({"space": space.id, "seat_selection": "true"}).count() == 1


# =====================================================
# LocationViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLocationViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        Location.objects.all().delete()

    def list_url(self):
        return reverse("location-list")

    def detail_url(self, pk):
        return reverse("location-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        LocationFactory.create_batch(2)
        response = self.client.get(self.list_url(), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_public_cannot_delete(self):
        loc = LocationFactory()
        response = self.client.delete(self.detail_url(loc.pk), **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_internal_can_delete(self):
        loc = LocationFactory()
        response = self.client.delete(self.detail_url(loc.pk), **int_headers())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Location.objects.filter(pk=loc.pk).exists())

    def test_filter_by_city(self):
        LocationFactory(city="Gent")
        LocationFactory(city="Brussel")
        response = self.client.get(self.list_url(), {"city": "Gent"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_is_own_location(self):
        LocationFactory(is_own_location=True)
        LocationFactory(is_own_location=False)
        response = self.client.get(self.list_url(), {"is_own_location": "true"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_translated_name(self):
        lang = LanguageFactory(code="nl")
        loc = LocationFactory()
        LocationTranslationFactory(location=loc, language=lang, name="Stadsschouwburg")
        LocationFactory()
        response = self.client.get(self.list_url(), {"name": "stads"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_ordering_by_city(self):
        LocationFactory(city="Gent")
        LocationFactory(city="Antwerpen")
        response = self.client.get(self.list_url(), {"ordering": "city"}, **pub_headers())
        cities = [r["city"] for r in response.data.get("results", response.data)]
        self.assertEqual(cities, sorted(cities))

    def test_search_by_city(self):
        LocationFactory(city="Gent")
        LocationFactory(city="Brussel")
        response = self.client.get(self.list_url(), {"search": "Gent"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)


# =====================================================
# SpaceViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestSpaceViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        Space.objects.all().delete()

    def list_url(self):
        return reverse("space-list")

    def detail_url(self, pk):
        return reverse("space-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        SpaceFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_filter_by_location(self):
        loc = LocationFactory()
        SpaceFactory(location=loc)
        SpaceFactory()
        response = self.client.get(self.list_url(), {"location": loc.id}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_translated_name(self):
        lang = LanguageFactory(code="nl")
        space = SpaceFactory()
        SpaceTranslationFactory(space=space, language=lang, name="Foyer")
        SpaceFactory()
        response = self.client.get(self.list_url(), {"name": "foyer"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_internal_can_delete(self):
        space = SpaceFactory()
        response = self.client.delete(self.detail_url(space.pk), **int_headers())
        self.assertEqual(response.status_code, 204)


# =====================================================
# HallViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestHallViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        Hall.objects.all().delete()

    def list_url(self):
        return reverse("hall-list")

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        HallFactory.create_batch(2)
        response = self.client.get(self.list_url(), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_filter_by_space(self):
        space = SpaceFactory()
        HallFactory(space=space)
        HallFactory()
        response = self.client.get(self.list_url(), {"space": space.id}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_location(self):
        loc = LocationFactory()
        HallFactory(space=SpaceFactory(location=loc))
        HallFactory()
        response = self.client.get(self.list_url(), {"location": loc.id}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_seat_selection(self):
        HallFactory(seat_selection=True)
        HallFactory(seat_selection=False)
        response = self.client.get(self.list_url(), {"seat_selection": "true"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_search_by_translated_name(self):
        lang = LanguageFactory(code="nl")
        hall = HallFactory()
        HallTranslationFactory(hall=hall, language=lang, name="Grote Zaal")
        HallFactory()
        response = self.client.get(self.list_url(), {"search": "Grote"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_ordering_by_id(self):
        HallFactory.create_batch(3)
        response = self.client.get(self.list_url(), {"ordering": "id"}, **pub_headers())
        ids = [r["id"] for r in response.data.get("results", response.data)]
        self.assertEqual(ids, sorted(ids))
