"""
Tests for apps/locations/filters.py and apps/locations/views.py.
"""

import pytest
from django.urls import reverse

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


class TestLocationViewSet:
    list_url = reverse("location-list")

    def detail_url(self, pk):
        return reverse("location-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self, anon_client):
        assert anon_client.get(self.list_url).status_code in (401, 403)

    def test_public_can_list(self, public_client):
        LocationFactory.create_batch(2)

        assert public_client.get(self.list_url).status_code == 200

    def test_public_cannot_delete(self, public_client):
        assert public_client.delete(self.detail_url(LocationFactory().pk)).status_code == 403

    def test_internal_can_delete(self, internal_client):
        loc = LocationFactory()

        assert internal_client.delete(self.detail_url(loc.pk)).status_code == 204
        assert not Location.objects.filter(pk=loc.pk).exists()

    def test_filter_by_city(self, public_client):
        LocationFactory(city="Gent")
        LocationFactory(city="Brussel")

        assert len(public_client.get(self.list_url, {"city": "Gent"}).data["results"]) == 1

    def test_filter_by_is_own_location(self, public_client):
        LocationFactory(is_own_location=True)
        LocationFactory(is_own_location=False)

        assert len(public_client.get(self.list_url, {"is_own_location": "true"}).data["results"]) == 1

    def test_filter_by_translated_name(self, public_client):
        lang = LanguageFactory(code="nl")
        loc = LocationFactory()
        LocationTranslationFactory(location=loc, language=lang, name="Stadsschouwburg")
        LocationFactory()

        assert len(public_client.get(self.list_url, {"name": "stads"}).data["results"]) == 1

    def test_ordering_by_city(self, public_client):
        LocationFactory(city="Gent")
        LocationFactory(city="Antwerpen")

        response = public_client.get(self.list_url, {"ordering": "city"})
        cities = [r["city"] for r in response.data["results"]]

        assert cities == sorted(cities)

    def test_search_by_city(self, public_client):
        LocationFactory(city="Gent")
        LocationFactory(city="Brussel")

        assert len(public_client.get(self.list_url, {"search": "Gent"}).data["results"]) == 1


# =====================================================
# SpaceViewSet
# =====================================================


class TestSpaceViewSet:
    list_url = reverse("space-list")

    def detail_url(self, pk):
        return reverse("space-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self, anon_client):
        assert anon_client.get(self.list_url).status_code in (401, 403)

    def test_public_can_list(self, public_client):
        SpaceFactory.create_batch(3)

        assert public_client.get(self.list_url).status_code == 200

    def test_filter_by_location(self, public_client):
        loc = LocationFactory()
        SpaceFactory(location=loc)
        SpaceFactory()

        assert len(public_client.get(self.list_url, {"location": loc.id}).data["results"]) == 1

    def test_filter_by_translated_name(self, public_client):
        lang = LanguageFactory(code="nl")
        space = SpaceFactory()
        SpaceTranslationFactory(space=space, language=lang, name="Foyer")
        SpaceFactory()

        assert len(public_client.get(self.list_url, {"name": "foyer"}).data["results"]) == 1

    def test_internal_can_delete(self, internal_client):
        space = SpaceFactory()

        assert internal_client.delete(self.detail_url(space.pk)).status_code == 204


# =====================================================
# HallViewSet
# =====================================================


class TestHallViewSet:
    list_url = reverse("hall-list")

    def detail_url(self, pk):
        return reverse("hall-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self, anon_client):
        assert anon_client.get(self.list_url).status_code in (401, 403)

    def test_public_can_list(self, public_client):
        HallFactory.create_batch(2)

        assert public_client.get(self.list_url).status_code == 200

    def test_filter_by_space(self, public_client):
        space = SpaceFactory()
        HallFactory(space=space)
        HallFactory()

        assert len(public_client.get(self.list_url, {"space": space.id}).data["results"]) == 1

    def test_filter_by_location(self, public_client):
        loc = LocationFactory()
        HallFactory(space=SpaceFactory(location=loc))
        HallFactory()

        assert len(public_client.get(self.list_url, {"location": loc.id}).data["results"]) == 1

    def test_filter_by_seat_selection(self, public_client):
        HallFactory(seat_selection=True)
        HallFactory(seat_selection=False)

        assert len(public_client.get(self.list_url, {"seat_selection": "true"}).data["results"]) == 1

    def test_search_by_translated_name(self, public_client):
        lang = LanguageFactory(code="nl")
        hall = HallFactory()
        HallTranslationFactory(hall=hall, language=lang, name="Grote Zaal")
        HallFactory()

        assert len(public_client.get(self.list_url, {"search": "Grote"}).data["results"]) == 1

    def test_ordering_by_id(self, public_client):
        HallFactory.create_batch(3)

        response = public_client.get(self.list_url, {"ordering": "id"})
        ids = [r["id"] for r in response.data["results"]]

        assert ids == sorted(ids)
