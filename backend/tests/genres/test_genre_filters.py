"""
Tests for apps/genres/filters.py and apps/genres/views.py.
"""

import pytest
from django.urls import reverse

from apps.genres.filters import GenreFilter, GenreUseAsFilter
from apps.genres.models import Genre, GenreUseAs
from tests.factories.genre import GenreFactory, GenreTranslationFactory, GenreUseAsFactory
from tests.factories.language import LanguageFactory

pytestmark = pytest.mark.django_db


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
        assert self._qs({"vendor_id": "abc"}).count() == 0

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


class TestGenreUseAsViewSet:
    list_url = reverse("genreuseas-list")

    def detail_url(self, pk):
        return reverse("genreuseas-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self, anon_client):
        assert anon_client.get(self.list_url).status_code in (401, 403)

    def test_public_can_list(self, public_client):
        GenreUseAsFactory.create_batch(2)

        assert public_client.get(self.list_url).status_code == 200

    def test_public_cannot_create(self, public_client):
        assert public_client.post(self.list_url, {"name": "tag"}).status_code == 403

    def test_internal_can_create(self, internal_client):
        response = internal_client.post(self.list_url, {"name": "tag"})

        assert response.status_code == 201
        assert GenreUseAs.objects.filter(name="tag").exists()

    def test_internal_can_delete(self, internal_client):
        obj = GenreUseAsFactory()

        assert internal_client.delete(self.detail_url(obj.pk)).status_code == 204

    def test_filter_by_name(self, public_client):
        GenreUseAsFactory(name="genre")
        GenreUseAsFactory(name="tag")

        assert len(public_client.get(self.list_url, {"name": "tag"}).data["results"]) == 1

    def test_ordering_by_name(self, public_client):
        GenreUseAsFactory(name="zzz")
        GenreUseAsFactory(name="aaa")

        response = public_client.get(self.list_url, {"ordering": "name"})
        names = [r["name"] for r in response.data["results"]]

        assert names == sorted(names)

    def test_search_by_name(self, public_client):
        GenreUseAsFactory(name="genre")
        GenreUseAsFactory(name="tag")

        assert len(public_client.get(self.list_url, {"search": "tag"}).data["results"]) == 1


# =====================================================
# GenreViewSet
# =====================================================


class TestGenreViewSet:
    list_url = reverse("genre-list")

    def detail_url(self, pk):
        return reverse("genre-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self, anon_client):
        assert anon_client.get(self.list_url).status_code in (401, 403)

    def test_public_can_list(self, public_client):
        GenreFactory.create_batch(3)

        assert public_client.get(self.list_url).status_code == 200
        assert len(public_client.get(self.list_url).data["results"]) == 3

    def test_public_cannot_delete(self, public_client):
        assert public_client.delete(self.detail_url(GenreFactory().pk)).status_code == 403

    def test_internal_can_create(self, internal_client):
        use_as = GenreUseAsFactory()

        assert internal_client.post(self.list_url, {"type": "theater", "use_as": use_as.pk}).status_code == 201

    def test_filter_by_use_as(self, public_client):
        use_a = GenreUseAsFactory()
        use_b = GenreUseAsFactory()
        GenreFactory(use_as=use_a)
        GenreFactory.create_batch(2, use_as=use_b)

        assert len(public_client.get(self.list_url, {"use_as": use_a.id}).data["results"]) == 1

    def test_filter_by_type(self, public_client):
        GenreFactory(type="theater")
        GenreFactory(type="festival")

        assert len(public_client.get(self.list_url, {"type": "theater"}).data["results"]) == 1

    def test_filter_by_translated_name(self, public_client):
        lang = LanguageFactory(code="en")
        GenreTranslationFactory(genre=GenreFactory(type="theater"), language=lang, name="Theater")
        GenreTranslationFactory(genre=GenreFactory(type="festival"), language=lang, name="Festival")

        assert len(public_client.get(self.list_url, {"name": "Festival"}).data["results"]) == 1

    def test_ordering_by_type(self, public_client):
        GenreFactory(type="zzz")
        GenreFactory(type="aaa")

        response = public_client.get(self.list_url, {"ordering": "type"})
        types = [r["type"] for r in response.data["results"]]

        assert types == sorted(types)

    def test_search_across_type_and_translations(self, public_client):
        lang = LanguageFactory(code="en")
        genre = GenreFactory(type="theater")
        GenreTranslationFactory(genre=genre, language=lang, name="Toneelstuk")

        assert len(public_client.get(self.list_url, {"search": "Toneelstuk"}).data["results"]) == 1
