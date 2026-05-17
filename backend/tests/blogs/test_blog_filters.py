"""Tests for apps/blogs/filters.py."""

import pytest

from apps.blogs.filters import BlogFilter
from apps.blogs.models import Blog
from tests.factories.blog import BlogFactory, BlogTranslationFactory
from tests.factories.language import LanguageFactory
from tests.factories.production import ProductionFactory

pytestmark = pytest.mark.django_db


class TestBlogFilter:
    def _qs(self, params):
        return BlogFilter(params, queryset=Blog.objects.all()).qs

    def test_slug_icontains(self) -> None:
        BlogFactory(slug="summer-special")
        BlogFactory(slug="winter-special")

        assert self._qs({"slug": "summer"}).count() == 1

    def test_title_filter_matches_translation(self) -> None:
        lang = LanguageFactory(code="en")
        blog_a = BlogFactory(slug="a")
        blog_b = BlogFactory(slug="b")
        BlogTranslationFactory(blog=blog_a, language=lang, title="Summer Festival")
        BlogTranslationFactory(blog=blog_b, language=lang, title="Winter Gala")

        result = self._qs({"title": "festival"})

        assert result.count() == 1
        assert result.first() == blog_a

    def test_title_filter_is_distinct(self) -> None:
        blog = BlogFactory()
        BlogTranslationFactory(blog=blog, language=LanguageFactory(code="en"), title="Shared")
        BlogTranslationFactory(blog=blog, language=LanguageFactory(code="nl"), title="Shared")

        assert self._qs({"title": "Shared"}).count() == 1

    def test_published_true_filters_published_only(self) -> None:
        BlogFactory(published_at=None)
        BlogFactory()

        assert self._qs({"published": "true"}).count() == 1

    def test_published_false_filters_drafts_only(self) -> None:
        BlogFactory(published_at=None)
        BlogFactory()

        assert self._qs({"published": "false"}).count() == 1

    def test_published_none_returns_unfiltered_queryset(self) -> None:
        BlogFactory(published_at=None)
        published_blog = BlogFactory()

        filterset = BlogFilter({}, queryset=Blog.objects.all())
        result = filterset.filter_published(Blog.objects.all(), "published", None)

        assert result.count() == 2
        assert published_blog in result

    def test_filter_by_production_id(self) -> None:
        production = ProductionFactory()
        matching = BlogFactory()
        non_matching = BlogFactory()
        matching.productions.add(production)

        result = self._qs({"production": production.id})

        assert result.count() == 1
        assert result.first() == matching
        assert result.first() != non_matching

    def test_external_id_filter_inherited_from_base_model_filter(self) -> None:
        BlogFactory(external_id="blog-001")
        BlogFactory(external_id="blog-002")

        assert self._qs({"external_id": "BLOG-001"}).count() == 1
