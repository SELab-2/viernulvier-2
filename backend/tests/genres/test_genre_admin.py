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

    def test_genreuseas_registered(self) -> None:
        assert GenreUseAs in admin.site._registry
        assert isinstance(admin.site._registry[GenreUseAs], GenreUseAsAdmin)

    def test_genre_registered(self) -> None:
        assert Genre in admin.site._registry
        assert isinstance(admin.site._registry[Genre], GenreAdmin)

    def test_genretranslation_registered(self) -> None:
        assert GenreTranslation in admin.site._registry
        assert isinstance(admin.site._registry[GenreTranslation], GenreTranslationAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestGenreAdminInheritance(TestCase):
    """Ensure admin classes inherit from BaseAdmin/ModelAdmin."""

    def test_genreuseas_inherits(self) -> None:
        assert issubclass(GenreUseAsAdmin, BaseAdmin)
        assert issubclass(GenreUseAsAdmin, admin.ModelAdmin)

    def test_genre_inherits(self) -> None:
        assert issubclass(GenreAdmin, BaseAdmin)
        assert issubclass(GenreAdmin, admin.ModelAdmin)

    def test_genretranslation_inherits(self) -> None:
        assert issubclass(GenreTranslationAdmin, BaseAdmin)
        assert issubclass(GenreTranslationAdmin, admin.ModelAdmin)


# ---------------------------------------------------------------------------
# Config checks
# ---------------------------------------------------------------------------


class TestGenreUseAsAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = GenreUseAsAdmin(GenreUseAs, admin.site)

    def test_list_display(self) -> None:
        assert "id" in self.admin.list_display
        assert "name" in self.admin.list_display

    def test_list_filter(self) -> None:
        assert self.admin.list_filter == ()  # none set

    def test_search_fields(self) -> None:
        assert "name" in self.admin.search_fields

    def test_ordering(self) -> None:
        assert "name" in self.admin.ordering


class TestGenreAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = GenreAdmin(Genre, admin.site)

    def test_list_display(self) -> None:
        assert "id" in self.admin.list_display
        assert "type" in self.admin.list_display
        assert "use_as" in self.admin.list_display

    def test_list_filter(self) -> None:
        assert "use_as" in self.admin.list_filter

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


class TestGenreTranslationAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = GenreTranslationAdmin(GenreTranslation, admin.site)

    def test_list_display(self) -> None:
        for field in ("id", "name", "language", "genre"):
            assert field in self.admin.list_display

    def test_list_filter(self) -> None:
        assert "language__code" in self.admin.list_filter

    def test_search_fields(self) -> None:
        assert "name" in self.admin.search_fields

    def test_ordering(self) -> None:
        assert "id" in self.admin.ordering


# ---------------------------------------------------------------------------
# Functional admin tests
# ---------------------------------------------------------------------------


class TestGenreAdminFunctional(TestCase):
    """Functional admin flows for genre models."""

    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(username="admin", password="password", email="admin@example.com")
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

    def test_useas_changelist(self) -> None:
        url = reverse("admin:genres_genreuseas_changelist")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_useas_add(self) -> None:
        url = reverse("admin:genres_genreuseas_add")
        response = self.client.post(url, {"name": "tag"}, follow=True)
        assert response.status_code == 200
        assert GenreUseAs.objects.filter(name="tag").exists()

    def test_useas_change(self) -> None:
        url = reverse("admin:genres_genreuseas_change", args=[self.use_as.pk])
        response = self.client.post(url, {"name": "genre-upd"}, follow=True)
        assert response.status_code == 200
        self.use_as.refresh_from_db()
        assert self.use_as.name == "genre-upd"

    def test_useas_delete(self) -> None:
        url = reverse("admin:genres_genreuseas_delete", args=[self.use_as.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not GenreUseAs.objects.filter(pk=self.use_as.pk).exists()

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
        assert response.status_code == 200
        assert Genre.objects.filter(type="Festival").exists()

    def test_genre_change(self) -> None:
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
        assert response.status_code == 200
        self.genre.refresh_from_db()
        assert self.genre.type == "Opera"

    def test_genre_delete(self) -> None:
        url = reverse("admin:genres_genre_delete", args=[self.genre.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not Genre.objects.filter(pk=self.genre.pk).exists()

    # -- GenreTranslation ---------------------------------------------------

    def test_translation_changelist(self) -> None:
        url = reverse("admin:genres_genretranslation_changelist")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_translation_add(self) -> None:
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
        assert response.status_code == 200
        assert GenreTranslation.objects.filter(name="Theatre").exists()

    def test_translation_change(self) -> None:
        url = reverse("admin:genres_genretranslation_change", args=[self.translation.pk])
        response = self.client.post(
            url,
            {
                "name": "Teater",
                "language": self.language.pk,
                "genre": self.genre.pk,
            },
            follow=True,
        )
        assert response.status_code == 200
        self.translation.refresh_from_db()
        assert self.translation.name == "Teater"

    def test_translation_delete(self) -> None:
        url = reverse("admin:genres_genretranslation_delete", args=[self.translation.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not GenreTranslation.objects.filter(pk=self.translation.pk).exists()


# ---------------------------------------------------------------------------
# Queryset / performance related tests
# ---------------------------------------------------------------------------


class TestGenreAdminQueryset(TestCase):
    """Test select_related / prefetch_related optimizations."""

    def setUp(self) -> None:
        self.site = admin.site
        self.admin_genre = GenreAdmin(Genre, self.site)
        self.admin_translation = GenreTranslationAdmin(GenreTranslation, self.site)
        self.use_as_admin = GenreUseAsAdmin(GenreUseAs, self.site)

        self.use_as = GenreUseAsFactory()
        self.language = LanguageFactory()
        self.genre = GenreFactory(use_as=self.use_as)
        self.translation = GenreTranslationFactory(genre=self.genre, language=self.language)

    def test_genre_get_queryset_selects_use_as_and_prefetches_translations(self) -> None:
        qs = self.admin_genre.get_queryset(request=None)
        # Check that select_related('use_as') is applied
        assert "use_as" in qs.query.select_related
        # Check that translations are prefetch_related
        prefetches = {getattr(x, "prefetch_to", x) for x in qs._prefetch_related_lookups}
        assert "translations" in prefetches

    def test_genre_translation_get_queryset_selects_genre_and_language(self) -> None:
        qs = self.admin_translation.get_queryset(request=None)
        assert "genre" in qs.query.select_related
        assert "language" in qs.query.select_related


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
        self.use_as = GenreUseAsFactory()
        self.language = LanguageFactory()
        self.genre = GenreFactory(type="Theater", use_as=self.use_as)
        self.translation = GenreTranslationFactory(genre=self.genre, language=self.language, name="Theater")

    def test_genre_add_with_empty_translation(self) -> None:
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
        assert response.status_code == 200
        assert Genre.objects.filter(type="Concert").exists()

    def test_genre_change_partial_translation_update(self) -> None:
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
        assert response.status_code == 200
        self.translation.refresh_from_db()
        assert self.translation.name == "Updated Theater"
