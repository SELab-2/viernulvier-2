"""
Comprehensive tests for apps/pricing/admin.py

Covers:
- Admin registration for pricing models
- Admin inheritance (BaseAdmin / ModelAdmin) where applicable
- list_display/list_filter/search_fields/ordering basic configuration
- Inline presence (without overly strict assumptions)
- get_queryset optimisation on translation admins (select_related)
- Functional admin changelist + changeform (superuser)
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.pricing.admin import (
    PriceAdmin,
    PriceRankAdmin,
    PriceTranslationAdmin,
    PriceRankTranslationAdmin,
)
from apps.pricing.models import Price, PriceRank, PriceTranslation, PriceRankTranslation
from tests.factories.language import LanguageFactory
from tests.factories.pricing import (
    PriceFactory,
    PriceRankFactory,
    PriceRankTranslationFactory,
    PriceTranslationFactory,
)


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
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_change", args=[pk])


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestPricingAdminRegistration(TestCase):
    def test_price_is_registered(self):
        """Test case for test_price_is_registered."""
        self.assertIn(Price, admin.site._registry)

    def test_price_rank_is_registered(self):
        """Test case for test_price_rank_is_registered."""
        self.assertIn(PriceRank, admin.site._registry)

    def test_price_translation_is_registered(self):
        """Test case for test_price_translation_is_registered."""
        self.assertIn(PriceTranslation, admin.site._registry)

    def test_price_rank_translation_is_registered(self):
        """Test case for test_price_rank_translation_is_registered."""
        self.assertIn(PriceRankTranslation, admin.site._registry)

    def test_registered_admin_classes(self):
        """Test case for test_registered_admin_classes."""
        self.assertIsInstance(admin.site._registry[Price], PriceAdmin)
        self.assertIsInstance(admin.site._registry[PriceRank], PriceRankAdmin)
        self.assertIsInstance(admin.site._registry[PriceTranslation], PriceTranslationAdmin)
        self.assertIsInstance(admin.site._registry[PriceRankTranslation], PriceRankTranslationAdmin)


# ---------------------------------------------------------------------------
# Inheritance (mirrors production admin tests style)
# ---------------------------------------------------------------------------

class TestPricingAdminInheritance(TestCase):
    admins = [PriceAdmin, PriceRankAdmin, PriceTranslationAdmin, PriceRankTranslationAdmin]

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
# Configuration (extends your existing config tests)
# ---------------------------------------------------------------------------

class TestPricingAdminConfiguration(TestCase):
    def setUp(self):
        self.site = AdminSite()

    def test_price_admin_configuration(self):
        """Test case for test_price_admin_configuration."""
        admin_obj = PriceAdmin(Price, self.site)

        self.assertIn("type", admin_obj.list_filter)
        self.assertIn("visibility", admin_obj.list_filter)
        self.assertIn("membership", admin_obj.list_filter)
        self.assertIn("cineville_box", admin_obj.list_filter)

        self.assertIn("id", admin_obj.search_fields)
        self.assertEqual(admin_obj.ordering, ("sort_order", "id"))

        # Inlines should exist (not necessarily strict count)
        self.assertTrue(admin_obj.inlines)

    def test_price_rank_admin_configuration(self):
        """Test case for test_price_rank_admin_configuration."""
        admin_obj = PriceRankAdmin(PriceRank, self.site)

        self.assertEqual(admin_obj.ordering, ("position", "id"))
        self.assertIn("id", admin_obj.search_fields)
        self.assertIn("position", admin_obj.search_fields)
        self.assertTrue(admin_obj.inlines)


# ---------------------------------------------------------------------------
# Queryset optimization (keeps your existing idea, but structured like production)
# ---------------------------------------------------------------------------

class TestPricingTranslationAdminGetQueryset(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lang = LanguageFactory.create(code="en", name="English")

        cls.price = PriceFactory.create(
            type="Standard",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
            cineville_box=False,
        )
        cls.rank = PriceRankFactory.create(position=1, sold_out_buffer=0)

        cls.price_tr = PriceTranslationFactory.create(
            price=cls.price, language=cls.lang, description="Standard ticket"
        )
        cls.rank_tr = PriceRankTranslationFactory.create(
            price_rank=cls.rank, language=cls.lang, description="First rank"
        )

    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()

    def test_price_translation_admin_select_related(self):
        """Test case for test_price_translation_admin_select_related."""
        admin_obj = PriceTranslationAdmin(PriceTranslation, self.site)
        request = self.factory.get("/admin/")
        qs = admin_obj.get_queryset(request)

        with self.assertNumQueries(1):
            obj = qs.get(pk=self.price_tr.pk)
            _ = obj.price.id
            _ = obj.language.code

    def test_price_rank_translation_admin_select_related(self):
        """Test case for test_price_rank_translation_admin_select_related."""
        admin_obj = PriceRankTranslationAdmin(PriceRankTranslation, self.site)
        request = self.factory.get("/admin/")
        qs = admin_obj.get_queryset(request)

        with self.assertNumQueries(1):
            obj = qs.get(pk=self.rank_tr.pk)
            _ = obj.price_rank.id
            _ = obj.language.code


# ---------------------------------------------------------------------------
# Functional admin tests (HTTP)
# ---------------------------------------------------------------------------

class TestPricingAdminChangelists(TestCase):
    def setUp(self):
        self.superuser = make_superuser("pricing_admin")
        self.client.force_login(self.superuser)

        self.lang = LanguageFactory.create(code="nl", name="Dutch")
        self.price = PriceFactory.create(
            type="Student",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=1,
            cineville_box=False,
        )
        self.rank = PriceRankFactory.create(position=1, sold_out_buffer=0)

        self.price_tr = PriceTranslationFactory.create(
            price=self.price, language=self.lang, description="Student ticket"
        )
        self.rank_tr = PriceRankTranslationFactory.create(
            price_rank=self.rank, language=self.lang, description="First rank"
        )

    def test_price_changelist_returns_200(self):
        """Test case for test_price_changelist_returns_200."""
        response = self.client.get(admin_changelist_url(Price))
        self.assertEqual(response.status_code, 200)

    def test_price_changeform_returns_200(self):
        """Test case for test_price_changeform_returns_200."""
        response = self.client.get(admin_change_url(Price, self.price.pk))
        self.assertEqual(response.status_code, 200)

    def test_price_translation_changelist_returns_200(self):
        """Test case for test_price_translation_changelist_returns_200."""
        response = self.client.get(admin_changelist_url(PriceTranslation))
        self.assertEqual(response.status_code, 200)

    def test_price_translation_changeform_returns_200(self):
        """Test case for test_price_translation_changeform_returns_200."""
        response = self.client.get(admin_change_url(PriceTranslation, self.price_tr.pk))
        self.assertEqual(response.status_code, 200)

    def test_price_rank_changelist_returns_200(self):
        """Test case for test_price_rank_changelist_returns_200."""
        response = self.client.get(admin_changelist_url(PriceRank))
        self.assertEqual(response.status_code, 200)

    def test_price_rank_changeform_returns_200(self):
        """Test case for test_price_rank_changeform_returns_200."""
        response = self.client.get(admin_change_url(PriceRank, self.rank.pk))
        self.assertEqual(response.status_code, 200)

    def test_price_rank_translation_changelist_returns_200(self):
        """Test case for test_price_rank_translation_changelist_returns_200."""
        response = self.client.get(admin_changelist_url(PriceRankTranslation))
        self.assertEqual(response.status_code, 200)

    def test_price_rank_translation_changeform_returns_200(self):
        """Test case for test_price_rank_translation_changeform_returns_200."""
        response = self.client.get(admin_change_url(PriceRankTranslation, self.rank_tr.pk))
        self.assertEqual(response.status_code, 200)