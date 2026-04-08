"""
Tests for apps/blogs/admin.py

Covers:
- Admin registration for Blog and BlogTranslation
- Admin classes inherit from BaseAdmin
- Admin configuration (list/search/filter/ordering/inlines/autocomplete)
- Custom BlogAdmin helper methods
- Functional admin pages with a superuser
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.blogs.admin import BlogAdmin, BlogTranslationAdmin, BlogTranslationInline
from apps.blogs.models import Blog, BlogTranslation
from apps.core.admin import BaseAdmin
from tests.factories.blog import BlogFactory, BlogTranslationFactory
from tests.factories.language import LanguageFactory
from tests.factories.production import ProductionFactory


class TestBlogAdminRegistration(TestCase):
    def test_blog_registered(self) -> None:
        assert Blog in admin.site._registry
        assert isinstance(admin.site._registry[Blog], BlogAdmin)

    def test_blog_translation_registered(self) -> None:
        assert BlogTranslation in admin.site._registry
        assert isinstance(admin.site._registry[BlogTranslation], BlogTranslationAdmin)


class TestBlogAdminInheritance(TestCase):
    def test_blog_admin_inherits_from_base_admin(self) -> None:
        assert issubclass(BlogAdmin, BaseAdmin)
        assert issubclass(BlogAdmin, admin.ModelAdmin)

    def test_blog_translation_admin_inherits_from_base_admin(self) -> None:
        assert issubclass(BlogTranslationAdmin, BaseAdmin)
        assert issubclass(BlogTranslationAdmin, admin.ModelAdmin)


class TestBlogAdminConfig(TestCase):
    def setUp(self) -> None:
        self.blog_admin = BlogAdmin(Blog, admin.site)
        self.translation_admin = BlogTranslationAdmin(BlogTranslation, admin.site)
        self.inline = BlogTranslationInline(Blog, admin.site)

    def test_blog_list_display_contains_expected_fields(self) -> None:
        expected = {
            "id",
            "display_title",
            "slug",
            "published_status",
            "published_at",
            "linked_productions_count",
        }
        assert expected.issubset(set(self.blog_admin.list_display))

    def test_blog_list_filter_contains_published_at(self) -> None:
        assert "published_at" in self.blog_admin.list_filter

    def test_blog_search_fields(self) -> None:
        assert "slug" in self.blog_admin.search_fields
        assert "translations__title" in self.blog_admin.search_fields
        assert "translations__body" in self.blog_admin.search_fields

    def test_blog_includes_translation_inline(self) -> None:
        assert BlogTranslationInline in self.blog_admin.inlines

    def test_blog_autocomplete_fields(self) -> None:
        assert "productions" in self.blog_admin.autocomplete_fields

    def test_translation_admin_list_display(self) -> None:
        assert "id" in self.translation_admin.list_display
        assert "title" in self.translation_admin.list_display
        assert "language" in self.translation_admin.list_display
        assert "blog" in self.translation_admin.list_display
        assert "has_excerpt" in self.translation_admin.list_display

    def test_translation_admin_list_filter(self) -> None:
        assert "language__code" in self.translation_admin.list_filter

    def test_translation_admin_autocomplete_fields(self) -> None:
        assert "language" in self.translation_admin.autocomplete_fields
        assert "blog" in self.translation_admin.autocomplete_fields

    def test_inline_config(self) -> None:
        assert self.inline.model is BlogTranslation
        assert tuple(self.inline.fields) == ("language", "title", "excerpt", "body")
        assert self.inline.extra == 1
        assert "language" in self.inline.autocomplete_fields


class TestBlogAdminMethods(TestCase):
    def setUp(self) -> None:
        self.admin = BlogAdmin(Blog, admin.site)
        self.lang_en = LanguageFactory(code="en", name="English")

    def test_display_title_prefers_english_translation(self) -> None:
        blog = BlogFactory(slug="fallback")
        BlogTranslationFactory(blog=blog, language=self.lang_en, title="English Title")

        assert self.admin.display_title(blog) == "English Title"

    def test_display_title_falls_back_to_slug(self) -> None:
        blog = BlogFactory(slug="fallback-slug")

        assert self.admin.display_title(blog) == "fallback-slug"

    def test_published_status_true_when_published_at_set(self) -> None:
        blog = BlogFactory()

        assert self.admin.published_status(blog) is True

    def test_published_status_false_when_draft(self) -> None:
        blog = BlogFactory(published_at=None)

        assert self.admin.published_status(blog) is False

    def test_linked_productions_count_renders_none_when_empty(self) -> None:
        blog = BlogFactory()

        rendered = self.admin.linked_productions_count(blog)

        assert "None" in str(rendered)

    def test_linked_productions_count_returns_numeric_count(self) -> None:
        blog = BlogFactory()
        blog.productions.add(ProductionFactory(), ProductionFactory())

        assert self.admin.linked_productions_count(blog) == "2"

    def test_get_queryset_prefetches_expected_relations(self) -> None:
        rf = RequestFactory()
        request = rf.get("/admin/blogs/blog/")

        queryset = self.admin.get_queryset(request)

        assert "translations__language" in queryset._prefetch_related_lookups
        assert "productions" in queryset._prefetch_related_lookups


class TestBlogTranslationAdminMethods(TestCase):
    def setUp(self) -> None:
        self.admin = BlogTranslationAdmin(BlogTranslation, admin.site)

    def test_has_excerpt_true_when_excerpt_exists(self) -> None:
        translation = BlogTranslationFactory(excerpt="Some excerpt")

        assert self.admin.has_excerpt(translation) is True

    def test_has_excerpt_false_when_excerpt_empty(self) -> None:
        translation = BlogTranslationFactory(excerpt="")

        assert self.admin.has_excerpt(translation) is False


class TestBlogAdminFunctional(TestCase):
    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(username="admin", password="password", email="admin@example.com")
        self.client.force_login(self.superuser)

        self.language = LanguageFactory(code="en", name="English")
        self.language_nl = LanguageFactory(code="nl", name="Dutch")
        self.production = ProductionFactory()
        self.blog = BlogFactory(slug="admin-blog")
        self.translation = BlogTranslationFactory(
            blog=self.blog,
            language=self.language,
            title="Admin title",
            body="Admin body",
            excerpt="Admin excerpt",
        )

    def test_blog_changelist(self) -> None:
        response = self.client.get(reverse("admin:blogs_blog_changelist"))

        assert response.status_code == 200

    def test_blog_add(self) -> None:
        response = self.client.post(
            reverse("admin:blogs_blog_add"),
            {
                "slug": "admin-added-blog",
                "published_at": "",
                "cover_image": "",
                "productions": [self.production.pk],
                "translations-TOTAL_FORMS": 0,
                "translations-INITIAL_FORMS": 0,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
            },
            follow=True,
        )

        assert response.status_code == 200
        assert Blog.objects.filter(slug="admin-added-blog").exists()

    def test_blog_change(self) -> None:
        response = self.client.post(
            reverse("admin:blogs_blog_change", args=[self.blog.pk]),
            {
                "slug": "admin-updated-blog",
                "published_at": "",
                "cover_image": "",
                "productions": [self.production.pk],
                "translations-TOTAL_FORMS": 1,
                "translations-INITIAL_FORMS": 1,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
                "translations-0-id": self.translation.pk,
                "translations-0-language": self.language.pk,
                "translations-0-title": self.translation.title,
                "translations-0-excerpt": self.translation.excerpt,
                "translations-0-body": self.translation.body,
            },
            follow=True,
        )

        assert response.status_code == 200
        self.blog.refresh_from_db()
        assert self.blog.slug == "admin-updated-blog"

    def test_blog_delete(self) -> None:
        response = self.client.post(
            reverse("admin:blogs_blog_delete", args=[self.blog.pk]),
            {"post": "yes"},
            follow=True,
        )

        assert response.status_code == 200
        assert not Blog.objects.filter(pk=self.blog.pk).exists()

    def test_blog_translation_changelist(self) -> None:
        response = self.client.get(reverse("admin:blogs_blogtranslation_changelist"))

        assert response.status_code == 200

    def test_blog_translation_add(self) -> None:
        response = self.client.post(
            reverse("admin:blogs_blogtranslation_add"),
            {
                "blog": self.blog.pk,
                "language": self.language_nl.pk,
                "title": "Added in admin",
                "excerpt": "Admin excerpt",
                "body": "Admin body",
            },
            follow=True,
        )

        assert response.status_code == 200
        assert BlogTranslation.objects.filter(blog=self.blog, language=self.language_nl, title="Added in admin").exists()

    def test_blog_translation_change(self) -> None:
        response = self.client.post(
            reverse("admin:blogs_blogtranslation_change", args=[self.translation.pk]),
            {
                "blog": self.blog.pk,
                "language": self.language.pk,
                "title": "Changed in admin",
                "excerpt": self.translation.excerpt,
                "body": self.translation.body,
            },
            follow=True,
        )

        assert response.status_code == 200
        self.translation.refresh_from_db()
        assert self.translation.title == "Changed in admin"

    def test_blog_translation_delete(self) -> None:
        response = self.client.post(
            reverse("admin:blogs_blogtranslation_delete", args=[self.translation.pk]),
            {"post": "yes"},
            follow=True,
        )

        assert response.status_code == 200
        assert not BlogTranslation.objects.filter(pk=self.translation.pk).exists()
