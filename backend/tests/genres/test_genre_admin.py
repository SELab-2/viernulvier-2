"""
Tests for apps/genres/admin.py

Covers:
- Admin registrations for Genre, GenreTranslation
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
    GenreTranslationInline,
)
from apps.genres.models import Genre, GenreTranslation
from tests.factories.genre import (
    GenreFactory,
    GenreTranslationFactory,
)
from tests.factories.language import LanguageFactory

# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestGenreAdminRegistration(TestCase):
    """Verify genre-related admins are registered on the default site."""

    def test_genre_registered(self) -> None:
        assert Genre in admin.site._registry
        assert isinstance(admin.site._registry[Genre], GenreAdmin)



# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestGenreAdminInheritance(TestCase):
    """Ensure admin classes inherit from BaseAdmin/ModelAdmin."""

    def test_genre_inherits(self) -> None:
        assert issubclass(GenreAdmin, BaseAdmin)
        assert issubclass(GenreAdmin, admin.ModelAdmin)


# ---------------------------------------------------------------------------
# Config checks
# ---------------------------------------------------------------------------


class TestGenreAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = GenreAdmin(Genre, admin.site)

    def test_list_display(self) -> None:
        assert "id" in self.admin.list_display
        assert "type" in self.admin.list_display

    def test_list_filter(self) -> None:
        assert self.admin.list_filter == ()

    def test_search_fields(self) -> None:
        assert "type" in self.admin.search_fields

    def test_ordering(self) -> None:
        assert "id" in self.admin.ordering

    def test_inlines_include_translation_inline(self) -> None:
        assert GenreTranslationInline in self.admin.inlines


class TestGenreTranslationInlineConfig(TestCase):
    def setUp(self) -> None:
        self.inline = GenreTranslationInline(Genre, admin.site)

    def test_model(self) -> None:
        assert self.inline.model is GenreTranslation

    def test_fields(self) -> None:
        assert tuple(self.inline.fields) == ("language", "name")

    def test_autocomplete_fields(self) -> None:
        assert "language" in self.inline.autocomplete_fields

    def test_extra(self) -> None:
        assert self.inline.extra == 1

# ---------------------------------------------------------------------------
# Functional admin tests
# ---------------------------------------------------------------------------


class TestGenreAdminFunctional(TestCase):
    """Functional admin flows for genre models."""

    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(username="admin", password="password", email="admin@example.com")
        self.client.force_login(self.superuser)

        self.language = LanguageFactory(code="en", name="English")
        self.genre = GenreFactory(type="Theater")
        self.translation = GenreTranslationFactory(
            name="Theater",
            language=self.language,
            genre=self.genre,
        )

    # -- Genre --------------------------------------------------------------

    def test_genre_changelist(self) -> None:
        url = reverse("admin:genres_genre_changelist")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_genre_add(self) -> None:
        url = reverse("admin:genres_genre_add")
        response = self.client.post(
            url,
            {
                "type": "Festival",
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
        assert response.status_code == 200
        assert Genre.objects.filter(type="Festival").exists()

    def test_genre_change(self) -> None:
        url = reverse("admin:genres_genre_change", args=[self.genre.pk])
        response = self.client.post(
            url,
            {
                "type": "Opera",
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
        assert response.status_code == 200
        self.genre.refresh_from_db()
        assert self.genre.type == "Opera"

    def test_genre_delete(self) -> None:
        url = reverse("admin:genres_genre_delete", args=[self.genre.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not Genre.objects.filter(pk=self.genre.pk).exists()


# ---------------------------------------------------------------------------
# Inline / autocomplete field edge tests
# ---------------------------------------------------------------------------


class TestGenreTranslationInlineEdgeCases(TestCase):
    """Check inline configuration and behavior."""

    def setUp(self) -> None:
        self.inline = GenreTranslationInline(Genre, admin.site)

    def test_inline_model_is_correct(self) -> None:
        assert self.inline.model is GenreTranslation

    def test_inline_fields_and_autocomplete(self) -> None:
        assert self.inline.fields == ("language", "name")
        assert "language" in self.inline.autocomplete_fields

    def test_inline_extra_forms_default(self) -> None:
        assert self.inline.extra == 1


# ---------------------------------------------------------------------------
# Admin functional edge cases
# ---------------------------------------------------------------------------


class TestGenreAdminFunctionalEdgeCases(TestCase):
    """Functional admin tests for edge cases like empty form submission."""

    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(username="admin", password="password", email="admin@example.com")
        self.client.force_login(self.superuser)
        self.language = LanguageFactory()
        self.genre = GenreFactory(type="Theater")
        self.translation = GenreTranslationFactory(genre=self.genre, language=self.language, name="Theater")

    def test_genre_add_with_empty_translation(self) -> None:
        url = reverse("admin:genres_genre_add")
        response = self.client.post(
            url,
            {
                "type": "Concert",
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
        assert response.status_code == 200
        assert Genre.objects.filter(type="Concert").exists()

    def test_genre_change_partial_translation_update(self) -> None:
        url = reverse("admin:genres_genre_change", args=[self.genre.pk])
        response = self.client.post(
            url,
            {
                "type": "Drama",
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
        assert response.status_code == 200
        self.translation.refresh_from_db()
        assert self.translation.name == "Updated Theater"
