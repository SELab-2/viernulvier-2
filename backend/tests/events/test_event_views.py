from datetime import timedelta

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.events.models import Event
from apps.events.views import EventViewSet
from tests.factories.event import EventFactory, EventPriceFactory
from tests.factories.language import LanguageFactory
from tests.factories.location import HallFactory, HallTranslationFactory
from tests.factories.pricing import PriceRankFactory, PriceRankTranslationFactory
from tests.factories.production import ProductionFactory, ProductionTranslationFactory

PUB_KEY = "pub-event-view-test-key"
INT_KEY = "int-event-view-test-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


def wrong_headers():
    return {"HTTP_X_API_KEY": "completely-wrong-key"}


def results_list(response):
    """Support both paginated and non-paginated responses."""
    return response.data.get("results", response.data)


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
# Events - shared setup mixin
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class _EventSetupMixin(TestCase):
    def setUp(self):
        self.client = APIClient()

        Event.objects.all().delete()
        self.production = ProductionFactory()
        self.hall = HallFactory()

        now = timezone.now()
        self.e1 = EventFactory(
            production=self.production,
            hall=self.hall,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
        )
        self.e2 = EventFactory(
            production=self.production,
            hall=self.hall,
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
        )


# ---------------------------------------------------------------------------
# GET /api/events/ - list
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
        self.assertIn("prices", item)

    def test_list_without_auth_returns_401(self):
        """Test case for test_list_without_auth_returns_401."""
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, 401)

    def test_list_with_wrong_key_returns_401(self):
        """Test case for test_list_with_wrong_key_returns_401."""
        response = self.client.get("/api/events/", **wrong_headers())
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# GET /api/events/<id>/ - retrieve
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
        self.assertEqual(response.data["production"]["id"], self.production.id)
        self.assertEqual(response.data["hall"]["id"], self.hall.id)

    def test_retrieve_nonexistent_returns_404(self):
        """Test case for test_retrieve_nonexistent_returns_404."""
        response = self.client.get("/api/events/999999/", **pub_headers())
        self.assertEqual(response.status_code, 404)

    def test_retrieve_without_auth_returns_401(self):
        """Test case for test_retrieve_without_auth_returns_401."""
        response = self.client.get(f"/api/events/{self.e1.id}/")
        self.assertEqual(response.status_code, 401)

    def test_retrieve_with_wrong_key_returns_401(self):
        """Test case for test_retrieve_with_wrong_key_returns_401."""
        response = self.client.get(f"/api/events/{self.e1.id}/", **wrong_headers())
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# POST /api/events/ - create (internal only)
# ---------------------------------------------------------------------------


