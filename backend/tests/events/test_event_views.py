from datetime import timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from apps.core.views import ApiModelViewSet
from apps.events.models import Event
from apps.events.views import EventViewSet
from apps.locations.models import Location, Space, Hall
from apps.productions.models import Production


PUB_KEY = "pub-event-view-test-key"
INT_KEY = "int-event-view-test-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pub_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {PUB_KEY}"}


def int_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {INT_KEY}"}


def wrong_headers():
    return {"HTTP_AUTHORIZATION": "Api-Key completely-wrong-key"}


def results_list(response):
    """Support both paginated and non-paginated responses."""
    return response.data.get("results", response.data)


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
# Class-level tests
# ---------------------------------------------------------------------------

class TestEventViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        """Test case for test_inherits_from_api_model_viewset."""
        self.assertTrue(issubclass(EventViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        """Test case for test_queryset_model."""
        self.assertEqual(EventViewSet.queryset.model, Event)

    def test_serializer_class(self):
        """Test case for test_serializer_class."""
        from apps.events.serializers import EventSerializer
        self.assertEqual(EventViewSet.serializer_class, EventSerializer)


# ---------------------------------------------------------------------------
# Events — shared setup mixin
# ---------------------------------------------------------------------------

@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class _EventSetupMixin(TestCase):
    def setUp(self):
        self.client = APIClient()

        Event.objects.all().delete()
        Production.objects.all().delete()
        Hall.objects.all().delete()
        Space.objects.all().delete()
        Location.objects.all().delete()

        self.production = Production.objects.create()
        self.hall = make_hall()

        now = timezone.now()
        self.e1 = Event.objects.create(
            production=self.production,
            hall=self.hall,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            ticketing_url="https://example.com/tickets-1",
        )
        self.e2 = Event.objects.create(
            production=self.production,
            hall=self.hall,
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            ticketing_url="https://example.com/tickets-2",
        )


# ---------------------------------------------------------------------------
# GET /api/events/ — list
# ---------------------------------------------------------------------------

class TestEventViewSetList(_EventSetupMixin):
    def test_list_with_public_key_returns_200(self):
        """Test case for test_list_with_public_key_returns_200."""
        response = self.client.get("/api/events/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_with_internal_key_also_returns_200(self):
        """Test case for test_list_with_internal_key_also_returns_200."""
        response = self.client.get("/api/events/?ordering=id", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_returns_events(self):
        """Test case for test_list_returns_events."""
        response = self.client.get("/api/events/?ordering=id", **pub_headers())
        items = results_list(response)
        ids = [item["id"] for item in items]
        self.assertIn(self.e1.id, ids)
        self.assertIn(self.e2.id, ids)

    def test_list_response_has_expected_fields(self):
        """Test case for test_list_response_has_expected_fields."""
        response = self.client.get("/api/events/?ordering=id", **pub_headers())
        item = results_list(response)[0]

        self.assertIn("id", item)
        self.assertIn("production", item)
        self.assertIn("hall", item)
        self.assertIn("starts_at", item)
        self.assertIn("ends_at", item)
        self.assertIn("ticketing_url", item)
        self.assertIn("prices", item)

    def test_list_without_auth_returns_403(self):
        """Test case for test_list_without_auth_returns_403."""
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, 403)

    def test_list_with_wrong_key_returns_401_or_403(self):
        """Test case for test_list_with_wrong_key_returns_401_or_403."""
        response = self.client.get("/api/events/", **wrong_headers())
        self.assertIn(response.status_code, [401, 403])


# ---------------------------------------------------------------------------
# GET /api/events/<id>/ — retrieve
# ---------------------------------------------------------------------------

class TestEventViewSetRetrieve(_EventSetupMixin):
    def test_retrieve_with_public_key_returns_200(self):
        """Test case for test_retrieve_with_public_key_returns_200."""
        response = self.client.get(f"/api/events/{self.e1.id}/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_retrieve_with_internal_key_also_returns_200(self):
        """Test case for test_retrieve_with_internal_key_also_returns_200."""
        response = self.client.get(f"/api/events/{self.e1.id}/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_retrieve_returns_correct_event(self):
        """Test case for test_retrieve_returns_correct_event."""
        response = self.client.get(f"/api/events/{self.e1.id}/", **pub_headers())
        self.assertEqual(response.data["id"], self.e1.id)
        self.assertEqual(response.data["production"], self.production.id)
        self.assertEqual(response.data["hall"], self.hall.id)

    def test_retrieve_nonexistent_returns_404(self):
        """Test case for test_retrieve_nonexistent_returns_404."""
        response = self.client.get("/api/events/999999/", **pub_headers())
        self.assertEqual(response.status_code, 404)

    def test_retrieve_without_auth_returns_403(self):
        """Test case for test_retrieve_without_auth_returns_403."""
        response = self.client.get(f"/api/events/{self.e1.id}/")
        self.assertEqual(response.status_code, 403)

    def test_retrieve_with_wrong_key_returns_401_or_403(self):
        """Test case for test_retrieve_with_wrong_key_returns_401_or_403."""
        response = self.client.get(f"/api/events/{self.e1.id}/", **wrong_headers())
        self.assertIn(response.status_code, [401, 403])


# ---------------------------------------------------------------------------
# POST /api/events/ — create (internal only)
# ---------------------------------------------------------------------------

class TestEventViewSetCreate(_EventSetupMixin):
    def test_create_with_internal_key_returns_201(self):
        """Test case for test_create_with_internal_key_returns_201."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/new",
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 201)

    def test_create_adds_event_to_db(self):
        """Test case for test_create_adds_event_to_db."""
        now = timezone.now()
        self.client.post(
            "/api/events/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/new",
            },
            format="json",
            **int_headers(),
        )
        self.assertTrue(Event.objects.filter(ticketing_url="https://example.com/new").exists())

    def test_create_with_public_key_returns_401_or_403(self):
        """Test case for test_create_with_public_key_returns_401_or_403."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/new",
            },
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, [401, 403])

    def test_create_without_auth_returns_403(self):
        """Test case for test_create_without_auth_returns_403."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/new",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_wrong_key_returns_401_or_403(self):
        """Test case for test_create_with_wrong_key_returns_401_or_403."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/new",
            },
            format="json",
            **wrong_headers(),
        )
        self.assertIn(response.status_code, [401, 403])

    def test_create_missing_required_field_returns_400(self):
        """Test case for test_create_missing_required_field_returns_400."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/new",
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# PUT /api/events/<id>/ — full update (internal only)
# ---------------------------------------------------------------------------

class TestEventViewSetUpdate(_EventSetupMixin):
    def test_put_with_internal_key_returns_200(self):
        """Test case for test_put_with_internal_key_returns_200."""
        now = timezone.now()
        response = self.client.put(
            f"/api/events/{self.e1.id}/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/updated",
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_put_updates_event_in_db(self):
        """Test case for test_put_updates_event_in_db."""
        now = timezone.now()
        self.client.put(
            f"/api/events/{self.e1.id}/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/updated",
            },
            format="json",
            **int_headers(),
        )
        self.e1.refresh_from_db()
        self.assertEqual(self.e1.ticketing_url, "https://example.com/updated")

    def test_put_with_public_key_returns_401_or_403(self):
        """Test case for test_put_with_public_key_returns_401_or_403."""
        now = timezone.now()
        response = self.client.put(
            f"/api/events/{self.e1.id}/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/updated",
            },
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, [401, 403])

    def test_put_nonexistent_returns_404(self):
        """Test case for test_put_nonexistent_returns_404."""
        now = timezone.now()
        response = self.client.put(
            "/api/events/999999/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
                "ticketing_url": "https://example.com/updated",
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# PATCH /api/events/<id>/ — partial update (internal only)
# ---------------------------------------------------------------------------

class TestEventViewSetPartialUpdate(_EventSetupMixin):
    def test_patch_with_internal_key_returns_200(self):
        """Test case for test_patch_with_internal_key_returns_200."""
        response = self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"ticketing_url": "https://example.com/patched"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_patch_updates_only_specified_fields(self):
        """Test case for test_patch_updates_only_specified_fields."""
        self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"ticketing_url": "https://example.com/patched"},
            format="json",
            **int_headers(),
        )
        self.e1.refresh_from_db()
        self.assertEqual(self.e1.ticketing_url, "https://example.com/patched")

    def test_patch_with_public_key_returns_401_or_403(self):
        """Test case for test_patch_with_public_key_returns_401_or_403."""
        response = self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"ticketing_url": "https://example.com/patched"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, [401, 403])

    def test_patch_without_auth_returns_403(self):
        """Test case for test_patch_without_auth_returns_403."""
        response = self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"ticketing_url": "https://example.com/patched"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_with_wrong_key_returns_401_or_403(self):
        """Test case for test_patch_with_wrong_key_returns_401_or_403."""
        response = self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"ticketing_url": "https://example.com/patched"},
            format="json",
            **wrong_headers(),
        )
        self.assertIn(response.status_code, [401, 403])


# ---------------------------------------------------------------------------
# DELETE /api/events/<id>/ — destroy (internal only)
# ---------------------------------------------------------------------------

class TestEventViewSetDelete(_EventSetupMixin):
    def test_delete_with_internal_key_returns_204(self):
        """Test case for test_delete_with_internal_key_returns_204."""
        response = self.client.delete(f"/api/events/{self.e1.id}/", **int_headers())
        self.assertEqual(response.status_code, 204)

    def test_delete_removes_event_from_db(self):
        """Test case for test_delete_removes_event_from_db."""
        self.client.delete(f"/api/events/{self.e1.id}/", **int_headers())
        self.assertFalse(Event.objects.filter(id=self.e1.id).exists())

    def test_delete_with_public_key_returns_401_or_403(self):
        """Test case for test_delete_with_public_key_returns_401_or_403."""
        response = self.client.delete(f"/api/events/{self.e1.id}/", **pub_headers())
        self.assertIn(response.status_code, [401, 403])

    def test_delete_without_auth_returns_403(self):
        """Test case for test_delete_without_auth_returns_403."""
        response = self.client.delete(f"/api/events/{self.e1.id}/")
        self.assertEqual(response.status_code, 403)

    def test_delete_nonexistent_returns_404(self):
        """Test case for test_delete_nonexistent_returns_404."""
        response = self.client.delete("/api/events/999999/", **int_headers())
        self.assertEqual(response.status_code, 404)