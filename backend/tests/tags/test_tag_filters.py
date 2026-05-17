"""Tests for TagFilter behaviour and tag API filtering/search/ordering."""

from django.test import override_settings
import pytest

from apps.tags.filters import TagFilter
from apps.tags.models import Tag
from tests.factories.language import LanguageFactory
from tests.factories.tag import TagFactory, TagTranslationFactory
from tests.helpers.api import INTERNAL_API_KEY, PUBLIC_API_KEY, BaseViewSetTestCase, paginated_results

pytestmark = pytest.mark.django_db


# =====================================================
# TagFilter
# =====================================================


class TestTagFilter:
    def _qs(self, params):
        return TagFilter(params, queryset=Tag.objects.all()).qs

    def test_type_icontains(self) -> None:
        TagFactory(type="theme")
        TagFactory(type="audience")

        assert self._qs({"type": "theme"}).count() == 1
        assert self._qs({"type": "hem"}).count() == 1

    def test_type_case_insensitive(self) -> None:
        TagFactory(type="Theme")

        assert self._qs({"type": "theme"}).count() == 1

    def test_source_icontains(self) -> None:
        TagFactory(source="uitdatabank")
        TagFactory(source="system")

        assert self._qs({"source": "uitdatabank"}).count() == 1
        assert self._qs({"source": "data"}).count() == 1

    def test_is_enabled_true(self) -> None:
        TagFactory(is_enabled=True)
        TagFactory(is_enabled=False)

        assert self._qs({"is_enabled": "true"}).count() == 1

    def test_is_enabled_false(self) -> None:
        TagFactory(is_enabled=True)
        TagFactory(is_enabled=False)

        assert self._qs({"is_enabled": "false"}).count() == 1

    def test_name_filter_across_translations(self) -> None:
        lang = LanguageFactory(code="en")
        tag_a = TagFactory()
        tag_b = TagFactory()
        TagTranslationFactory(tag=tag_a, language=lang, name="Contemporary")
        TagTranslationFactory(tag=tag_b, language=lang, name="Family")

        result = self._qs({"name": "contemporary"})

        assert result.count() == 1
        assert result.first() == tag_a

    def test_name_filter_case_insensitive(self) -> None:
        lang = LanguageFactory(code="en")
        tag = TagFactory()
        TagTranslationFactory(tag=tag, language=lang, name="Contemporary")

        assert self._qs({"name": "CONTEMPORARY"}).count() == 1

    def test_name_filter_distinct_no_duplicates(self) -> None:
        lang_nl = LanguageFactory(code="nl")
        lang_fr = LanguageFactory(code="fr")
        tag = TagFactory()
        TagTranslationFactory(tag=tag, language=lang_nl, name="Modern")
        TagTranslationFactory(tag=tag, language=lang_fr, name="Moderne")

        assert self._qs({"name": "odern"}).count() == 1

    def test_name_filter_no_match(self) -> None:
        lang = LanguageFactory(code="en")
        tag = TagFactory()
        TagTranslationFactory(tag=tag, language=lang, name="Jazz")

        assert self._qs({"name": "classical"}).count() == 0

    def test_external_id_iexact(self) -> None:
        TagFactory(external_id="TAG-001")
        TagFactory(external_id="TAG-002")

        assert self._qs({"external_id": "tag-001"}).count() == 1

    def test_type_and_is_enabled_combined(self) -> None:
        TagFactory(type="theme", is_enabled=True)
        TagFactory(type="theme", is_enabled=False)
        TagFactory(type="audience", is_enabled=True)

        assert self._qs({"type": "theme", "is_enabled": "true"}).count() == 1

    def test_no_params_returns_all(self) -> None:
        TagFactory.create_batch(4)

        assert self._qs({}).count() == 4


# =====================================================
# TagViewSet
# =====================================================


@override_settings(PUBLIC_API_KEY=PUBLIC_API_KEY, INTERNAL_API_KEY=INTERNAL_API_KEY)
class TestTagViewSet(BaseViewSetTestCase):
    resource_name = "tag"

    def setUp(self) -> None:
        super().setUp()
        Tag.objects.all().delete()

    def test_anon_is_rejected(self) -> None:
        response = self.client.get(self.list_url())
        assert response.status_code in (401, 403)

    def test_public_can_list(self) -> None:
        TagFactory.create_batch(3)
        response = self.client.get(self.list_url(), **self.pub_headers())
        assert response.status_code == 200
        results = paginated_results(response)
        assert len(results) == 3

    def test_public_can_retrieve(self) -> None:
        tag = TagFactory()
        response = self.client.get(self.detail_url(pk=tag.pk), **self.pub_headers())
        assert response.status_code == 200

    def test_public_cannot_delete(self) -> None:
        tag = TagFactory()
        response = self.client.delete(self.detail_url(pk=tag.pk), **self.pub_headers())
        assert response.status_code == 403

    def test_public_cannot_create(self) -> None:
        response = self.client.post(self.list_url(), {"type": "theme"}, **self.pub_headers())
        assert response.status_code == 403

    def test_internal_can_delete(self) -> None:
        tag = TagFactory()
        response = self.client.delete(self.detail_url(pk=tag.pk), **self.int_headers())
        assert response.status_code == 204
        assert not Tag.objects.filter(pk=tag.pk).exists()

    def test_filter_by_type(self) -> None:
        TagFactory(type="theme")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"type": "theme"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_filter_by_is_enabled(self) -> None:
        TagFactory(is_enabled=True)
        TagFactory(is_enabled=False)
        response = self.client.get(self.list_url(), {"is_enabled": "true"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_filter_by_translated_name(self) -> None:
        lang = LanguageFactory(code="en")
        tag_a = TagFactory()
        tag_b = TagFactory()
        TagTranslationFactory(tag=tag_a, language=lang, name="Contemporary")
        TagTranslationFactory(tag=tag_b, language=lang, name="Family")
        response = self.client.get(self.list_url(), {"name": "Contemporary"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_filter_by_source(self) -> None:
        TagFactory(source="uitdatabank")
        TagFactory(source="system")
        response = self.client.get(self.list_url(), {"source": "uitdatabank"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_ordering_by_type_ascending(self) -> None:
        TagFactory(type="theme")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"ordering": "type"}, **self.pub_headers())
        types = [r["type"] for r in paginated_results(response)]
        assert types == sorted(types)

    def test_ordering_by_type_descending(self) -> None:
        TagFactory(type="theme")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"ordering": "-type"}, **self.pub_headers())
        types = [r["type"] for r in paginated_results(response)]
        assert types == sorted(types, reverse=True)

    def test_default_ordering_by_id(self) -> None:
        TagFactory.create_batch(3)
        response = self.client.get(self.list_url(), **self.pub_headers())
        ids = [r["id"] for r in paginated_results(response)]
        assert ids == sorted(ids)

    def test_search_by_type(self) -> None:
        TagFactory(type="theme")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"search": "theme"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_search_by_source(self) -> None:
        TagFactory(source="uitdatabank")
        TagFactory(source="system")
        response = self.client.get(self.list_url(), {"search": "uitdatabank"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1

    def test_search_by_translated_name(self) -> None:
        lang = LanguageFactory(code="en")
        tag = TagFactory(type="theme")
        TagTranslationFactory(tag=tag, language=lang, name="Contemporary")
        TagFactory(type="audience")
        response = self.client.get(self.list_url(), {"search": "Contemporary"}, **self.pub_headers())
        results = paginated_results(response)
        assert len(results) == 1
