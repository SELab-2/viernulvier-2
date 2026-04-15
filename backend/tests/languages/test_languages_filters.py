"""
Tests for apps/languages/filters.py and apps/languages/views.py.
"""

import pytest
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.languages.filters import LanguageFilter
from apps.languages.models import Language
from tests.factories.language import LanguageFactory
from tests.helpers.api import (
    internal_headers,
    paginated_results,
    public_headers,
    v1_detail_url,
    v1_list_url,
)

pytestmark = pytest.mark.django_db


# =====================================================
# LanguageFilter
# =====================================================


class TestLanguageFilter:
    def _qs(self, params):
        return LanguageFilter(params, queryset=Language.objects.all()).qs

    # --- code ---

    def test_code_exact_match(self):
        LanguageFactory(code="nl")
        LanguageFactory(code="en")

        assert self._qs({"code": "nl"}).count() == 1
        assert self._qs({"code": "nl"}).first().code == "nl"

    def test_code_is_case_insensitive(self):
        LanguageFactory(code="nl")

        assert self._qs({"code": "NL"}).count() == 1
        assert self._qs({"code": "Nl"}).count() == 1

    def test_code_no_partial_match(self):
        LanguageFactory(code="nl")

        assert self._qs({"code": "n"}).count() == 0

    # --- name ---

    def test_name_icontains(self):
        LanguageFactory(code="nl", name="Dutch")
        LanguageFactory(code="en", name="English")

        assert self._qs({"name": "dutch"}).count() == 1
        assert self._qs({"name": "ngl"}).count() == 1

    def test_name_no_match(self):
        LanguageFactory(code="nl", name="Dutch")

        assert self._qs({"name": "French"}).count() == 0

    # --- is_active ---

    def test_is_active_true(self):
        LanguageFactory(code="nl", is_active=True)
        LanguageFactory(code="en", is_active=False)

        result = self._qs({"is_active": "true"})

        assert result.count() == 1
        assert result.first().code == "nl"

    def test_is_active_false(self):
        LanguageFactory(code="nl", is_active=True)
        LanguageFactory(code="en", is_active=False)

        assert self._qs({"is_active": "false"}).count() == 1

    # --- external_id ---

    def test_external_id_iexact(self):
        LanguageFactory(code="nl", external_id="ext-001")
        LanguageFactory(code="en", external_id="ext-002")

        assert self._qs({"external_id": "EXT-001"}).count() == 1

    # --- combined ---

    def test_multiple_filters_are_anded(self):
        LanguageFactory(code="nl", name="Dutch", is_active=True)
        LanguageFactory(code="de", name="German", is_active=False)

        result = self._qs({"name": "erman", "is_active": "false"})

        assert result.count() == 1
        assert result.first().code == "de"

    def test_no_filters_returns_all(self):
        LanguageFactory.create_batch(3)

        assert self._qs({}).count() == 3


# =====================================================
# LanguageViewSet
# =====================================================

PUB_KEY = "pub-filter-test-key"
INT_KEY = "int-filter-test-key"


def int_headers():
    return internal_headers(INT_KEY)


def pub_headers():
    return public_headers(PUB_KEY)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestLanguageViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()

    def detail_url(self, code):
        return v1_detail_url("language", code=code)

    list_url = v1_list_url("language")

    def test_anon_returns_401_or_403(self):
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        LanguageFactory.create_batch(2)
        response = self.client.get(self.list_url, **pub_headers())
        self.assertEqual(response.status_code, 200)
        results = paginated_results(response)
        self.assertEqual(len(results), 2)

    def test_public_can_retrieve(self):
        LanguageFactory(code="nl")
        response = self.client.get(self.detail_url("nl"), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_public_cannot_create(self):
        response = self.client.post(self.list_url, {"code": "de", "name": "German"}, format="json", **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_public_cannot_update(self):
        LanguageFactory(code="nl")
        response = self.client.patch(self.detail_url("nl"), {"name": "Nederlands"}, format="json", **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_public_cannot_delete(self):
        LanguageFactory(code="nl")
        response = self.client.delete(self.detail_url("nl"), **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_internal_can_create(self):
        response = self.client.post(
            self.list_url, {"code": "de", "name": "German", "is_active": False}, format="json", **int_headers()
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Language.objects.filter(code="de").exists())

    def test_internal_can_delete(self):
        LanguageFactory(code="nl")
        response = self.client.delete(self.detail_url("nl"), **int_headers())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Language.objects.filter(code="nl").exists())

    def test_filter_by_code(self):
        LanguageFactory(code="nl")
        LanguageFactory(code="en")
        response = self.client.get(self.list_url, {"code": "nl"}, **pub_headers())
        results = paginated_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["code"], "nl")

    def test_filter_by_is_active(self):
        LanguageFactory(code="nl", is_active=True)
        LanguageFactory(code="en", is_active=False)
        response = self.client.get(self.list_url, {"is_active": "true"}, **pub_headers())
        results = paginated_results(response)
        self.assertEqual(len(results), 1)

    def test_ordering_by_name_ascending(self):
        LanguageFactory(code="nl", name="Dutch")
        LanguageFactory(code="en", name="English")
        LanguageFactory(code="fr", name="French")
        response = self.client.get(self.list_url, {"ordering": "name"}, **pub_headers())
        names = [r["name"] for r in paginated_results(response)]
        self.assertEqual(names, sorted(names))

    def test_ordering_by_name_descending(self):
        LanguageFactory(code="nl", name="Dutch")
        LanguageFactory(code="en", name="English")
        response = self.client.get(self.list_url, {"ordering": "-name"}, **pub_headers())
        names = [r["name"] for r in paginated_results(response)]
        self.assertEqual(names, sorted(names, reverse=True))

    def test_search_by_code(self):
        LanguageFactory(code="nl", name="Dutch")
        LanguageFactory(code="en", name="English")
        response = self.client.get(self.list_url, {"search": "nl"}, **pub_headers())
        results = paginated_results(response)
        self.assertEqual(len(results), 1)

    def test_search_by_name(self):
        LanguageFactory(code="nl", name="Dutch")
        LanguageFactory(code="en", name="English")
        response = self.client.get(self.list_url, {"search": "English"}, **pub_headers())
        results = paginated_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["code"], "en")

    def test_lookup_by_code_not_pk(self):
        LanguageFactory(code="nl")
        response = self.client.get(self.detail_url("nl"), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_unknown_code_returns_404(self):
        response = self.client.get(self.detail_url("xx"), **pub_headers())
        self.assertEqual(response.status_code, 404)
