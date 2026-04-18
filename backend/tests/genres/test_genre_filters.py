"""
Tests for apps/genres/filters.py and apps/genres/views.py.
"""

from django.test import override_settings
import pytest

from apps.genres.filters import GenreFilter
from apps.genres.models import Genre
from tests.factories.genre import GenreFactory, GenreTranslationFactory
from tests.factories.language import LanguageFactory
from tests.helpers.api import INTERNAL_API_KEY, PUBLIC_API_KEY, BaseViewSetTestCase, paginated_results

pytestmark = pytest.mark.django_db


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


@override_settings(PUBLIC_API_KEY=PUBLIC_API_KEY, INTERNAL_API_KEY=INTERNAL_API_KEY)
class TestGenreViewSet(BaseViewSetTestCase):
    resource_name = "genre"

    def setUp(self) -> None:
        super().setUp()
        Genre.objects.all().delete()

    def test_anon_is_rejected(self) -> None:
        response = self.client.get(self.list_url())
        assert response.status_code in (401, 403)

    def test_public_can_list(self) -> None:
        GenreFactory.create_batch(3)
        response = self.client.get(self.list_url(), **self.pub_headers())
        assert response.status_code == 200
        results = paginated_results(response)
        assert len(results) == 3

    def test_public_cannot_delete(self) -> None:
        genre = GenreFactory()
        response = self.client.delete(self.detail_url(pk=genre.pk), **self.pub_headers())
        assert response.status_code == 403

    def test_internal_can_create(self) -> None:
        response = self.client.post(self.list_url(), {"type": "theater"}, **self.int_headers())
        assert response.status_code == 201

    def test_filter_by_type(self) -> None:
        GenreFactory(type="theater")
        GenreFactory(type="festival")
        response = self.client.get(self.list_url(), {"type": "theater"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_filter_by_translated_name(self) -> None:
        lang = LanguageFactory(code="en")
        GenreTranslationFactory(genre=GenreFactory(type="theater"), language=lang, name="Theater")
        GenreTranslationFactory(genre=GenreFactory(type="festival"), language=lang, name="Festival")
        response = self.client.get(self.list_url(), {"name": "Festival"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_ordering_by_type(self) -> None:
        GenreFactory(type="zzz")
        GenreFactory(type="aaa")
        response = self.client.get(self.list_url(), {"ordering": "type"}, **self.pub_headers())
        types = [r["type"] for r in paginated_results(response)]
        assert types == sorted(types)

    def test_search_across_type_and_translations(self) -> None:
        lang = LanguageFactory(code="en")
        genre = GenreFactory(type="theater")
        GenreTranslationFactory(genre=genre, language=lang, name="Toneelstuk")
        response = self.client.get(self.list_url(), {"search": "Toneelstuk"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1
