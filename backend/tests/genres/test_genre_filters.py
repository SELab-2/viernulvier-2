"""
Tests for apps/genres/filters.py and apps/genres/views.py.
"""

from django.test import TestCase, override_settings
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.genres.filters import GenreFilter
from apps.genres.models import Genre
from tests.factories.genre import GenreFactory, GenreTranslationFactory
from tests.factories.language import LanguageFactory

pytestmark = pytest.mark.django_db

PUB_KEY = "pub-genre-filter-test-key"
INT_KEY = "int-genre-filter-test-key"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


# =====================================================
# GenreFilter
# =====================================================


class TestGenreFilter:
    def _qs(self, params):
        return GenreFilter(params, queryset=Genre.objects.all()).qs

    def test_type_icontains(self) -> None:
        GenreFactory(type="theater")
        GenreFactory(type="festival")

        assert self._qs({"type": "theater"}).count() == 1
        assert self._qs({"type": "eat"}).count() == 1

    def test_type_case_insensitive(self) -> None:
        GenreFactory(type="Theater")

        assert self._qs({"type": "theater"}).count() == 1

    def test_vendor_id_iexact(self) -> None:
        GenreFactory(vendor_id="abc-123")
        GenreFactory(vendor_id="def-456")

        assert self._qs({"vendor_id": "ABC-123"}).count() == 1
        assert self._qs({"vendor_id": "abc"}).count() == 1

    def test_name_filter_matches_translation(self) -> None:
        lang = LanguageFactory(code="en")
        genre_a = GenreFactory(type="theater")
        genre_b = GenreFactory(type="festival")
        GenreTranslationFactory(genre=genre_a, language=lang, name="Theater")
        GenreTranslationFactory(genre=genre_b, language=lang, name="Festival")

        result = self._qs({"name": "theater"})

        assert result.count() == 1
        assert result.first() == genre_a

    def test_name_filter_distinct_no_duplicates(self) -> None:
        genre = GenreFactory()
        GenreTranslationFactory(genre=genre, language=LanguageFactory(code="en"), name="Rock")
        GenreTranslationFactory(genre=genre, language=LanguageFactory(code="nl"), name="Rock")

        assert self._qs({"name": "Rock"}).count() == 1

    def test_name_filter_no_match(self) -> None:
        lang = LanguageFactory(code="en")
        GenreTranslationFactory(genre=GenreFactory(), language=lang, name="Jazz")

        assert self._qs({"name": "classical"}).count() == 0



# =====================================================
# GenreViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestGenreViewSet(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Genre.objects.all().delete()

    def list_url(self):
        return reverse("v1:genre-list")

    def detail_url(self, pk):
        return reverse("v1:genre-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self) -> None:
        response = self.client.get(self.list_url())
        assert response.status_code in (401, 403)

    def test_public_can_list(self) -> None:
        GenreFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        assert response.status_code == 200
        results = response.data.get("results", response.data)
        assert len(results) == 3

    def test_public_cannot_delete(self) -> None:
        genre = GenreFactory()
        response = self.client.delete(self.detail_url(genre.pk), **pub_headers())
        assert response.status_code == 403

    def test_internal_can_create(self) -> None:
        response = self.client.post(self.list_url(), {"type": "theater"}, **int_headers())
        assert response.status_code == 201

    def test_filter_by_type(self) -> None:
        GenreFactory(type="theater")
        GenreFactory(type="festival")
        response = self.client.get(self.list_url(), {"type": "theater"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_by_translated_name(self) -> None:
        lang = LanguageFactory(code="en")
        GenreTranslationFactory(genre=GenreFactory(type="theater"), language=lang, name="Theater")
        GenreTranslationFactory(genre=GenreFactory(type="festival"), language=lang, name="Festival")
        response = self.client.get(self.list_url(), {"name": "Festival"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_ordering_by_type(self) -> None:
        GenreFactory(type="zzz")
        GenreFactory(type="aaa")
        response = self.client.get(self.list_url(), {"ordering": "type"}, **pub_headers())
        types = [r["type"] for r in response.data.get("results", response.data)]
        assert types == sorted(types)

    def test_search_across_type_and_translations(self) -> None:
        lang = LanguageFactory(code="en")
        genre = GenreFactory(type="theater")
        GenreTranslationFactory(genre=genre, language=lang, name="Toneelstuk")
        response = self.client.get(self.list_url(), {"search": "Toneelstuk"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1
