"""
Tests for apps/pricing/filters.py and apps/pricing/views.py.
"""

import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.pricing.filters import PriceFilter, PriceRankFilter
from apps.pricing.models import Price, PriceRank
from tests.factories.language import LanguageFactory
from tests.factories.pricing import (
    PriceFactory,
    PriceRankFactory,
    PriceRankTranslationFactory,
    PriceTranslationFactory,
)

pytestmark = pytest.mark.django_db

PUB_KEY = "pub-pricing-filter-test-key"
INT_KEY = "int-pricing-filter-test-key"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


# =====================================================
# PriceFilter
# =====================================================


class TestPriceFilter:
    def _qs(self, params):
        return PriceFilter(params, queryset=Price.objects.all()).qs

    def test_type_icontains(self):
        PriceFactory(type="student")
        PriceFactory(type="full")

        assert self._qs({"type": "student"}).count() == 1
        assert self._qs({"type": "tude"}).count() == 1

    def test_type_case_insensitive(self):
        PriceFactory(type="Student")

        assert self._qs({"type": "student"}).count() == 1

    def test_visibility_exact(self):
        PriceFactory(visibility="public")
        PriceFactory(visibility="members_only")

        assert self._qs({"visibility": "public"}).count() == 1

    def test_membership_icontains(self):
        PriceFactory(membership="cineville")
        PriceFactory(membership="")

        assert self._qs({"membership": "cineville"}).count() == 1
        assert self._qs({"membership": "cine"}).count() == 1

    def test_cineville_box_true(self):
        PriceFactory(cineville_box=True)
        PriceFactory(cineville_box=False)

        assert self._qs({"cineville_box": "true"}).count() == 1

    def test_cineville_box_false(self):
        PriceFactory(cineville_box=True)
        PriceFactory(cineville_box=False)

        assert self._qs({"cineville_box": "false"}).count() == 1

    def test_description_filter_across_translations(self):
        lang = LanguageFactory(code="en")
        price_a = PriceFactory(type="student")
        price_b = PriceFactory(type="full")
        PriceTranslationFactory(price=price_a, language=lang, description="Student price")
        PriceTranslationFactory(price=price_b, language=lang, description="Full price")

        result = self._qs({"description": "student"})

        assert result.count() == 1
        assert result.first() == price_a

    def test_description_filter_distinct_no_duplicates(self):
        lang_nl = LanguageFactory(code="nl")
        lang_fr = LanguageFactory(code="fr")
        price = PriceFactory()
        PriceTranslationFactory(price=price, language=lang_nl, description="Student")
        PriceTranslationFactory(price=price, language=lang_fr, description="Étudiant")

        assert self._qs({"description": "tudiant"}).count() == 1

    def test_external_id_iexact(self):
        PriceFactory(external_id="PRICE-001")
        PriceFactory(external_id="PRICE-002")

        assert self._qs({"external_id": "price-001"}).count() == 1

    def test_combined_type_and_cineville_box(self):
        PriceFactory(type="cineville", cineville_box=True)
        PriceFactory(type="cineville", cineville_box=False)

        assert self._qs({"type": "cineville", "cineville_box": "true"}).count() == 1


# =====================================================
# PriceRankFilter
# =====================================================


class TestPriceRankFilter:
    def _qs(self, params):
        return PriceRankFilter(params, queryset=PriceRank.objects.all()).qs

    def test_position_exact(self):
        PriceRankFactory(position=1)
        PriceRankFactory(position=2)

        assert self._qs({"position": "1"}).count() == 1

    def test_position_gte(self):
        PriceRankFactory(position=1)
        PriceRankFactory(position=3)
        PriceRankFactory(position=5)

        assert self._qs({"position_gte": "3"}).count() == 2

    def test_position_lte(self):
        PriceRankFactory(position=1)
        PriceRankFactory(position=3)
        PriceRankFactory(position=5)

        assert self._qs({"position_lte": "3"}).count() == 2

    def test_position_range(self):
        PriceRankFactory(position=1)
        PriceRankFactory(position=3)
        PriceRankFactory(position=5)

        assert self._qs({"position_gte": "2", "position_lte": "4"}).count() == 1

    def test_description_filter_across_translations(self):
        lang = LanguageFactory(code="en")
        rank_a = PriceRankFactory(position=1)
        rank_b = PriceRankFactory(position=2)
        PriceRankTranslationFactory(price_rank=rank_a, language=lang, description="Standard")
        PriceRankTranslationFactory(price_rank=rank_b, language=lang, description="Premium")

        result = self._qs({"description": "standard"})

        assert result.count() == 1
        assert result.first() == rank_a

    def test_external_id_iexact(self):
        PriceRankFactory(position=1, external_id="RANK-001")
        PriceRankFactory(position=2, external_id="RANK-002")

        assert self._qs({"external_id": "RANK-001"}).count() == 1


# =====================================================
# PriceViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestPriceViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        Price.objects.all().delete()

    def list_url(self):
        return reverse("price-list")

    def detail_url(self, pk):
        return reverse("price-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        PriceFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_public_cannot_delete(self):
        price = PriceFactory()
        response = self.client.delete(self.detail_url(price.pk), **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_internal_can_delete(self):
        price = PriceFactory()
        response = self.client.delete(self.detail_url(price.pk), **int_headers())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Price.objects.filter(pk=price.pk).exists())

    def test_filter_by_type(self):
        PriceFactory(type="student")
        PriceFactory(type="full")
        response = self.client.get(self.list_url(), {"type": "student"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_cineville_box(self):
        PriceFactory(cineville_box=True)
        PriceFactory(cineville_box=False)
        response = self.client.get(self.list_url(), {"cineville_box": "true"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_default_ordering_by_sort_order(self):
        PriceFactory(sort_order=10)
        PriceFactory(sort_order=1)
        response = self.client.get(self.list_url(), **pub_headers())
        orders = [r["sort_order"] for r in response.data.get("results", response.data)]
        self.assertEqual(orders, sorted(orders))

    def test_search_by_type(self):
        PriceFactory(type="student")
        PriceFactory(type="full")
        response = self.client.get(self.list_url(), {"search": "student"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)


# =====================================================
# PriceRankViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestPriceRankViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        PriceRank.objects.all().delete()

    def list_url(self):
        return reverse("price-rank-list")

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        PriceRankFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_filter_by_position(self):
        PriceRankFactory(position=1)
        PriceRankFactory(position=2)
        response = self.client.get(self.list_url(), {"position": "1"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_position_range(self):
        PriceRankFactory(position=1)
        PriceRankFactory(position=3)
        PriceRankFactory(position=5)
        response = self.client.get(self.list_url(), {"position_gte": "2", "position_lte": "4"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_default_ordering_by_position(self):
        PriceRankFactory(position=5)
        PriceRankFactory(position=1)
        response = self.client.get(self.list_url(), **pub_headers())
        positions = [r["position"] for r in response.data.get("results", response.data)]
        self.assertEqual(positions, sorted(positions))

    def test_search_by_translated_description(self):
        lang = LanguageFactory(code="en")
        rank = PriceRankFactory(position=1)
        PriceRankTranslationFactory(price_rank=rank, language=lang, description="Student rank")
        PriceRankFactory(position=2)
        response = self.client.get(self.list_url(), {"search": "Student"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
