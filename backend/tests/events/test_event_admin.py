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
from tests.factories.event import EventFactory
from tests.factories.language import LanguageFactory
from tests.factories.location import HallFactory
from tests.factories.production import ProductionFactory, ProductionTranslationFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_superuser(username="admin"):
    return User.objects.create_superuser(username=username, password="password", email=f"{username}@example.com")


def admin_changelist_url(model):
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")


def admin_change_url(model, pk):
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_change", args=[pk])


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestEventsAdminRegistration(TestCase):
    def test_event_is_registered(self) -> None:
        """Event model has to be registered in admin."""
        assert Event in admin.site._registry

    def test_registered_admin_class_for_event(self) -> None:
        """Event admin class has to be of type EventAdmin."""
        assert isinstance(admin.site._registry[Event], EventAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestEventsAdminInheritance(TestCase):
    admins = [EventAdmin]

    def test_admins_inherit_from_base_admin_if_used(self) -> None:
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                assert issubclass(admin_class, BaseAdmin)

    def test_admins_inherit_from_model_admin(self) -> None:
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                assert issubclass(admin_class, admin.ModelAdmin)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class TestEventsAdminConfiguration(TestCase):
    def setUp(self) -> None:
        self.site = AdminSite()

    def test_event_admin_configuration(self) -> None:
        admin_obj = EventAdmin(Event, self.site)

        # Ordering / date hierarchy
        assert admin_obj.ordering == ("-starts_at",)
        assert admin_obj.date_hierarchy == "starts_at"

        # list_display
        for field in ["production", "hall", "starts_at", "ends_at"]:
            assert field in admin_obj.list_display

        assert "production" in admin_obj.autocomplete_fields
        assert "hall" in admin_obj.autocomplete_fields
        assert "production_admin_link" in admin_obj.readonly_fields

        # inlines
        assert admin_obj.inlines
        assert EventPriceInline in admin_obj.inlines

    def test_event_price_inline_configuration(self) -> None:
        assert EventPriceInline.extra == 0
        assert "price_rank" in EventPriceInline.autocomplete_fields
        assert "price" in EventPriceInline.autocomplete_fields
        assert EventPriceInline.fields == ("price_rank", "price", "amount", "available")

    def test_production_admin_link_returns_dash_without_object(self) -> None:
        admin_obj = EventAdmin(Event, self.site)

        assert admin_obj.production_admin_link(None) == "-"


# ---------------------------------------------------------------------------
# Queryset optimisation (smoke)
# ---------------------------------------------------------------------------


class TestEventAdminGetQueryset(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.prod = ProductionFactory()
        cls.hall = HallFactory()
        now = timezone.now()
        cls.event = EventFactory(
            production=cls.prod,
            hall=cls.hall,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
        )

    def setUp(self) -> None:
        self.site = AdminSite()
        self.factory = RequestFactory()

    def test_event_admin_queryset_uses_select_related_and_prefetch_related(self) -> None:
        admin_obj = EventAdmin(Event, self.site)
        request = self.factory.get("/admin/")
        qs = admin_obj.get_queryset(request)

        # Check select_related fields
        related_fields = ["production", "hall"]
        for field in related_fields:
            assert field in qs.query.select_related

        # Check prefetch_related fields
        prefetch_fields = ["production__translations", "hall__translations"]
        prefetches = set(qs._prefetch_related_lookups)
        for field in prefetch_fields:
            assert field in prefetches


# ---------------------------------------------------------------------------
# Functional admin tests (HTTP)
# ---------------------------------------------------------------------------


class TestEventsAdminChangelists(TestCase):
    def setUp(self) -> None:
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
        )

    def test_event_changelist_returns_200(self) -> None:
        url = admin_changelist_url(Event)
        response = self.client.get(url)
        assert response.status_code == 200

    def test_event_changeform_returns_200(self) -> None:
        """Event change form should load for superusers."""
        response = self.client.get(admin_change_url(Event, self.event.pk))
        assert response.status_code == 200

    def test_event_changeform_shows_production_admin_link(self) -> None:
        response = self.client.get(admin_change_url(Event, self.event.pk))
        production_admin_url = reverse("admin:productions_production_change", args=[self.prod.pk])

        self.assertContains(response, production_admin_url)

        # Link text can vary (e.g. "<production> by <artist>") depending on
        # available base translation data, but the target URL must always exist.
        self.assertContains(response, "Production details")

    def test_event_changeform_shows_artist_name_in_production_link(self) -> None:
        language = LanguageFactory(code="nl", name="Dutch")
        ProductionTranslationFactory(
            production=self.prod,
            language=language,
            title="Event Titel",
            artist_name="Artiest Naam",
        )

        response = self.client.get(admin_change_url(Event, self.event.pk))
        self.assertContains(response, "by Artiest Naam")