class TestEventViewSetCreate(_EventSetupMixin):
    def test_create_with_internal_key_returns_201(self):
        """Test case for test_create_with_internal_key_returns_201."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "production_id": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
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
                "production_id": self.production.id,
                "hall_id": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
            },
            format="json",
            **int_headers(),
        )
        self.assertTrue(Event.objects.filter(starts_at=(now.isoformat())).exists())

    def test_create_with_public_key_returns_403(self):
        """Test case for test_create_with_public_key_returns_403."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "production_id": self.production.id,
                "hall_id": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
            },
            format="json",
            **pub_headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_create_without_auth_returns_401(self):
        """Test case for test_create_without_auth_returns_401."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_create_with_wrong_key_returns_401(self):
        """Test case for test_create_with_wrong_key_returns_401."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
            },
            format="json",
            **wrong_headers(),
        )
        self.assertEqual(response.status_code, 401)

    def test_create_missing_required_field_returns_400(self):
        """Test case for test_create_missing_required_field_returns_400."""
        now = timezone.now()
        response = self.client.post(
            "/api/events/",
            {
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# PUT /api/events/<id>/ - full update (internal only)
# ---------------------------------------------------------------------------


class TestEventViewSetUpdate(_EventSetupMixin):
    def test_put_with_internal_key_returns_200(self):
        """Test case for test_put_with_internal_key_returns_200."""
        now = timezone.now()
        response = self.client.put(
            f"/api/events/{self.e1.id}/",
            {
                "production_id": self.production.id,
                "hall_id": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_put_with_public_key_returns_403(self):
        """Test case for test_put_with_public_key_returns_403."""
        now = timezone.now()
        response = self.client.put(
            f"/api/events/{self.e1.id}/",
            {
                "production": self.production.id,
                "hall": self.hall.id,
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=2)).isoformat(),
            },
            format="json",
            **pub_headers(),
        )
        self.assertEqual(response.status_code, 403)

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
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# PATCH /api/events/<id>/ - partial update (internal only)
# ---------------------------------------------------------------------------


class TestEventViewSetPartialUpdate(_EventSetupMixin):
    def test_patch_with_internal_key_returns_200(self):
        """Test case for test_patch_with_internal_key_returns_200."""
        response = self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"starts_at": (timezone.now() + timedelta(hours=1)).isoformat()},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_patch_updates_only_specified_fields(self):
        """Test case for test_patch_updates_only_specified_fields."""
        new_start_time = timezone.now() + timedelta(hours=1)

        response = self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"starts_at": new_start_time.isoformat()},
            format="json",
            **int_headers(),
        )

        self.assertEqual(response.status_code, 200)

        self.e1.refresh_from_db()

        self.assertAlmostEqual(self.e1.starts_at, new_start_time, delta=timedelta(seconds=1))

    def test_patch_with_public_key_returns_403(self):
        """Test case for test_patch_with_public_key_returns_403."""
        response = self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"starts_at": (timezone.now() + timedelta(hours=1)).isoformat()},
            format="json",
            **pub_headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_without_auth_returns_401(self):
        """Test case for test_patch_without_auth_returns_401."""
        response = self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"starts_at": (timezone.now() + timedelta(hours=1)).isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_patch_with_wrong_key_returns_401(self):
        """Test case for test_patch_with_wrong_key_returns_401."""
        response = self.client.patch(
            f"/api/events/{self.e1.id}/",
            {"starts_at": (timezone.now() + timedelta(hours=1)).isoformat()},
            format="json",
            **wrong_headers(),
        )
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# DELETE /api/events/<id>/ - destroy (internal only)
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

    def test_delete_with_public_key_returns_403(self):
        """Test case for test_delete_with_public_key_returns_403."""
        response = self.client.delete(f"/api/events/{self.e1.id}/", **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_delete_without_auth_returns_401(self):
        """Test case for test_delete_without_auth_returns_401."""
        response = self.client.delete(f"/api/events/{self.e1.id}/")
        self.assertEqual(response.status_code, 401)

    def test_delete_nonexistent_returns_404(self):
        """Test case for test_delete_nonexistent_returns_404."""
        response = self.client.delete("/api/events/999999/", **int_headers())
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# N+1 guard - queryset prefetches
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestEventViewSetPrefetch(TestCase):
    """Ensure list view stays bounded in queries when data volume grows."""

    def setUp(self):
        self.client = APIClient()
        self.lang_nl = LanguageFactory.create(code="nl", name="Dutch")
        self.lang_en = LanguageFactory.create(code="en", name="English")

        for idx in range(5):
            production = ProductionFactory()
            ProductionTranslationFactory(
                production=production,
                language=self.lang_nl,
                title=f"Titel {idx}",
            )
            ProductionTranslationFactory(
                production=production,
                language=self.lang_en,
                title=f"Title {idx}",
            )

            hall = HallFactory()
            HallTranslationFactory(hall=hall, language=self.lang_nl, name=f"Zaal {idx}")
            HallTranslationFactory(hall=hall, language=self.lang_en, name=f"Hall {idx}")

            rank = PriceRankFactory(position=idx + 1)
            PriceRankTranslationFactory(price_rank=rank, language=self.lang_nl, description="NL")
            PriceRankTranslationFactory(price_rank=rank, language=self.lang_en, description="EN")

            event = EventFactory(
                production=production,
                hall=hall,
                starts_at=timezone.now() + timedelta(days=idx),
                ends_at=timezone.now() + timedelta(days=idx, hours=2),
            )
            EventPriceFactory(event=event, price_rank=rank)

    def test_list_prefetches_related_models(self):
        # Ensure query count stays bounded when related data grows
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get("/api/events/?ordering=id", **pub_headers())
        
        for i, query in enumerate(captured.captured_queries):
            print(f"{i+1}: {query['sql'][:200]}")


        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(results_list(response)), 5)
        self.assertLessEqual(len(captured), 14)
