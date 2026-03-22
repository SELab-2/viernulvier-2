"""
Tests for apps/productions/filters.py and apps/productions/views.py.
"""

import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

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

PUB_KEY = "pub-production-filter-test-key"
INT_KEY = "int-production-filter-test-key"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


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

    def test_invalid_attendance_mode_returns_one(self):
        ProductionFactory(attendance_mode="offline")

        assert self._qs({"attendance_mode": "hybrid"}).count() == 1

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


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        Production.objects.all().delete()

    def list_url(self):
        return reverse("v1:production-list")

    def detail_url(self, pk):
        return reverse("v1:production-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self):
        response = self.client.get(self.list_url())
        self.assertIn(response.status_code, (401, 403))

    def test_public_can_list(self):
        ProductionFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 3)

    def test_public_can_retrieve(self):
        prod = ProductionFactory()
        response = self.client.get(self.detail_url(prod.pk), **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_public_cannot_delete(self):
        prod = ProductionFactory()
        response = self.client.delete(self.detail_url(prod.pk), **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_internal_can_delete(self):
        prod = ProductionFactory()
        response = self.client.delete(self.detail_url(prod.pk), **int_headers())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Production.objects.filter(pk=prod.pk).exists())

    def test_filter_by_attendance_mode(self):
        ProductionFactory(attendance_mode="offline")
        ProductionFactory(attendance_mode="online")
        response = self.client.get(self.list_url(), {"attendance_mode": "offline"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_genre(self):
        use_as = GenreUseAsFactory()
        genre = GenreFactory(use_as=use_as)
        prod = ProductionFactory()
        ProductionGenreFactory(production=prod, genre=genre, position=1)
        ProductionFactory()
        response = self.client.get(self.list_url(), {"genre": genre.id}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_tag(self):
        tag = TagFactory()
        prod = ProductionFactory()
        ProductionTagFactory(production=prod, tag=tag)
        ProductionFactory()
        response = self.client.get(self.list_url(), {"tag": tag.id}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_has_media(self):
        gallery = MediaGalleryFactory()
        ProductionFactory(media_gallery=gallery)
        ProductionFactory(media_gallery=None)
        response = self.client.get(self.list_url(), {"has_media": "true"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_by_translated_title(self):
        lang = LanguageFactory(code="en")
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTranslationFactory(production=prod_a, language=lang, title="Hamlet")
        ProductionTranslationFactory(production=prod_b, language=lang, title="Macbeth")
        response = self.client.get(self.list_url(), {"title": "Hamlet"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_default_ordering_newest_first(self):
        ProductionFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        ids = [r["id"] for r in response.data.get("results", response.data)]
        self.assertGreater(ids[0], ids[-1])

    def test_ordering_by_attendance_mode(self):
        ProductionFactory(attendance_mode="online")
        ProductionFactory(attendance_mode="offline")
        response = self.client.get(self.list_url(), {"ordering": "attendance_mode"}, **pub_headers())
        modes = [r["attendance_mode"] for r in response.data.get("results", response.data)]
        self.assertEqual(modes, sorted(modes))

    def test_search_by_title_translation(self):
        lang = LanguageFactory(code="en")
        prod = ProductionFactory()
        ProductionTranslationFactory(production=prod, language=lang, title="Hamlet")
        ProductionFactory()
        response = self.client.get(self.list_url(), {"search": "Hamlet"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_search_by_artist_name(self):
        lang = LanguageFactory(code="en")
        prod = ProductionFactory()
        ProductionTranslationFactory(production=prod, language=lang, artist_name="Toneelschuur")
        ProductionFactory()
        response = self.client.get(self.list_url(), {"search": "Toneelschuur"}, **pub_headers())
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
