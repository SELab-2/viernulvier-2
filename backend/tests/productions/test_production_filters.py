"""
Tests for apps/productions/filters.py and apps/productions/views.py.
"""

from datetime import UTC, datetime

from django.http import QueryDict
from django.test import TestCase, override_settings
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.productions.filters import ProductionFilter
from apps.productions.models import Production
from tests.factories.event import EventFactory
from tests.factories.genre import GenreFactory
from tests.factories.language import LanguageFactory
from tests.factories.media_library import MediaGalleryFactory
from tests.factories.production import (
    ProductionFactory,
    ProductionGenreFactory,
    ProductionTagFactory,
    ProductionTranslationFactory,
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

    def test_filter_by_attendance_mode(self) -> None:
        ProductionFactory(attendance_mode="offline")
        ProductionFactory(attendance_mode="online")

        assert self._qs({"attendance_mode": "offline"}).count() == 1

    def test_invalid_attendance_mode_returns_one(self) -> None:
        ProductionFactory(attendance_mode="offline")

        assert self._qs({"attendance_mode": "hybrid"}).count() == 1

    def test_filter_by_performer_type(self) -> None:
        ProductionFactory(performer_type="solo")
        ProductionFactory(performer_type="group")

        assert self._qs({"performer_type": "solo"}).count() == 1

    def test_filter_by_uit_database_type(self) -> None:
        type_a = UitDatabaseTypeFactory()
        type_b = UitDatabaseTypeFactory()
        ProductionFactory(uit_database_type=type_a)
        ProductionFactory(uit_database_type=type_b)

        assert self._qs({"uit_database_type": type_a.id}).count() == 1

    def test_filter_by_genre(self) -> None:
        genre_a = GenreFactory()
        genre_b = GenreFactory()
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionGenreFactory(production=prod_a, genre=genre_a, position=1)
        ProductionGenreFactory(production=prod_b, genre=genre_b, position=1)

        result = self._qs({"genre": genre_a.id})

        assert result.count() == 1
        assert result.first() == prod_a

    def test_filter_by_genre_distinct_no_duplicates(self) -> None:
        genre_a = GenreFactory()
        genre_b = GenreFactory()
        prod = ProductionFactory()
        ProductionGenreFactory(production=prod, genre=genre_a, position=1)
        ProductionGenreFactory(production=prod, genre=genre_b, position=2)

        assert self._qs({"genre": genre_a.id}).count() == 1

    def test_filter_by_tag(self) -> None:
        tag_a = TagFactory()
        tag_b = TagFactory()
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTagFactory(production=prod_a, tag=tag_a)
        ProductionTagFactory(production=prod_b, tag=tag_b)

        result = self._qs({"tag": tag_a.id})

        assert result.count() == 1

    def test_filter_by_multiple_genres_uses_and_semantics(self) -> None:
        genre_a = GenreFactory()
        genre_b = GenreFactory()
        prod_both = ProductionFactory()
        prod_only_a = ProductionFactory()
        prod_only_b = ProductionFactory()

        ProductionGenreFactory(production=prod_both, genre=genre_a, position=1)
        ProductionGenreFactory(production=prod_both, genre=genre_b, position=2)
        ProductionGenreFactory(production=prod_only_a, genre=genre_a, position=1)
        ProductionGenreFactory(production=prod_only_b, genre=genre_b, position=1)

        params = QueryDict("", mutable=True)
        params.setlist("genre", [str(genre_a.id), str(genre_b.id)])

        result = self._qs(params)

        assert list(result) == [prod_both]

    def test_filter_by_multiple_tags_uses_and_semantics(self) -> None:
        tag_a = TagFactory()
        tag_b = TagFactory()
        prod_both = ProductionFactory()
        prod_only_a = ProductionFactory()
        prod_only_b = ProductionFactory()

        ProductionTagFactory(production=prod_both, tag=tag_a)
        ProductionTagFactory(production=prod_both, tag=tag_b)
        ProductionTagFactory(production=prod_only_a, tag=tag_a)
        ProductionTagFactory(production=prod_only_b, tag=tag_b)

        params = QueryDict("", mutable=True)
        params.setlist("tag", [str(tag_a.id), str(tag_b.id)])

        result = self._qs(params)

        assert list(result) == [prod_both]

    def test_filter_by_comma_separated_genres_uses_and_semantics(self) -> None:
        genre_a = GenreFactory()
        genre_b = GenreFactory()
        prod_both = ProductionFactory()
        prod_only_a = ProductionFactory()

        ProductionGenreFactory(production=prod_both, genre=genre_a, position=1)
        ProductionGenreFactory(production=prod_both, genre=genre_b, position=2)
        ProductionGenreFactory(production=prod_only_a, genre=genre_a, position=1)

        result = self._qs({"genre": f"{genre_a.id},{genre_b.id}"})

        assert list(result) == [prod_both]

    def test_filter_by_genre_ignores_empty_and_invalid_parts(self) -> None:
        genre = GenreFactory()
        prod = ProductionFactory()
        ProductionGenreFactory(production=prod, genre=genre, position=1)
        ProductionFactory()

        result = self._qs({"genre": f" ,abc,{genre.id}"})

        assert list(result) == [prod]

    def test_filter_by_genre_with_only_invalid_values_returns_unfiltered(self) -> None:
        ProductionFactory.create_batch(3)

        result = self._qs({"genre": " ,abc, "})

        assert result.count() == 3

    def test_filter_by_tag_with_only_invalid_values_returns_unfiltered(self) -> None:
        ProductionFactory.create_batch(2)

        result = self._qs({"tag": " ,abc, "})

        assert result.count() == 2

    def test_has_media_true(self) -> None:
        gallery = MediaGalleryFactory()
        ProductionFactory(media_gallery=gallery)
        ProductionFactory(media_gallery=None)

        assert self._qs({"has_media": "true"}).count() == 1

    def test_has_media_false(self) -> None:
        gallery = MediaGalleryFactory()
        ProductionFactory(media_gallery=gallery)
        ProductionFactory(media_gallery=None)

        assert self._qs({"has_media": "false"}).count() == 1

    def test_title_filter_across_translations(self) -> None:
        lang = LanguageFactory(code="en")
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTranslationFactory(production=prod_a, language=lang, title="Hamlet")
        ProductionTranslationFactory(production=prod_b, language=lang, title="Macbeth")

        result = self._qs({"title": "hamlet"})

        assert result.count() == 1
        assert result.first() == prod_a

    def test_title_filter_distinct_no_duplicates(self) -> None:
        lang_nl = LanguageFactory(code="nl")
        lang_fr = LanguageFactory(code="fr")
        prod = ProductionFactory()
        ProductionTranslationFactory(production=prod, language=lang_nl, title="Hamlet")
        ProductionTranslationFactory(production=prod, language=lang_fr, title="Hamlet")

        assert self._qs({"title": "Hamlet"}).count() == 1

    def test_artist_name_filter(self) -> None:
        lang = LanguageFactory(code="en")
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTranslationFactory(production=prod_a, language=lang, artist_name="Toneelschuur")
        ProductionTranslationFactory(production=prod_b, language=lang, artist_name="NTGent")

        assert self._qs({"artist_name": "toneelschuur"}).count() == 1

    def test_attendance_mode_and_has_media_combined(self) -> None:
        gallery = MediaGalleryFactory()
        ProductionFactory(attendance_mode="offline", media_gallery=gallery)
        ProductionFactory(attendance_mode="offline", media_gallery=None)
        ProductionFactory(attendance_mode="online", media_gallery=gallery)

        assert self._qs({"attendance_mode": "offline", "has_media": "true"}).count() == 1

    def test_external_id_inherited(self) -> None:
        ProductionFactory(external_id="PROD-001")
        ProductionFactory(external_id="PROD-002")

        assert self._qs({"external_id": "PROD-001"}).count() == 1

    def test_no_params_returns_all(self) -> None:
        ProductionFactory.create_batch(4)

        assert self._qs({}).count() == 4


# =====================================================
# ProductionViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSet(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Production.objects.all().delete()

    def list_url(self):
        return reverse("v1:production-list")

    def detail_url(self, pk):
        return reverse("v1:production-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self) -> None:
        response = self.client.get(self.list_url())
        assert response.status_code in (401, 403)

    def test_public_can_list(self) -> None:
        ProductionFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        assert response.status_code == 200
        results = response.data.get("results", response.data)
        assert len(results) == 3

    def test_public_can_retrieve(self) -> None:
        prod = ProductionFactory()
        response = self.client.get(self.detail_url(prod.pk), **pub_headers())
        assert response.status_code == 200

    def test_public_cannot_delete(self) -> None:
        prod = ProductionFactory()
        response = self.client.delete(self.detail_url(prod.pk), **pub_headers())
        assert response.status_code == 403

    def test_internal_can_delete(self) -> None:
        prod = ProductionFactory()
        response = self.client.delete(self.detail_url(prod.pk), **int_headers())
        assert response.status_code == 204
        assert not Production.objects.filter(pk=prod.pk).exists()

    def test_filter_by_attendance_mode(self) -> None:
        ProductionFactory(attendance_mode="offline")
        ProductionFactory(attendance_mode="online")
        response = self.client.get(self.list_url(), {"attendance_mode": "offline"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_by_genre(self) -> None:
        genre = GenreFactory()
        prod = ProductionFactory()
        ProductionGenreFactory(production=prod, genre=genre, position=1)
        ProductionFactory()
        response = self.client.get(self.list_url(), {"genre": genre.id}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_by_tag(self) -> None:
        tag = TagFactory()
        prod = ProductionFactory()
        ProductionTagFactory(production=prod, tag=tag)
        ProductionFactory()
        response = self.client.get(self.list_url(), {"tag": tag.id}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_by_multiple_genres_uses_and_semantics(self) -> None:
        genre_a = GenreFactory()
        genre_b = GenreFactory()
        prod_both = ProductionFactory()
        prod_only_a = ProductionFactory()

        ProductionGenreFactory(production=prod_both, genre=genre_a, position=1)
        ProductionGenreFactory(production=prod_both, genre=genre_b, position=2)
        ProductionGenreFactory(production=prod_only_a, genre=genre_a, position=1)

        params = QueryDict("", mutable=True)
        params.setlist("genre", [str(genre_a.id), str(genre_b.id)])

        response = self.client.get(self.list_url(), params, **pub_headers())
        results = response.data.get("results", response.data)
        assert [item["id"] for item in results] == [prod_both.id]

    def test_filter_by_multiple_tags_uses_and_semantics(self) -> None:
        tag_a = TagFactory()
        tag_b = TagFactory()
        prod_both = ProductionFactory()
        prod_only_a = ProductionFactory()

        ProductionTagFactory(production=prod_both, tag=tag_a)
        ProductionTagFactory(production=prod_both, tag=tag_b)
        ProductionTagFactory(production=prod_only_a, tag=tag_a)

        params = QueryDict("", mutable=True)
        params.setlist("tag", [str(tag_a.id), str(tag_b.id)])

        response = self.client.get(self.list_url(), params, **pub_headers())
        results = response.data.get("results", response.data)
        assert [item["id"] for item in results] == [prod_both.id]

    def test_filter_by_comma_separated_tags_uses_and_semantics(self) -> None:
        tag_a = TagFactory()
        tag_b = TagFactory()
        prod_both = ProductionFactory()
        prod_only_b = ProductionFactory()

        ProductionTagFactory(production=prod_both, tag=tag_a)
        ProductionTagFactory(production=prod_both, tag=tag_b)
        ProductionTagFactory(production=prod_only_b, tag=tag_b)

        response = self.client.get(self.list_url(), {"tag": f"{tag_a.id},{tag_b.id}"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert [item["id"] for item in results] == [prod_both.id]

    def test_filter_has_media(self) -> None:
        gallery = MediaGalleryFactory()
        ProductionFactory(media_gallery=gallery)
        ProductionFactory(media_gallery=None)
        response = self.client.get(self.list_url(), {"has_media": "true"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_by_translated_title(self) -> None:
        lang = LanguageFactory(code="en")
        prod_a = ProductionFactory()
        prod_b = ProductionFactory()
        ProductionTranslationFactory(production=prod_a, language=lang, title="Hamlet")
        ProductionTranslationFactory(production=prod_b, language=lang, title="Macbeth")
        response = self.client.get(self.list_url(), {"title": "Hamlet"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_default_ordering_newest_first(self) -> None:
        ProductionFactory.create_batch(3)
        response = self.client.get(self.list_url(), **pub_headers())
        ids = [r["id"] for r in response.data.get("results", response.data)]
        assert ids[0] > ids[-1]

    def test_ordering_by_attendance_mode(self) -> None:
        ProductionFactory(attendance_mode="online")
        ProductionFactory(attendance_mode="offline")
        response = self.client.get(self.list_url(), {"ordering": "attendance_mode"}, **pub_headers())
        modes = [r["attendance_mode"] for r in response.data.get("results", response.data)]
        assert modes == sorted(modes)

    def test_ordering_by_title_sort(self) -> None:
        lang = LanguageFactory(code="en")
        prod_b = ProductionFactory()
        prod_a = ProductionFactory()
        ProductionTranslationFactory(production=prod_b, language=lang, title="Zulu")
        ProductionTranslationFactory(production=prod_a, language=lang, title="Alpha")

        response = self.client.get(self.list_url(), {"ordering": "title_sort"}, **pub_headers())
        ids = [r["id"] for r in response.data.get("results", response.data)]
        assert ids[:2] == [prod_a.id, prod_b.id]

    def test_search_by_title_translation(self) -> None:
        lang = LanguageFactory(code="en")
        prod = ProductionFactory()
        ProductionTranslationFactory(production=prod, language=lang, title="Hamlet")
        ProductionFactory()
        response = self.client.get(self.list_url(), {"search": "Hamlet"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_search_by_artist_name(self) -> None:
        lang = LanguageFactory(code="en")
        prod = ProductionFactory()
        ProductionTranslationFactory(production=prod, language=lang, artist_name="Toneelschuur")
        ProductionFactory()
        response = self.client.get(self.list_url(), {"search": "Toneelschuur"}, **pub_headers())
        results = response.data.get("results", response.data)
        assert len(results) == 1


def _dt(year, month, day, hour=0):
    return datetime(year, month, day, hour, tzinfo=UTC)


class TestProductionFilterFirstEventStartAfter:
    """First event start date filters for ProductionFilter."""

    def _qs(self, params):
        return ProductionFilter(params, queryset=Production.objects.all()).qs

    def setup_method(self):
        Production.objects.all().delete()
        self.early = ProductionFactory()
        self.late = ProductionFactory()
        EventFactory(production=self.early, starts_at=_dt(2025, 1, 1), ends_at=_dt(2025, 1, 1, 22))
        EventFactory(production=self.late, starts_at=_dt(2025, 9, 1), ends_at=_dt(2025, 9, 1, 22))

    def test_after_cutoff_excludes_early_production(self) -> None:
        assert self.early not in self._qs({"first_event_start_after": "2025-06-01T00:00:00Z"})

    def test_after_cutoff_includes_late_production(self) -> None:
        assert self.late in self._qs({"first_event_start_after": "2025-06-01T00:00:00Z"})

    def test_exact_boundary_is_inclusive(self) -> None:
        assert self.late in self._qs({"first_event_start_after": "2025-09-01T00:00:00Z"})

    def test_future_cutoff_returns_empty(self) -> None:
        assert self._qs({"first_event_start_after": "2030-01-01T00:00:00Z"}).count() == 0

    def test_past_cutoff_returns_both(self) -> None:
        assert self._qs({"first_event_start_after": "2020-01-01T00:00:00Z"}).count() == 2

    def test_production_without_events_is_excluded(self) -> None:
        no_event = ProductionFactory()
        assert no_event not in self._qs({"first_event_start_after": "2020-01-01T00:00:00Z"})


class TestProductionFilterFirstEventStartBefore:
    """First_event_start_before must hold only productions with an event on or before the timestamp."""

    def _qs(self, params):
        return ProductionFilter(params, queryset=Production.objects.all()).qs

    def setup_method(self):
        Production.objects.all().delete()
        self.early = ProductionFactory()
        self.late = ProductionFactory()
        EventFactory(production=self.early, starts_at=_dt(2025, 1, 1), ends_at=_dt(2025, 1, 1, 22))
        EventFactory(production=self.late, starts_at=_dt(2025, 9, 1), ends_at=_dt(2025, 9, 1, 22))

    def test_before_cutoff_excludes_late_production(self) -> None:
        assert self.late not in self._qs({"first_event_start_before": "2025-06-01T00:00:00Z"})

    def test_before_cutoff_includes_early_production(self) -> None:
        assert self.early in self._qs({"first_event_start_before": "2025-06-01T00:00:00Z"})

    def test_exact_boundary_is_inclusive(self) -> None:
        assert self.early in self._qs({"first_event_start_before": "2025-01-01T00:00:00Z"})

    def test_very_old_cutoff_returns_empty(self) -> None:
        assert self._qs({"first_event_start_before": "2000-01-01T00:00:00Z"}).count() == 0

    def test_future_cutoff_returns_both(self) -> None:
        assert self._qs({"first_event_start_before": "2030-01-01T00:00:00Z"}).count() == 2

    def test_production_without_events_is_excluded(self) -> None:
        no_event = ProductionFactory()
        assert no_event not in self._qs({"first_event_start_before": "2030-01-01T00:00:00Z"})


class TestProductionFilterEventDateRange:
    """After/before filters should work together to return productions with an event in the specified date range."""

    def _qs(self, params):
        return ProductionFilter(params, queryset=Production.objects.all()).qs

    def setup_method(self):
        Production.objects.all().delete()
        self.jan = ProductionFactory()
        self.may = ProductionFactory()
        self.sep = ProductionFactory()
        for prod, month in ((self.jan, 1), (self.may, 5), (self.sep, 9)):
            EventFactory(production=prod, starts_at=_dt(2025, month, 1), ends_at=_dt(2025, month, 1, 22))

    def test_range_returns_only_production_inside_window(self) -> None:
        qs = self._qs(
            {
                "first_event_start_after": "2025-03-01T00:00:00Z",
                "first_event_start_before": "2025-07-01T00:00:00Z",
            }
        )
        assert list(qs) == [self.may]

    def test_impossible_range_returns_empty(self) -> None:
        qs = self._qs(
            {
                "first_event_start_after": "2025-08-01T00:00:00Z",
                "first_event_start_before": "2025-04-01T00:00:00Z",
            }
        )
        assert qs.count() == 0
