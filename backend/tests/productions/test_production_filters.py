"""
Tests for apps/productions/filters.py and apps/productions/views.py.
"""

import pytest
from django.urls import reverse

from apps.productions.filters import ProductionFilter
from apps.productions.models import Production
from tests.factories.genre import GenreFactory, GenreUseAsFactory
from tests.factories.language import LanguageFactory
from tests.factories.media_library import MediaGalleryFactory
from tests.factories.production import (
    ProductionFactory,
    ProductionGenreFactory,
    ProductionTagFactory,
    ProductionTranslationFactory,
    UitDatabaseThemeFactory,
    UitDatabaseTypeFactory,
)
from tests.factories.tag import TagFactory

pytestmark = pytest.mark.django_db


# =====================================================
# ProductionFilter
# =====================================================


class TestProductionFilter:
    def _qs(self, params):
        return ProductionFilter(params, queryset=Production.objects.all()).qs

    def test_filter_by_attendance_mode(self):
        ProductionFactory(attendance_mode="offline")
        ProductionFactory(attendance_mode="online")

        assert self._qs({"attendance_mode": "offline"}).count() == 1

    def test_invalid_attendance_mode_returns_empty(self):
        ProductionFactory(attendance_mode="offline")

        assert self._qs({"attendance_mode": "hybrid"}).count() == 0

    def test_filter_by_performer_type(self):
        ProductionFactory(performer_type="solo")
        ProductionFactory(performer_type="group")

        assert self._qs({"performer_type": "solo"}).count() == 1

    def test_filter_by_uit_database_theme(self):
        theme_a = UitDatabaseThemeFactory()
        theme_b = UitDatabaseThemeFactory()
        ProductionFactory(uit_database_theme=theme_a)
        ProductionFactory(uit_database_theme=theme_b)

        assert self._qs({"uit_database_theme": theme_a.id}).count() == 1

    def test_filter_by_uit_database_type(self):
        type_a = UitDatabaseTypeFactory()
        type_b = UitDatabaseTypeFactory()
        ProductionFactory(uit_database_type=type_a)
        ProductionFactory(uit_database_type=type_b)

        assert self._qs({"uit_database_type": type_a.id}).count() == 1

    def test_filter_by_genre(self):
        use_as = GenreUseAsFactory()
        genre_a = GenreFactory(use_as=use_as)
        genre_b = GenreFactory(use_as=use_as)
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionGenreFactory(production=prod_a, genre=genre_a, position=1)
        ProductionGenreFactory(production=prod_b, genre=genre_b, position=1)

        result = self._qs({"genre": genre_a.id})

        assert result.count() == 1
        assert result.first() == prod_a

    def test_filter_by_genre_distinct_no_duplicates(self):
        use_as = GenreUseAsFactory()
        genre_a = GenreFactory(use_as=use_as)
        genre_b = GenreFactory(use_as=use_as)
        prod = ProductionFactory()
        ProductionGenreFactory(production=prod, genre=genre_a, position=1)
        ProductionGenreFactory(production=prod, genre=genre_b, position=2)

        assert self._qs({"genre": genre_a.id}).count() == 1

    def test_filter_by_tag(self):
        tag_a = TagFactory()
        tag_b = TagFactory()
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTagFactory(production=prod_a, tag=tag_a)
        ProductionTagFactory(production=prod_b, tag=tag_b)

        result = self._qs({"tag": tag_a.id})

        assert result.count() == 1

    def test_has_media_true(self):
        gallery = MediaGalleryFactory()
        ProductionFactory(media_gallery=gallery)
        ProductionFactory(media_gallery=None)

        assert self._qs({"has_media": "true"}).count() == 1

    def test_has_media_false(self):
        gallery = MediaGalleryFactory()
        ProductionFactory(media_gallery=gallery)
        ProductionFactory(media_gallery=None)

        assert self._qs({"has_media": "false"}).count() == 1

    def test_title_filter_across_translations(self):
        lang = LanguageFactory(code="en")
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTranslationFactory(production=prod_a, language=lang, title="Hamlet")
        ProductionTranslationFactory(production=prod_b, language=lang, title="Macbeth")

        result = self._qs({"title": "hamlet"})

        assert result.count() == 1
        assert result.first() == prod_a

    def test_title_filter_distinct_no_duplicates(self):
        lang_nl = LanguageFactory(code="nl")
        lang_fr = LanguageFactory(code="fr")
        prod = ProductionFactory()
        ProductionTranslationFactory(production=prod, language=lang_nl, title="Hamlet")
        ProductionTranslationFactory(production=prod, language=lang_fr, title="Hamlet")

        assert self._qs({"title": "Hamlet"}).count() == 1

    def test_artist_name_filter(self):
        lang = LanguageFactory(code="en")
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTranslationFactory(production=prod_a, language=lang, artist_name="Toneelschuur")
        ProductionTranslationFactory(production=prod_b, language=lang, artist_name="NTGent")

        assert self._qs({"artist_name": "toneelschuur"}).count() == 1

    def test_attendance_mode_and_has_media_combined(self):
        gallery = MediaGalleryFactory()
        ProductionFactory(attendance_mode="offline", media_gallery=gallery)
        ProductionFactory(attendance_mode="offline", media_gallery=None)
        ProductionFactory(attendance_mode="online", media_gallery=gallery)

        assert self._qs({"attendance_mode": "offline", "has_media": "true"}).count() == 1

    def test_external_id_inherited(self):
        ProductionFactory(external_id="PROD-001")
        ProductionFactory(external_id="PROD-002")

        assert self._qs({"external_id": "PROD-001"}).count() == 1

    def test_no_params_returns_all(self):
        ProductionFactory.create_batch(4)

        assert self._qs({}).count() == 4


