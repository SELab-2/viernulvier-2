"""
Tests for apps/locations/views.py - Location, Space, Hall viewsets

Covers:
- Class-level inheritance and queryset models
- Prefetch/select_related configuration to avoid N+1
- CRUD access control following ApiModelViewSet rules
- Basic response field presence
"""

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.locations.models import Hall, Location, Space
from apps.locations.views import HallViewSet, LocationViewSet, SpaceViewSet
from tests.factories.language import LanguageFactory
from tests.factories.location import (
    HallFactory,
    HallTranslationFactory,
    LocationFactory,
    LocationTranslationFactory,
    SpaceFactory,
)

PUB_KEY = "pub-view-test-key"
INT_KEY = "int-view-test-key"


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def wrong_headers():
    return {"HTTP_X_API_KEY": "completely-wrong-key"}


def results_list(response):
    return response.data.get("results", response.data)


# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestLocationViewSetClass(TestCase):
    """Class-level checks for LocationViewSet."""

    def test_inherits_api_model_viewset(self):
        self.assertTrue(issubclass(LocationViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        self.assertEqual(LocationViewSet.queryset.model, Location)

    def test_prefetch_translations(self):
        self.assertIn("translations__language", LocationViewSet.queryset._prefetch_related_lookups)


class TestSpaceViewSetClass(TestCase):
    """Class-level checks for SpaceViewSet."""

    def test_inherits_api_model_viewset(self):
        self.assertTrue(issubclass(SpaceViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        self.assertEqual(SpaceViewSet.queryset.model, Space)

    def test_select_related_location(self):
        self.assertIn("location", SpaceViewSet.queryset.query.select_related)

    def test_prefetch_translations(self):
        self.assertIn("translations__language", SpaceViewSet.queryset._prefetch_related_lookups)


class TestHallViewSetClass(TestCase):
    """Class-level checks for HallViewSet."""

    def test_inherits_api_model_viewset(self):
        self.assertTrue(issubclass(HallViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        self.assertEqual(HallViewSet.queryset.model, Hall)

    def test_select_related_space_and_location(self):
        sel = HallViewSet.queryset.query.select_related
        self.assertIn("space", sel)
        self.assertIn("location", sel.get("space", {}))

    def test_prefetch_translations(self):
        self.assertIn("translations__language", HallViewSet.queryset._prefetch_related_lookups)


# ---------------------------------------------------------------------------
# N+1 guards - queryset prefetches
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLocationViewSetPrefetch(TestCase):
    """Ensure location list stays bounded in queries with translations present."""

    def setUp(self):
        self.client = APIClient()
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")
        self.lang_en = LanguageFactory(code="en", name="English")

        for idx in range(5):
            loc = LocationFactory(city=f"City {idx}")
            LocationTranslationFactory(location=loc, language=self.lang_nl, name=f"Stad {idx}")
            LocationTranslationFactory(location=loc, language=self.lang_en, name=f"City {idx}")

    def test_location_list_bounded_queries(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/locations/?ordering=id", **pub_headers())

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(results_list(response)), 5)
        self.assertEqual(len(ctx), 4)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestHallViewSetPrefetch(TestCase):
    """Ensure hall list remains bounded with related space/location and translations."""

    def setUp(self):
        self.client = APIClient()
        self.lang_nl = LanguageFactory(code="nl", name="Dutch")
        self.lang_en = LanguageFactory(code="en", name="English")

        for idx in range(4):
            hall = HallFactory()
            HallTranslationFactory(hall=hall, language=self.lang_nl, name=f"Zaal {idx}")
            HallTranslationFactory(hall=hall, language=self.lang_en, name=f"Hall {idx}")

    def test_hall_list_bounded_queries(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/halls/?ordering=id", **pub_headers())

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(results_list(response)), 4)
        self.assertLessEqual(len(ctx), 12)


# ---------------------------------------------------------------------------
# Location endpoints
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLocationViewSet(TestCase):
    """CRUD tests for Location endpoints."""

    def setUp(self):
        self.client = APIClient()
        Location.objects.all().delete()
        self.location = LocationFactory()

    def test_list_public(self):
        response = self.client.get("/api/locations/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_internal(self):
        response = self.client.get("/api/locations/?ordering=id", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_without_auth(self):
        response = self.client.get("/api/locations/")
        self.assertEqual(response.status_code, 401)

    def test_retrieve_public(self):
        response = self.client.get(f"/api/locations/{self.location.id}/", **pub_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.location.id)

    def test_retrieve_wrong_key(self):
        response = self.client.get(f"/api/locations/{self.location.id}/", **wrong_headers())
        self.assertEqual(response.status_code, 401)

    def test_create_internal(self):
        payload = {
            "street": "Main",
            "number": "10",
            "postal_code": "9000",
            "city": "Gent",
            "country": "Belgium",
            "phone_1": "123",
            "phone_2": "",
            "is_own_location": True,
        }
        response = self.client.post("/api/locations/", payload, format="json", **int_headers())
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Location.objects.filter(city="Gent", street="Main").exists())

    def test_create_public_denied(self):
        payload = {
            "street": "Main",
            "number": "10",
            "postal_code": "9000",
            "city": "Gent",
            "country": "Belgium",
        }
        response = self.client.post("/api/locations/", payload, format="json", **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_update_internal(self):
        payload = {
            "street": "Updated",
            "number": "1",
            "postal_code": "9000",
            "city": "Gent",
            "country": "Belgium",
        }
        response = self.client.put(
            f"/api/locations/{self.location.id}/",
            payload,
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.location.refresh_from_db()
        self.assertEqual(self.location.street, "Updated")

    def test_delete_internal(self):
        response = self.client.delete(f"/api/locations/{self.location.id}/", **int_headers())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Location.objects.filter(id=self.location.id).exists())


# ---------------------------------------------------------------------------
# Space endpoints
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestSpaceViewSet(TestCase):
    """CRUD tests for Space endpoints."""

    def setUp(self):
        self.client = APIClient()
        Space.objects.all().delete()
        self.space = SpaceFactory()

    def test_list_public(self):
        response = self.client.get("/api/spaces/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_retrieve_public(self):
        response = self.client.get(f"/api/spaces/{self.space.id}/", **pub_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["location"]["id"], self.space.location.id)

    def test_create_internal(self):
        location = LocationFactory()
        response = self.client.post(
            "/api/spaces/",
            {"location_id": location.id},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Space.objects.filter(location=location).count() >= 1)

    def test_update_internal(self):
        other_location = LocationFactory()
        response = self.client.patch(
            f"/api/spaces/{self.space.id}/",
            {"location_id": other_location.id},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.space.refresh_from_db()
        self.assertEqual(self.space.location, other_location)

    def test_delete_internal(self):
        response = self.client.delete(f"/api/spaces/{self.space.id}/", **int_headers())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Space.objects.filter(id=self.space.id).exists())


# ---------------------------------------------------------------------------
# Hall endpoints
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestHallViewSet(TestCase):
    """CRUD tests for Hall endpoints."""

    def setUp(self):
        self.client = APIClient()
        Hall.objects.all().delete()
        self.hall = HallFactory()

    def test_list_public(self):
        response = self.client.get("/api/halls/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_retrieve_public(self):
        response = self.client.get(f"/api/halls/{self.hall.id}/", **pub_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["space"]["id"], self.hall.space.id)

    def test_create_internal(self):
        space = SpaceFactory()
        response = self.client.post(
            "/api/halls/",
            {"space_id": space.id, "seat_selection": True, "open_seating": False},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Hall.objects.filter(space=space).exists())

    def test_update_internal(self):
        response = self.client.patch(
            f"/api/halls/{self.hall.id}/",
            {"seat_selection": True},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.hall.refresh_from_db()
        self.assertTrue(self.hall.seat_selection)

    def test_delete_internal(self):
        response = self.client.delete(f"/api/halls/{self.hall.id}/", **int_headers())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Hall.objects.filter(id=self.hall.id).exists())
