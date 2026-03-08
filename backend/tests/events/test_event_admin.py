from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.core.admin import BaseAdmin
from apps.events.admin import EventAdmin, EventPriceInline
from apps.events.models import Event
from tests.factories.event import EventFactory
from tests.factories.location import HallFactory
from tests.factories.production import ProductionFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_superuser(username="admin"):
    return User.objects.create_superuser(
        username=username, password="password", email=f"{username}@example.com"
    )

def admin_changelist_url(model):
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")

def admin_change_url(model, pk):
    return reverse(
        f"admin:{model._meta.app_label}_{model._meta.model_name}_change", args=[pk]
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestEventsAdminRegistration(TestCase):
    def test_event_is_registered(self):
        """Event model moet geregistreerd zijn in de admin."""
        self.assertIn(Event, admin.site._registry)

    def test_registered_admin_class_for_event(self):
        """Event admin class moet EventAdmin zijn."""
        self.assertIsInstance(admin.site._registry[Event], EventAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------

class TestEventsAdminInheritance(TestCase):
    admins = [EventAdmin]

    def test_admins_inherit_from_base_admin_if_used(self):
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                self.assertTrue(issubclass(admin_class, BaseAdmin))

    def test_admins_inherit_from_model_admin(self):
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
        admin_obj = EventAdmin(Event, self.site)

        # Ordering / date hierarchy
        self.assertEqual(admin_obj.ordering, ("-starts_at",))
        self.assertEqual(admin_obj.date_hierarchy, "starts_at")

        # list_display
        for field in ["production", "hall", "starts_at", "ends_at"]:
            self.assertIn(field, admin_obj.list_display)

        # autocomplete_fields
        for field in ["production", "hall"]:
            self.assertIn(field, admin_obj.autocomplete_fields)

        # inlines
        self.assertTrue(admin_obj.inlines)
        self.assertIn(EventPriceInline, admin_obj.inlines)

    def test_event_price_inline_configuration(self):
        self.assertEqual(EventPriceInline.extra, 0)
        self.assertIn("price_rank", EventPriceInline.autocomplete_fields)
        self.assertIn("price", EventPriceInline.autocomplete_fields)
        self.assertEqual(EventPriceInline.fields, ("price_rank", "price", "amount", "available"))


# ---------------------------------------------------------------------------
# Queryset optimisation (smoke)
# ---------------------------------------------------------------------------

class TestEventAdminGetQueryset(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prod = ProductionFactory()
        cls.hall = HallFactory()
        now = timezone.now()
        cls.event = EventFactory(
            production=cls.prod,
            hall=cls.hall,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            ticketing_url="https://example.com/tickets",
        )

    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()

    def test_event_admin_queryset_uses_select_related_and_prefetch_related(self):
        admin_obj = EventAdmin(Event, self.site)
        request = self.factory.get("/admin/")
        qs = admin_obj.get_queryset(request)

        # Check select_related fields
        related_fields = ["production", "hall"]
        for field in related_fields:
            self.assertIn(field, qs.query.select_related)

        # Check prefetch_related fields
        prefetch_fields = ["production__translations", "hall__translations"]
        prefetches = set(qs._prefetch_related_lookups)
        for field in prefetch_fields:
            self.assertIn(field, prefetches)


# ---------------------------------------------------------------------------
# Functional admin tests (HTTP)
# ---------------------------------------------------------------------------

class TestEventsAdminChangelists(TestCase):
    def setUp(self):
        self.superuser = make_superuser("events_admin")
        self.client.force_login(self.superuser)

        self.prod = ProductionFactory()
        self.hall = HallFactory()
        now = timezone.now()
        self.event = EventFactory(
            production=self.prod,
            hall=self.hall,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            ticketing_url="https://example.com/tickets",
        )

    def test_event_changelist_returns_200(self):
        url = admin_changelist_url(Event)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_event_changeform_returns_200(self):
        url = admin_change_url(Event, self.event.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)