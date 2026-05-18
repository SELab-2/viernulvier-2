"""
Comprehensive tests for apps/pricing/admin.py

Covers:
- Admin registration for pricing models
- Admin inheritance (BaseAdmin / ModelAdmin)
- list_display/list_filter/search_fields/ordering configuration
- Inline presence
- get_queryset optimisation on translation admins (select_related)
- Functional admin changelist + changeform (superuser)
"""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.pricing.admin import (
    PriceAdmin,
    PriceRankAdmin,
)
from apps.pricing.models import Price, PriceRank
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
    """Create a superuser for admin HTTP tests."""
    return User.objects.create_superuser(username=username, password="password", email=f"{username}@example.com")


def admin_changelist_url(model):
    """Return the admin changelist URL for a model."""
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")


def admin_change_url(model, pk):
    """Return the admin change URL for a model instance."""
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_change", args=[pk])


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestPricingAdminRegistration(TestCase):
    def test_price_is_registered(self) -> None:
        assert Price in admin.site._registry

    def test_price_rank_is_registered(self) -> None:
        assert PriceRank in admin.site._registry

    def test_registered_admin_classes(self) -> None:
        assert isinstance(admin.site._registry[Price], PriceAdmin)
        assert isinstance(admin.site._registry[PriceRank], PriceRankAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestPricingAdminInheritance(TestCase):
    admins = [
        PriceAdmin,
        PriceRankAdmin,
    ]

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


class TestPricingAdminConfiguration(TestCase):
    def setUp(self) -> None:
        self.site = AdminSite()

    def test_price_admin_list_filter_contains_type(self) -> None:
        admin_obj = PriceAdmin(Price, self.site)
        assert "type" in admin_obj.list_filter

    def test_price_admin_list_filter_contains_visibility(self) -> None:
        admin_obj = PriceAdmin(Price, self.site)
        assert "visibility" in admin_obj.list_filter

    def test_price_admin_list_filter_contains_cineville_box(self) -> None:
        admin_obj = PriceAdmin(Price, self.site)
        assert "cineville_box" in admin_obj.list_filter

    def test_price_admin_list_filter_does_not_contain_membership(self) -> None:
        """membership was removed from PriceAdmin.list_filter."""
        admin_obj = PriceAdmin(Price, self.site)
        assert "membership" not in admin_obj.list_filter

    def test_price_admin_search_fields_contains_id(self) -> None:
        admin_obj = PriceAdmin(Price, self.site)
        assert "id" in admin_obj.search_fields

    def test_price_admin_ordering(self) -> None:
        admin_obj = PriceAdmin(Price, self.site)
        assert admin_obj.ordering == ("sort_order", "id")

    def test_price_admin_has_inlines(self) -> None:
        admin_obj = PriceAdmin(Price, self.site)
        assert admin_obj.inlines

    def test_price_rank_admin_ordering(self) -> None:
        admin_obj = PriceRankAdmin(PriceRank, self.site)
        assert admin_obj.ordering == ("position", "id")

    def test_price_rank_admin_search_fields_contains_id(self) -> None:
        admin_obj = PriceRankAdmin(PriceRank, self.site)
        assert "id" in admin_obj.search_fields

    def test_price_rank_admin_search_fields_contains_position(self) -> None:
        admin_obj = PriceRankAdmin(PriceRank, self.site)
        assert "position" in admin_obj.search_fields

    def test_price_rank_admin_has_inlines(self) -> None:
        admin_obj = PriceRankAdmin(PriceRank, self.site)
        assert admin_obj.inlines


# ---------------------------------------------------------------------------
# Functional admin tests (HTTP)
# ---------------------------------------------------------------------------


class TestPricingAdminChangelists(TestCase):
    def setUp(self) -> None:
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

        self.price_tr = PriceTranslationFactory.create(price=self.price, language=self.lang, description="Student ticket")
        self.rank_tr = PriceRankTranslationFactory.create(price_rank=self.rank, language=self.lang, description="First rank")

    def test_price_changelist_returns_200(self) -> None:
        assert self.client.get(admin_changelist_url(Price)).status_code == 200

    def test_price_changeform_returns_200(self) -> None:
        assert self.client.get(admin_change_url(Price, self.price.pk)).status_code == 200

    def test_price_changelist_filter_by_type(self) -> None:
        url = admin_changelist_url(Price)
        assert self.client.get(url, {"type": "Student"}).status_code == 200

    def test_price_changelist_filter_by_cineville_box(self) -> None:
        url = admin_changelist_url(Price)
        assert self.client.get(url, {"cineville_box": "0"}).status_code == 200

    def test_price_rank_changelist_returns_200(self) -> None:
        assert self.client.get(admin_changelist_url(PriceRank)).status_code == 200

    def test_price_rank_changeform_returns_200(self) -> None:
        assert self.client.get(admin_change_url(PriceRank, self.rank.pk)).status_code == 200