# =====================================================
# ProductionViewSet
# =====================================================


class TestProductionViewSet:
    list_url = reverse("production-list")

    def detail_url(self, pk):
        return reverse("production-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self, anon_client):
        assert anon_client.get(self.list_url).status_code in (401, 403)

    def test_public_can_list(self, public_client):
        ProductionFactory.create_batch(3)

        response = public_client.get(self.list_url)

        assert response.status_code == 200
        assert len(response.data["results"]) == 3

    def test_public_can_retrieve(self, public_client):
        prod = ProductionFactory()

        assert public_client.get(self.detail_url(prod.pk)).status_code == 200

    def test_public_cannot_delete(self, public_client):
        assert public_client.delete(self.detail_url(ProductionFactory().pk)).status_code == 403

    def test_internal_can_delete(self, internal_client):
        prod = ProductionFactory()

        assert internal_client.delete(self.detail_url(prod.pk)).status_code == 204
        assert not Production.objects.filter(pk=prod.pk).exists()

    def test_filter_by_attendance_mode(self, public_client):
        ProductionFactory(attendance_mode="offline")
        ProductionFactory(attendance_mode="online")

        assert len(public_client.get(self.list_url, {"attendance_mode": "offline"}).data["results"]) == 1

    def test_filter_by_genre(self, public_client):
        use_as = GenreUseAsFactory()
        genre = GenreFactory(use_as=use_as)
        prod = ProductionFactory()
        ProductionGenreFactory(production=prod, genre=genre, position=1)
        ProductionFactory()

        assert len(public_client.get(self.list_url, {"genre": genre.id}).data["results"]) == 1

    def test_filter_by_tag(self, public_client):
        tag = TagFactory()
        prod = ProductionFactory()
        ProductionTagFactory(production=prod, tag=tag)
        ProductionFactory()

        assert len(public_client.get(self.list_url, {"tag": tag.id}).data["results"]) == 1

    def test_filter_has_media(self, public_client):
        gallery = MediaGalleryFactory()
        ProductionFactory(media_gallery=gallery)
        ProductionFactory(media_gallery=None)

        assert len(public_client.get(self.list_url, {"has_media": "true"}).data["results"]) == 1

    def test_filter_by_translated_title(self, public_client):
        lang = LanguageFactory(code="en")
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTranslationFactory(production=prod_a, language=lang, title="Hamlet")
        ProductionTranslationFactory(production=prod_b, language=lang, title="Macbeth")

        assert len(public_client.get(self.list_url, {"title": "Hamlet"}).data["results"]) == 1

    def test_default_ordering_newest_first(self, public_client):
        ProductionFactory.create_batch(3)

        response = public_client.get(self.list_url)
        ids = [r["id"] for r in response.data["results"]]

        assert ids[0] > ids[-1]

    def test_ordering_by_attendance_mode(self, public_client):
        ProductionFactory(attendance_mode="online")
        ProductionFactory(attendance_mode="offline")

        response = public_client.get(self.list_url, {"ordering": "attendance_mode"})
        modes = [r["attendance_mode"] for r in response.data["results"]]

        assert modes == sorted(modes)

    def test_search_by_title_translation(self, public_client):
        lang = LanguageFactory(code="en")
        prod = ProductionFactory()
        ProductionTranslationFactory(production=prod, language=lang, title="Hamlet")
        ProductionFactory()

        assert len(public_client.get(self.list_url, {"search": "Hamlet"}).data["results"]) == 1

    def test_search_by_artist_name(self, public_client):
        lang = LanguageFactory(code="en")
        prod = ProductionFactory()
        ProductionTranslationFactory(production=prod, language=lang, artist_name="Toneelschuur")
        ProductionFactory()

        assert len(public_client.get(self.list_url, {"search": "Toneelschuur"}).data["results"]) == 1
