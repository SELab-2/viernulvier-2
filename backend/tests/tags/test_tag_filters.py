"""
Tests for apps/tags/filters.py and apps/tags/views.py.
"""

import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.tags.filters import TagFilter
from apps.tags.models import Tag
from tests.factories.language import LanguageFactory
from tests.factories.tag import TagFactory, TagTranslationFactory

pytestmark = pytest.mark.django_db

PUB_KEY = "pub-tag-filter-test-key"
INT_KEY = "int-tag-filter-test-key"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


# =====================================================
# TagFilter
# =====================================================


class TestTagFilter:
    def _qs(self, params):
        return TagFilter(params, queryset=Tag.objects.all()).qs

    def test_type_icontains(self):
        TagFactory(type="theme")
        TagFactory(type="audience")

        assert self._qs({"type": "theme"}).count() == 1
        assert self._qs({"type": "hem"}).count() == 1

    def test_type_case_insensitive(self):
        TagFactory(type="Theme")

        assert self._qs({"type": "theme"}).count() == 1

    def test_source_icontains(self):
        TagFactory(source="uitdatabank")
        TagFactory(source="system")

        assert self._qs({"source": "uitdatabank"}).count() == 1
        assert self._qs({"source": "data"}).count() == 1

    def test_source_type_icontains(self):
        TagFactory(source_type="targetAudience")
        TagFactory(source_type="theme")

        assert self._qs({"source_type": "target"}).count() == 1

    def test_is_external_true(self):
        TagFactory(is_external=True)
        TagFactory(is_external=False)

        assert self._qs({"is_external": "true"}).count() == 1

    def test_is_external_false(self):
        TagFactory(is_external=True)
        TagFactory(is_external=False)

        assert self._qs({"is_external": "false"}).count() == 1

    def test_is_enabled_true(self):
        TagFactory(is_enabled=True)
        TagFactory(is_enabled=False)

        assert self._qs({"is_enabled": "true"}).count() == 1

    def test_is_enabled_false(self):
        TagFactory(is_enabled=True)
        TagFactory(is_enabled=False)

        assert self._qs({"is_enabled": "false"}).count() == 1

    def test_name_filter_across_translations(self):
        lang = LanguageFactory(code="en")
        tag_a = TagFactory()
        tag_b = TagFactory()
        TagTranslationFactory(tag=tag_a, language=lang, name="Contemporary")
        TagTranslationFactory(tag=tag_b, language=lang, name="Family")

        result = self._qs({"name": "contemporary"})

        assert result.count() == 1
        assert result.first() == tag_a

    def test_name_filter_case_insensitive(self):
        lang = LanguageFactory(code="en")
        tag = TagFactory()
        TagTranslationFactory(tag=tag, language=lang, name="Contemporary")

        assert self._qs({"name": "CONTEMPORARY"}).count() == 1

    def test_name_filter_distinct_no_duplicates(self):
        lang_nl = LanguageFactory(code="nl")
        lang_fr = LanguageFactory(code="fr")
        tag = TagFactory()
        TagTranslationFactory(tag=tag, language=lang_nl, name="Modern")
        TagTranslationFactory(tag=tag, language=lang_fr, name="Moderne")

        assert self._qs({"name": "odern"}).count() == 1

    def test_name_filter_no_match(self):
        lang = LanguageFactory(code="en")
        tag = TagFactory()
        TagTranslationFactory(tag=tag, language=lang, name="Jazz")

        assert self._qs({"name": "classical"}).count() == 0

    def test_external_id_iexact(self):
        TagFactory(external_id="TAG-001")
        TagFactory(external_id="TAG-002")

        assert self._qs({"external_id": "tag-001"}).count() == 1

    def test_is_external_and_source_combined(self):
        TagFactory(is_external=True, source="uitdatabank")
        TagFactory(is_external=True, source="other")
        TagFactory(is_external=False, source="uitdatabank")

        assert self._qs({"is_external": "true", "source": "uitdatabank"}).count() == 1

    def test_type_and_is_enabled_combined(self):
        TagFactory(type="theme", is_enabled=True)
        TagFactory(type="theme", is_enabled=False)
        TagFactory(type="audience", is_enabled=True)

        assert self._qs({"type": "theme", "is_enabled": "true"}).count() == 1

    def test_no_params_returns_all(self):
        TagFactory.create_batch(4)

        assert self._qs({}).count() == 4


# =====================================================
# TagViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestTagViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        Tag.objects.all().delete()

    def list_url(self):
        return reverse("v1:tag-list")

    def detail_url(self, pk):
        return reverse("v1:tag-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        TagFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 3)

    def test_public_can_retrieve(self):
        tag = TagFactory()
        response = self.client.get(self.detail_url(tag.pk), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_public_cannot_delete(self):
        tag = TagFactory()
        response = self.client.delete(self.detail_url(tag.pk), **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_public_cannot_create(self):
        response = self.client.post(self.list_url(), {"type": "theme"}, **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_internal_can_delete(self):
        tag = TagFactory()
        response = self.client.delete(self.detail_url(tag.pk), **int_headers())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())

    def test_filter_by_type(self):
        TagFactory(type="theme")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"type": "theme"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_is_enabled(self):
        TagFactory(is_enabled=True)
        TagFactory(is_enabled=False)
        response = self.client.get(self.list_url(), {"is_enabled": "true"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_is_external(self):
        TagFactory(is_external=True)
        TagFactory(is_external=False)
        response = self.client.get(self.list_url(), {"is_external": "true"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_translated_name(self):
        lang = LanguageFactory(code="en")
        tag_a = TagFactory()
        tag_b = TagFactory()
        TagTranslationFactory(tag=tag_a, language=lang, name="Contemporary")
        TagTranslationFactory(tag=tag_b, language=lang, name="Family")
        response = self.client.get(self.list_url(), {"name": "Contemporary"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_source(self):
        TagFactory(source="uitdatabank")
        TagFactory(source="system")
        response = self.client.get(self.list_url(), {"source": "uitdatabank"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_ordering_by_type_ascending(self):
        TagFactory(type="theme")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"ordering": "type"}, **pub_headers())
        types = [r["type"] for r in response.data.get("results", response.data)]
        self.assertEqual(types, sorted(types))

    def test_ordering_by_type_descending(self):
        TagFactory(type="theme")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"ordering": "-type"}, **pub_headers())
        types = [r["type"] for r in response.data.get("results", response.data)]
        self.assertEqual(types, sorted(types, reverse=True))

    def test_default_ordering_by_id(self):
        TagFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        ids = [r["id"] for r in response.data.get("results", response.data)]
        self.assertEqual(ids, sorted(ids))

    def test_search_by_type(self):
        TagFactory(type="theme")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"search": "theme"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_search_by_source(self):
        TagFactory(source="uitdatabank")
        TagFactory(source="system")
        response = self.client.get(self.list_url(), {"search": "uitdatabank"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_search_by_translated_name(self):
        lang = LanguageFactory(code="en")
        tag = TagFactory(type="theme")
        TagTranslationFactory(tag=tag, language=lang, name="Contemporary")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"search": "Contemporary"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
