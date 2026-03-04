"""
Comprehensive tests for apps/events/admin.py

Covers:
- Admin registration for event models
- Admin inheritance (BaseAdmin / ModelAdmin) where applicable
- list_display/list_filter/search_fields/ordering/date_hierarchy basic configuration
- Inline presence (without overly strict assumptions)
- get_queryset optimisation (select_related / prefetch_related) smoke
- Functional admin changelist + changeform (superuser)
"""

from datetime import timedelta

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.admin import BaseAdmin
from apps.events.admin import EventAdmin, EventPriceInline
from apps.events.models import Event
from apps.locations.models import Hall, Location, Space
from apps.productions.models import Production

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_superuser(username="admin"):
    return User.objects.create_superuser(username=username, password="password", email=f"{username}@example.com")


def admin_changelist_url(model):
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")


def admin_change_url(model, pk):
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_change", args=[pk])


def make_hall() -> Hall:
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
# Registration
# ---------------------------------------------------------------------------


class TestEventsAdminRegistration(TestCase):
    def test_event_is_registered(self):
        """Test case for test_event_is_registered."""
        self.assertIn(Event, admin.site._registry)

    def test_registered_admin_class_for_event(self):
        """Test case for test_registered_admin_class_for_event."""
        self.assertIsInstance(admin.site._registry[Event], EventAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestEventsAdminInheritance(TestCase):
    admins = [EventAdmin]

    def test_admins_inherit_from_base_admin_if_used(self):
        """Test case for test_admins_inherit_from_base_admin_if_used."""
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                self.assertTrue(issubclass(admin_class, BaseAdmin))

    def test_admins_inherit_from_model_admin(self):
        """Test case for test_admins_inherit_from_model_admin."""
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                self.assertTrue(issubclass(admin_class, admin.ModelAdmin))


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class TestEventsAdminConfiguration(TestCase):
    def setUp(self):
        self.site = AdminSite()

    def test_event_admin_configuration(self):
        """Test case for test_event_admin_configuration."""
        admin_obj = EventAdmin(Event, self.site)

        # Ordering/date hierarchy (explicit in your events admin)
        self.assertEqual(admin_obj.ordering, ("-starts_at",))
        self.assertEqual(admin_obj.date_hierarchy, "starts_at")

        # Some basic checks without being overly strict
        self.assertIn("production", admin_obj.list_display)
        self.assertIn("hall", admin_obj.list_display)
        self.assertIn("starts_at", admin_obj.list_display)

        self.assertIn("production", admin_obj.autocomplete_fields)
        self.assertIn("hall", admin_obj.autocomplete_fields)

        # Inlines should exist (not strict count)
        self.assertTrue(admin_obj.inlines)
        self.assertIn(EventPriceInline, admin_obj.inlines)

    def test_event_price_inline_configuration(self):
        """Test case for test_event_price_inline_configuration."""
        self.assertEqual(EventPriceInline.extra, 0)
        self.assertIn("price_rank", EventPriceInline.autocomplete_fields)
        self.assertEqual(EventPriceInline.fields, ("price_rank", "amount", "available"))


# ---------------------------------------------------------------------------
# Queryset optimization (smoke)
# ---------------------------------------------------------------------------


class TestEventAdminGetQueryset(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prod = Production.objects.create()
        cls.hall = make_hall()
        now = timezone.now()
        cls.event = Event.objects.create(
            production=cls.prod,
            hall=cls.hall,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            ticketing_url="https://example.com/tickets",
        )

    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()

    def test_event_admin_queryset_has_expected_related_optimizations(self):
        """
        In pricing admin tests we avoid brittle exact query counting and instead assert
        that the queryset is configured to fetch the expected relations efficiently.
        """
        admin_obj = EventAdmin(Event, self.site)
        request = self.factory.get("/admin/")
        qs = admin_obj.get_queryset(request)

        select_related = qs.query.select_related
        self.assertIn("production", select_related)
        self.assertIn("hall", select_related)

        self.assertIn("space", select_related["hall"])
        self.assertIn("location", select_related["hall"]["space"])

        def _prefetch_name(item):
            return getattr(item, "prefetch_to", item)

        prefetches = {_prefetch_name(x) for x in qs._prefetch_related_lookups}
        self.assertIn("prices", prefetches)
        self.assertIn("production__translations", prefetches)
        self.assertIn("hall__translations", prefetches)


# ---------------------------------------------------------------------------
# Functional admin tests (HTTP)
# ---------------------------------------------------------------------------


class TestEventsAdminChangelists(TestCase):
    def setUp(self):
        self.superuser = make_superuser("events_admin")
        self.client.force_login(self.superuser)

        self.prod = Production.objects.create()
        self.hall = make_hall()
        now = timezone.now()
        self.event = Event.objects.create(
            production=self.prod,
            hall=self.hall,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            ticketing_url="https://example.com/tickets",
        )

    def test_event_changelist_returns_200(self):
        """Test case for test_event_changelist_returns_200."""
        response = self.client.get(admin_changelist_url(Event))
        self.assertEqual(response.status_code, 200)

    def test_event_changeform_returns_200(self):
        """Test case for test_event_changeform_returns_200."""
        response = self.client.get(admin_change_url(Event, self.event.pk))
        self.assertEqual(response.status_code, 200)
