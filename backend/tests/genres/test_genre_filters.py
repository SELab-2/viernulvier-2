"""
Tests for apps/genres/filters.py and apps/genres/views.py.
"""

import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.genres.filters import GenreFilter, GenreUseAsFilter
from apps.genres.models import Genre, GenreUseAs
from tests.factories.genre import GenreFactory, GenreTranslationFactory, GenreUseAsFactory
from tests.factories.language import LanguageFactory

pytestmark = pytest.mark.django_db

PUB_KEY = "pub-genre-filter-test-key"
INT_KEY = "int-genre-filter-test-key"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


# =====================================================
# GenreUseAsFilter
# =====================================================


class TestGenreUseAsFilter:
    def _qs(self, params):
        return GenreUseAsFilter(params, queryset=GenreUseAs.objects.all()).qs

    def test_name_icontains(self):
        GenreUseAsFactory(name="genre")
        GenreUseAsFactory(name="tag")

        assert self._qs({"name": "genre"}).count() == 1
        assert self._qs({"name": "enr"}).count() == 1

    def test_name_case_insensitive(self):
        GenreUseAsFactory(name="Genre")

        assert self._qs({"name": "genre"}).count() == 1

    def test_external_id_inherited(self):
        GenreUseAsFactory(external_id="use-001")
        GenreUseAsFactory(external_id="use-002")

        assert self._qs({"external_id": "USE-001"}).count() == 1

    def test_no_params_returns_all(self):
        GenreUseAsFactory.create_batch(3)

        assert self._qs({}).count() == 3


# =====================================================
# GenreFilter
# =====================================================


class TestGenreFilter:
    def _qs(self, params):
        return GenreFilter(params, queryset=Genre.objects.all()).qs

    def test_filter_by_use_as(self):
        use_a = GenreUseAsFactory()
        use_b = GenreUseAsFactory()
        GenreFactory(use_as=use_a)
        GenreFactory(use_as=use_b)

        assert self._qs({"use_as": use_a.id}).count() == 1

    def test_type_icontains(self):
        GenreFactory(type="theater")
        GenreFactory(type="festival")

        assert self._qs({"type": "theater"}).count() == 1
        assert self._qs({"type": "eat"}).count() == 1

    def test_type_case_insensitive(self):
        GenreFactory(type="Theater")

        assert self._qs({"type": "theater"}).count() == 1

    def test_vendor_id_iexact(self):
        GenreFactory(vendor_id="abc-123")
        GenreFactory(vendor_id="def-456")

        assert self._qs({"vendor_id": "ABC-123"}).count() == 1
        assert self._qs({"vendor_id": "abc"}).count() == 1

    def test_name_filter_matches_translation(self):
        lang = LanguageFactory(code="en")
        genre_a = GenreFactory(type="theater")
        genre_b = GenreFactory(type="festival")
        GenreTranslationFactory(genre=genre_a, language=lang, name="Theater")
        GenreTranslationFactory(genre=genre_b, language=lang, name="Festival")

        result = self._qs({"name": "theater"})

        assert result.count() == 1
        assert result.first() == genre_a

    def test_name_filter_distinct_no_duplicates(self):
        genre = GenreFactory()
        GenreTranslationFactory(genre=genre, language=LanguageFactory(code="en"), name="Rock")
        GenreTranslationFactory(genre=genre, language=LanguageFactory(code="nl"), name="Rock")

        assert self._qs({"name": "Rock"}).count() == 1

    def test_name_filter_no_match(self):
        lang = LanguageFactory(code="en")
        GenreTranslationFactory(genre=GenreFactory(), language=lang, name="Jazz")

        assert self._qs({"name": "classical"}).count() == 0

    def test_combined_type_and_use_as(self):
        use_a = GenreUseAsFactory()
        use_b = GenreUseAsFactory()
        GenreFactory(type="theater", use_as=use_a)
        GenreFactory(type="theater", use_as=use_b)

        assert self._qs({"type": "theater", "use_as": use_a.id}).count() == 1


# =====================================================
# GenreUseAsViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestGenreUseAsViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        GenreUseAs.objects.all().delete()

    def list_url(self):
        return reverse("genre-use-as-list")

    def detail_url(self, pk):
        return reverse("genre-use-as-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        GenreUseAsFactory.create_batch(2)
        response = self.client.get(self.list_url(), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_public_cannot_create(self):
        response = self.client.post(self.list_url(), {"name": "tag"}, **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_internal_can_create(self):
        response = self.client.post(self.list_url(), {"name": "tag"}, **int_headers())
        self.assertEqual(response.status_code, 201)
        self.assertTrue(GenreUseAs.objects.filter(name="tag").exists())

    def test_internal_can_delete(self):
        obj = GenreUseAsFactory()
        response = self.client.delete(self.detail_url(obj.pk), **int_headers())
        self.assertEqual(response.status_code, 204)

    def test_filter_by_name(self):
        GenreUseAsFactory(name="genre")
        GenreUseAsFactory(name="tag")
        response = self.client.get(self.list_url(), {"name": "tag"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_ordering_by_name(self):
        GenreUseAsFactory(name="zzz")
        GenreUseAsFactory(name="aaa")
        response = self.client.get(self.list_url(), {"ordering": "name"}, **pub_headers())
        names = [r["name"] for r in response.data.get("results", response.data)]
        self.assertEqual(names, sorted(names))

    def test_search_by_name(self):
        GenreUseAsFactory(name="genre")
        GenreUseAsFactory(name="tag")
        response = self.client.get(self.list_url(), {"search": "tag"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)


# =====================================================
# GenreViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestGenreViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        Genre.objects.all().delete()

    def list_url(self):
        return reverse("genre-list")

    def detail_url(self, pk):
        return reverse("genre-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        GenreFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 3)

    def test_public_cannot_delete(self):
        genre = GenreFactory()
        response = self.client.delete(self.detail_url(genre.pk), **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_internal_can_create(self):
        use_as = GenreUseAsFactory()
        response = self.client.post(self.list_url(), {"type": "theater", "use_as": use_as.pk}, **int_headers())
        self.assertEqual(response.status_code, 201)

    def test_filter_by_use_as(self):
        use_a = GenreUseAsFactory()
        use_b = GenreUseAsFactory()
        GenreFactory(use_as=use_a)
        GenreFactory.create_batch(2, use_as=use_b)
        response = self.client.get(self.list_url(), {"use_as": use_a.id}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_type(self):
        GenreFactory(type="theater")
        GenreFactory(type="festival")
        response = self.client.get(self.list_url(), {"type": "theater"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_translated_name(self):
        lang = LanguageFactory(code="en")
        GenreTranslationFactory(genre=GenreFactory(type="theater"), language=lang, name="Theater")
        GenreTranslationFactory(genre=GenreFactory(type="festival"), language=lang, name="Festival")
        response = self.client.get(self.list_url(), {"name": "Festival"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_ordering_by_type(self):
        GenreFactory(type="zzz")
        GenreFactory(type="aaa")
        response = self.client.get(self.list_url(), {"ordering": "type"}, **pub_headers())
        types = [r["type"] for r in response.data.get("results", response.data)]
        self.assertEqual(types, sorted(types))

    def test_search_across_type_and_translations(self):
        lang = LanguageFactory(code="en")
        genre = GenreFactory(type="theater")
        GenreTranslationFactory(genre=genre, language=lang, name="Toneelstuk")
        response = self.client.get(self.list_url(), {"search": "Toneelstuk"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
