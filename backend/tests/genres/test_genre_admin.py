"""
Tests for apps/genres/admin.py

Covers:
- Admin registrations for GenreUseAs, Genre, GenreTranslation
- Admin classes inherit from BaseAdmin
- list_display / list_filter / search_fields / ordering settings
- Functional admin pages (changelist, add, change, delete) with superuser
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.genres.admin import (
    GenreAdmin,
    GenreTranslationAdmin,
    GenreTranslationInline,
    GenreUseAsAdmin,
)
from apps.genres.models import Genre, GenreTranslation, GenreUseAs
from tests.factories.genre import (
    GenreFactory,
    GenreTranslationFactory,
    GenreUseAsFactory,
)
from tests.factories.language import LanguageFactory

# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestGenreAdminRegistration(TestCase):
    """Verify genre-related admins are registered on the default site."""

    def test_genreuseas_registered(self):
        self.assertIn(GenreUseAs, admin.site._registry)
        self.assertIsInstance(admin.site._registry[GenreUseAs], GenreUseAsAdmin)

    def test_genre_registered(self):
        self.assertIn(Genre, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Genre], GenreAdmin)

    def test_genretranslation_registered(self):
        self.assertIn(GenreTranslation, admin.site._registry)
        self.assertIsInstance(
            admin.site._registry[GenreTranslation], GenreTranslationAdmin
        )


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestGenreAdminInheritance(TestCase):
    """Ensure admin classes inherit from BaseAdmin/ModelAdmin."""

    def test_genreuseas_inherits(self):
        self.assertTrue(issubclass(GenreUseAsAdmin, BaseAdmin))
        self.assertTrue(issubclass(GenreUseAsAdmin, admin.ModelAdmin))

    def test_genre_inherits(self):
        self.assertTrue(issubclass(GenreAdmin, BaseAdmin))
        self.assertTrue(issubclass(GenreAdmin, admin.ModelAdmin))

    def test_genretranslation_inherits(self):
        self.assertTrue(issubclass(GenreTranslationAdmin, BaseAdmin))
        self.assertTrue(issubclass(GenreTranslationAdmin, admin.ModelAdmin))


# ---------------------------------------------------------------------------
# Config checks
# ---------------------------------------------------------------------------


class TestGenreUseAsAdminConfig(TestCase):
    def setUp(self):
        self.admin = GenreUseAsAdmin(GenreUseAs, admin.site)

    def test_list_display(self):
        self.assertIn("id", self.admin.list_display)
        self.assertIn("name", self.admin.list_display)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ())  # none set

    def test_search_fields(self):
        self.assertIn("name", self.admin.search_fields)

    def test_ordering(self):
        self.assertIn("name", self.admin.ordering)


class TestGenreAdminConfig(TestCase):
    def setUp(self):
        self.admin = GenreAdmin(Genre, admin.site)

    def test_list_display(self):
        self.assertIn("id", self.admin.list_display)
        self.assertIn("type", self.admin.list_display)
        self.assertIn("use_as", self.admin.list_display)

    def test_list_filter(self):
        self.assertIn("use_as", self.admin.list_filter)

    def test_search_fields(self):
        self.assertIn("type", self.admin.search_fields)

    def test_ordering(self):
        self.assertIn("id", self.admin.ordering)

    def test_inlines_include_translation_inline(self):
        self.assertIn(GenreTranslationInline, self.admin.inlines)


class TestGenreTranslationInlineConfig(TestCase):
    def setUp(self):
        self.inline = GenreTranslationInline(Genre, admin.site)

    def test_model(self):
        self.assertIs(self.inline.model, GenreTranslation)

    def test_fields(self):
        self.assertEqual(tuple(self.inline.fields), ("language", "name"))

    def test_autocomplete_fields(self):
        self.assertIn("language", self.inline.autocomplete_fields)

    def test_extra(self):
        self.assertEqual(self.inline.extra, 1)


class TestGenreTranslationAdminConfig(TestCase):
    def setUp(self):
        self.admin = GenreTranslationAdmin(GenreTranslation, admin.site)

    def test_list_display(self):
        for field in ("id", "name", "language", "genre"):
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self):
        self.assertIn("language__code", self.admin.list_filter)

    def test_search_fields(self):
        self.assertIn("name", self.admin.search_fields)

    def test_ordering(self):
        self.assertIn("id", self.admin.ordering)


# ---------------------------------------------------------------------------
# Functional admin tests
# ---------------------------------------------------------------------------


class TestGenreAdminFunctional(TestCase):
    """Functional admin flows for genre models."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", password="password", email="admin@example.com"
        )
        self.client.force_login(self.superuser)

        self.use_as = GenreUseAsFactory(name="genre")
        self.language = LanguageFactory(code="en", name="English")
        self.genre = GenreFactory(type="Theater", use_as=self.use_as)
        self.translation = GenreTranslationFactory(
            name="Theater",
            language=self.language,
            genre=self.genre,
        )

    # -- GenreUseAs ---------------------------------------------------------

    def test_useas_changelist(self):
        url = reverse("admin:genres_genreuseas_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_useas_add(self):
        url = reverse("admin:genres_genreuseas_add")
        response = self.client.post(url, {"name": "tag"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GenreUseAs.objects.filter(name="tag").exists())

    def test_useas_change(self):
        url = reverse("admin:genres_genreuseas_change", args=[self.use_as.pk])
        response = self.client.post(url, {"name": "genre-upd"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.use_as.refresh_from_db()
        self.assertEqual(self.use_as.name, "genre-upd")

    def test_useas_delete(self):
        url = reverse("admin:genres_genreuseas_delete", args=[self.use_as.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GenreUseAs.objects.filter(pk=self.use_as.pk).exists())

    # -- Genre --------------------------------------------------------------

    def test_genre_changelist(self):
        url = reverse("admin:genres_genre_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_genre_add(self):
        url = reverse("admin:genres_genre_add")
        response = self.client.post(
            url,
            {
                "type": "Festival",
                "use_as": self.use_as.pk,
                "translations-TOTAL_FORMS": 1,
                "translations-INITIAL_FORMS": 0,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
                "translations-0-id": "",
                "translations-0-language": "",
                "translations-0-name": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Genre.objects.filter(type="Festival").exists())

    def test_genre_change(self):
        url = reverse("admin:genres_genre_change", args=[self.genre.pk])
        response = self.client.post(
            url,
            {
                "type": "Opera",
                "use_as": self.use_as.pk,
                "translations-TOTAL_FORMS": 1,
                "translations-INITIAL_FORMS": 1,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
                "translations-0-id": self.translation.pk,
                "translations-0-language": self.language.pk,
                "translations-0-name": self.translation.name,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.genre.refresh_from_db()
        self.assertEqual(self.genre.type, "Opera")

    def test_genre_delete(self):
        url = reverse("admin:genres_genre_delete", args=[self.genre.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Genre.objects.filter(pk=self.genre.pk).exists())

    # -- GenreTranslation ---------------------------------------------------

    def test_translation_changelist(self):
        url = reverse("admin:genres_genretranslation_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_translation_add(self):
        url = reverse("admin:genres_genretranslation_add")
        response = self.client.post(
            url,
            {
                "name": "Theatre",
                "language": self.language.pk,
                "genre": self.genre.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GenreTranslation.objects.filter(name="Theatre").exists())

    def test_translation_change(self):
        url = reverse(
            "admin:genres_genretranslation_change", args=[self.translation.pk]
        )
        response = self.client.post(
            url,
            {
                "name": "Teater",
                "language": self.language.pk,
                "genre": self.genre.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.translation.refresh_from_db()
        self.assertEqual(self.translation.name, "Teater")

    def test_translation_delete(self):
        url = reverse(
            "admin:genres_genretranslation_delete", args=[self.translation.pk]
        )
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            GenreTranslation.objects.filter(pk=self.translation.pk).exists()
        )


# ---------------------------------------------------------------------------
# Queryset / performance related tests
# ---------------------------------------------------------------------------


class TestGenreAdminQueryset(TestCase):
    """Test select_related / prefetch_related optimizations."""

    def setUp(self):
        self.site = admin.site
        self.admin_genre = GenreAdmin(Genre, self.site)
        self.admin_translation = GenreTranslationAdmin(GenreTranslation, self.site)
        self.use_as_admin = GenreUseAsAdmin(GenreUseAs, self.site)

        self.use_as = GenreUseAsFactory()
        self.language = LanguageFactory()
        self.genre = GenreFactory(use_as=self.use_as)
        self.translation = GenreTranslationFactory(
            genre=self.genre, language=self.language
        )

    def test_genre_get_queryset_selects_use_as_and_prefetches_translations(self):
        qs = self.admin_genre.get_queryset(request=None)
        # Check that select_related('use_as') is applied
        self.assertTrue("use_as" in qs.query.select_related)
        # Check that translations are prefetch_related
        prefetches = {
            getattr(x, "prefetch_to", x) for x in qs._prefetch_related_lookups
        }
        self.assertIn("translations", prefetches)

    def test_genre_translation_get_queryset_selects_genre_and_language(self):
        qs = self.admin_translation.get_queryset(request=None)
        self.assertTrue("genre" in qs.query.select_related)
        self.assertTrue("language" in qs.query.select_related)


# ---------------------------------------------------------------------------
# Inline / autocomplete field edge tests
# ---------------------------------------------------------------------------


class TestGenreTranslationInlineEdgeCases(TestCase):
    """Check inline configuration and behavior."""

    def setUp(self):
        self.inline = GenreTranslationInline(Genre, admin.site)

    def test_inline_model_is_correct(self):
        self.assertIs(self.inline.model, GenreTranslation)

    def test_inline_fields_and_autocomplete(self):
        self.assertEqual(self.inline.fields, ("language", "name"))
        self.assertIn("language", self.inline.autocomplete_fields)

    def test_inline_extra_forms_default(self):
        self.assertEqual(self.inline.extra, 1)


# ---------------------------------------------------------------------------
# Admin functional edge cases
# ---------------------------------------------------------------------------


class TestGenreAdminFunctionalEdgeCases(TestCase):
    """Functional admin tests for edge cases like empty form submission."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", password="password", email="admin@example.com"
        )
        self.client.force_login(self.superuser)
        self.use_as = GenreUseAsFactory()
        self.language = LanguageFactory()
        self.genre = GenreFactory(type="Theater", use_as=self.use_as)
        self.translation = GenreTranslationFactory(
            genre=self.genre, language=self.language, name="Theater"
        )

    def test_genre_add_with_empty_translation(self):
        url = reverse("admin:genres_genre_add")
        response = self.client.post(
            url,
            {
                "type": "Concert",
                "use_as": self.use_as.pk,
                "translations-TOTAL_FORMS": 1,
                "translations-INITIAL_FORMS": 0,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
                "translations-0-id": "",
                "translations-0-language": "",
                "translations-0-name": "",
            },
            follow=True,
        )
        # Should still succeed, translation will be ignored
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Genre.objects.filter(type="Concert").exists())

    def test_genre_change_partial_translation_update(self):
        url = reverse("admin:genres_genre_change", args=[self.genre.pk])
        response = self.client.post(
            url,
            {
                "type": "Drama",
                "use_as": self.use_as.pk,
                "translations-TOTAL_FORMS": 1,
                "translations-INITIAL_FORMS": 1,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
                "translations-0-id": self.translation.pk,
                "translations-0-language": self.language.pk,
                "translations-0-name": "Updated Theater",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.translation.refresh_from_db()
        self.assertEqual(self.translation.name, "Updated Theater")
