"""
Tests for apps/productions/admin.py

Covers:
- All admin classes are registered (Production, ProductionTranslation,
  UitDatabaseTheme, UitDatabaseType, ProductionGenre, ProductionTag)
- All admins inherit from BaseAdmin
- list_display configuration for every admin
- list_filter configuration for relevant admins
- search_fields configuration for every admin
- autocomplete_fields configuration for every admin
- Inline classes are present on ProductionAdmin (translation, genre, tag)
- Inline model, extra and autocomplete_fields attributes
- get_queryset uses select_related on ProductionAdmin
- Functional admin changelist and changeform (with superuser)
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.productions.admin import (
    ProductionAdmin,
    ProductionGenreAdmin,
    ProductionGenreInline,
    ProductionTagAdmin,
    ProductionTagInline,
    ProductionTranslationAdmin,
    ProductionTranslationInline,
    UitDatabaseThemeAdmin,
    UitDatabaseTypeAdmin,
)
from apps.productions.models import (
    Production,
    ProductionGenre,
    ProductionTag,
    ProductionTranslation,
    UitDatabaseTheme,
    UitDatabaseType,
)
from tests.factories.language import LanguageFactory
from tests.factories.production import (
    ProductionFactory,
    ProductionTagFactory,
    ProductionTranslationFactory,
    UitDatabaseThemeFactory,
    UitDatabaseTypeFactory,
)
from tests.factories.tag import TagFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_superuser(username="admin"):
    return User.objects.create_superuser(
        username=username, password="password", email=f"{username}@example.com"
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestAdminRegistration(TestCase):
    """Verify all admin classes are registered against their models."""

    def test_production_is_registered(self):
        self.assertIn(Production, admin.site._registry)

    def test_registered_admin_is_production_admin(self):
        self.assertIsInstance(admin.site._registry[Production], ProductionAdmin)

    def test_production_translation_is_registered(self):
        self.assertIn(ProductionTranslation, admin.site._registry)

    def test_registered_admin_is_production_translation_admin(self):
        self.assertIsInstance(
            admin.site._registry[ProductionTranslation], ProductionTranslationAdmin
        )

    def test_uit_database_theme_is_registered(self):
        self.assertIn(UitDatabaseTheme, admin.site._registry)

    def test_registered_admin_is_uit_database_theme_admin(self):
        self.assertIsInstance(
            admin.site._registry[UitDatabaseTheme], UitDatabaseThemeAdmin
        )

    def test_uit_database_type_is_registered(self):
        self.assertIn(UitDatabaseType, admin.site._registry)

    def test_registered_admin_is_uit_database_type_admin(self):
        self.assertIsInstance(
            admin.site._registry[UitDatabaseType], UitDatabaseTypeAdmin
        )

    def test_production_genre_is_registered(self):
        self.assertIn(ProductionGenre, admin.site._registry)

    def test_registered_admin_is_production_genre_admin(self):
        self.assertIsInstance(
            admin.site._registry[ProductionGenre], ProductionGenreAdmin
        )

    def test_production_tag_is_registered(self):
        self.assertIn(ProductionTag, admin.site._registry)

    def test_registered_admin_is_production_tag_admin(self):
        self.assertIsInstance(admin.site._registry[ProductionTag], ProductionTagAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestAdminInheritance(TestCase):
    """All admin classes must extend BaseAdmin (and therefore ModelAdmin)."""

    admins = [
        ProductionAdmin,
        ProductionTranslationAdmin,
        UitDatabaseThemeAdmin,
        UitDatabaseTypeAdmin,
        ProductionGenreAdmin,
        ProductionTagAdmin,
    ]

    def test_all_admins_inherit_from_base_admin(self):
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                self.assertTrue(issubclass(admin_class, BaseAdmin))

    def test_all_admins_inherit_from_model_admin(self):
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                self.assertTrue(issubclass(admin_class, admin.ModelAdmin))


# ---------------------------------------------------------------------------
# UitDatabaseThemeAdmin configuration
# ---------------------------------------------------------------------------


class TestUitDatabaseThemeAdminConfiguration(TestCase):
    """Tests for UitDatabaseThemeAdmin meta configuration."""

    def setUp(self):
        self.admin = admin.site._registry[UitDatabaseTheme]

    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_name(self):
        self.assertIn("name", self.admin.list_display)

    def test_search_fields_contains_name(self):
        self.assertIn("name", self.admin.search_fields)


# ---------------------------------------------------------------------------
# UitDatabaseTypeAdmin configuration
# ---------------------------------------------------------------------------


class TestUitDatabaseTypeAdminConfiguration(TestCase):
    """Tests for UitDatabaseTypeAdmin meta configuration."""

    def setUp(self):
        self.admin = admin.site._registry[UitDatabaseType]

    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_name(self):
        self.assertIn("name", self.admin.list_display)

    def test_search_fields_contains_name(self):
        self.assertIn("name", self.admin.search_fields)


# ---------------------------------------------------------------------------
# ProductionAdmin configuration
# ---------------------------------------------------------------------------


class TestProductionAdminConfiguration(TestCase):
    """Tests for individual meta configuration of ProductionAdmin."""

    def setUp(self):
        self.admin = admin.site._registry[Production]

    # list_display
    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_attendance_mode(self):
        self.assertIn("attendance_mode", self.admin.list_display)

    def test_list_display_contains_performer_type(self):
        self.assertIn("performer_type", self.admin.list_display)

    def test_list_display_contains_uit_database_theme(self):
        self.assertIn("uit_database_theme", self.admin.list_display)

    def test_list_display_contains_uit_database_type(self):
        self.assertIn("uit_database_type", self.admin.list_display)

    # list_filter
    def test_list_filter_contains_attendance_mode(self):
        self.assertIn("attendance_mode", self.admin.list_filter)

    def test_list_filter_contains_performer_type(self):
        self.assertIn("performer_type", self.admin.list_filter)

    def test_list_filter_contains_uit_database_theme(self):
        self.assertIn("uit_database_theme", self.admin.list_filter)

    def test_list_filter_contains_uit_database_type(self):
        self.assertIn("uit_database_type", self.admin.list_filter)

    # search_fields
    def test_search_fields_contains_id(self):
        self.assertIn("id", self.admin.search_fields)

    def test_search_fields_contains_translations_title(self):
        self.assertIn("translations__title", self.admin.search_fields)

    def test_search_fields_contains_translations_artist_name(self):
        self.assertIn("translations__artist_name", self.admin.search_fields)

    # autocomplete_fields
    def test_autocomplete_fields_contains_uit_database_theme(self):
        self.assertIn("uit_database_theme", self.admin.autocomplete_fields)

    def test_autocomplete_fields_contains_uit_database_type(self):
        self.assertIn("uit_database_type", self.admin.autocomplete_fields)

    # inlines
    def test_inlines_contains_production_translation_inline(self):
        inline_classes = [inline.model for inline in self.admin.inlines]
        self.assertIn(ProductionTranslation, inline_classes)

    def test_inlines_contains_production_genre_inline(self):
        inline_classes = [inline.model for inline in self.admin.inlines]
        self.assertIn(ProductionGenre, inline_classes)

    def test_inlines_contains_production_tag_inline(self):
        inline_classes = [inline.model for inline in self.admin.inlines]
        self.assertIn(ProductionTag, inline_classes)

    def test_three_inlines_registered(self):
        self.assertEqual(len(self.admin.inlines), 3)


# ---------------------------------------------------------------------------
# ProductionTranslationAdmin configuration
# ---------------------------------------------------------------------------


class TestProductionTranslationAdminConfiguration(TestCase):
    """Tests for individual meta configuration of ProductionTranslationAdmin."""

    def setUp(self):
        self.admin = admin.site._registry[ProductionTranslation]

    # list_display
    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_production(self):
        self.assertIn("production", self.admin.list_display)

    def test_list_display_contains_language(self):
        self.assertIn("language", self.admin.list_display)

    def test_list_display_contains_title(self):
        self.assertIn("title", self.admin.list_display)

    def test_list_display_contains_artist_name(self):
        self.assertIn("artist_name", self.admin.list_display)

    # list_filter
    def test_list_filter_contains_language(self):
        self.assertIn("language", self.admin.list_filter)

    # search_fields
    def test_search_fields_contains_title(self):
        self.assertIn("title", self.admin.search_fields)

    def test_search_fields_contains_artist_name(self):
        self.assertIn("artist_name", self.admin.search_fields)

    def test_search_fields_contains_production_id(self):
        self.assertIn("production__id", self.admin.search_fields)

    # autocomplete_fields
    def test_autocomplete_fields_contains_production(self):
        self.assertIn("production", self.admin.autocomplete_fields)

    def test_autocomplete_fields_contains_language(self):
        self.assertIn("language", self.admin.autocomplete_fields)


# ---------------------------------------------------------------------------
# ProductionGenreAdmin configuration
# ---------------------------------------------------------------------------


class TestProductionGenreAdminConfiguration(TestCase):
    """Tests for individual meta configuration of ProductionGenreAdmin."""

    def setUp(self):
        self.admin = admin.site._registry[ProductionGenre]

    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_production(self):
        self.assertIn("production", self.admin.list_display)

    def test_list_display_contains_genre(self):
        self.assertIn("genre", self.admin.list_display)

    def test_list_display_contains_position(self):
        self.assertIn("position", self.admin.list_display)

    def test_autocomplete_fields_contains_production(self):
        self.assertIn("production", self.admin.autocomplete_fields)


# ---------------------------------------------------------------------------
# ProductionTagAdmin configuration
# ---------------------------------------------------------------------------


class TestProductionTagAdminConfiguration(TestCase):
    """Tests for individual meta configuration of ProductionTagAdmin."""

    def setUp(self):
        self.admin = admin.site._registry[ProductionTag]

    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_production(self):
        self.assertIn("production", self.admin.list_display)

    def test_list_display_contains_tag(self):
        self.assertIn("tag", self.admin.list_display)

    def test_autocomplete_fields_contains_production(self):
        self.assertIn("production", self.admin.autocomplete_fields)

    def test_autocomplete_fields_contains_tag(self):
        self.assertIn("tag", self.admin.autocomplete_fields)


# ---------------------------------------------------------------------------
# Inline configuration
# ---------------------------------------------------------------------------


class TestProductionTranslationInline(TestCase):
    """Tests for ProductionTranslationInline configuration."""

    def test_model_is_production_translation(self):
        self.assertEqual(ProductionTranslationInline.model, ProductionTranslation)

    def test_extra_is_one(self):
        self.assertEqual(ProductionTranslationInline.extra, 1)

    def test_autocomplete_fields_contains_language(self):
        self.assertIn("language", ProductionTranslationInline.autocomplete_fields)

    def test_has_collapse_class(self):
        self.assertIn("collapse", ProductionTranslationInline.classes)

    def test_is_tabular_inline(self):
        self.assertTrue(issubclass(ProductionTranslationInline, admin.TabularInline))


class TestProductionGenreInline(TestCase):
    """Tests for ProductionGenreInline configuration."""

    def test_model_is_production_genre(self):
        self.assertEqual(ProductionGenreInline.model, ProductionGenre)

    def test_extra_is_one(self):
        self.assertEqual(ProductionGenreInline.extra, 1)

    def test_is_tabular_inline(self):
        self.assertTrue(issubclass(ProductionGenreInline, admin.TabularInline))


class TestProductionTagInline(TestCase):
    """Tests for ProductionTagInline configuration."""

    def test_model_is_production_tag(self):
        self.assertEqual(ProductionTagInline.model, ProductionTag)

    def test_extra_is_one(self):
        self.assertEqual(ProductionTagInline.extra, 1)

    def test_autocomplete_fields_contains_tag(self):
        self.assertIn("tag", ProductionTagInline.autocomplete_fields)

    def test_is_tabular_inline(self):
        self.assertTrue(issubclass(ProductionTagInline, admin.TabularInline))


# ---------------------------------------------------------------------------
# get_queryset optimisation
# ---------------------------------------------------------------------------


class TestProductionAdminGetQueryset(TestCase):
    """Verify get_queryset uses select_related for FK optimisation."""

    def setUp(self):
        self.superuser = make_superuser()
        self.factory = RequestFactory()
        self.model_admin = admin.site._registry[Production]

    def _make_request(self):
        request = self.factory.get("/")
        request.user = self.superuser
        return request

    def test_queryset_is_production_queryset(self):
        qs = self.model_admin.get_queryset(self._make_request())
        self.assertEqual(qs.model, Production)

    def test_queryset_has_select_related_for_uit_database_theme(self):
        qs = self.model_admin.get_queryset(self._make_request())
        self.assertIn("uit_database_theme", qs.query.select_related)

    def test_queryset_has_select_related_for_uit_database_type(self):
        qs = self.model_admin.get_queryset(self._make_request())
        self.assertIn("uit_database_type", qs.query.select_related)


# ---------------------------------------------------------------------------
# Functional changelist tests  (HTTP, requires superuser login)
# ---------------------------------------------------------------------------


class TestUitDatabaseThemeAdminChangelist(TestCase):
    """Functional tests for UitDatabaseThemeAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("theme_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self):
        url = reverse("admin:productions_uitdatabasetheme_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_changelist_shows_theme(self):
        UitDatabaseThemeFactory.create(name="Jazz Night")
        url = reverse("admin:productions_uitdatabasetheme_changelist")
        response = self.client.get(url)
        self.assertContains(response, "Jazz Night")

    def test_changeform_returns_200(self):
        theme = UitDatabaseThemeFactory.create(name="Test Theme")
        url = reverse("admin:productions_uitdatabasetheme_change", args=[theme.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TestUitDatabaseTypeAdminChangelist(TestCase):
    """Functional tests for UitDatabaseTypeAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("type_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self):
        url = reverse("admin:productions_uitdatabasetype_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_changelist_shows_type(self):
        UitDatabaseTypeFactory.create(name="Concert")
        url = reverse("admin:productions_uitdatabasetype_changelist")
        response = self.client.get(url)
        self.assertContains(response, "Concert")

    def test_changeform_returns_200(self):
        db_type = UitDatabaseTypeFactory.create(name="Test Type")
        url = reverse("admin:productions_uitdatabasetype_change", args=[db_type.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TestProductionAdminChangelist(TestCase):
    """Functional tests for ProductionAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("prod_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self):
        url = reverse("admin:productions_production_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_changelist_with_production(self):
        ProductionFactory.create()
        url = reverse("admin:productions_production_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_changeform_returns_200(self):
        production = ProductionFactory.create()
        url = reverse("admin:productions_production_change", args=[production.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_changelist_filter_by_attendance_mode(self):
        ProductionFactory.create(attendance_mode="offline")
        url = reverse("admin:productions_production_changelist")
        response = self.client.get(url, {"attendance_mode": "offline"})
        self.assertEqual(response.status_code, 200)

    def test_changelist_filter_by_performer_type(self):
        ProductionFactory.create(performer_type="solo")
        url = reverse("admin:productions_production_changelist")
        response = self.client.get(url, {"performer_type": "solo"})
        self.assertEqual(response.status_code, 200)

    def test_changelist_search(self):
        url = reverse("admin:productions_production_changelist")
        response = self.client.get(url, {"q": "test"})
        self.assertEqual(response.status_code, 200)


class TestProductionTranslationAdminChangelist(TestCase):
    """Functional tests for ProductionTranslationAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("trans_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self):
        url = reverse("admin:productions_productiontranslation_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_changeform_returns_200(self):
        production = ProductionFactory.create()
        language = LanguageFactory.create(code="en", name="English")
        translation = ProductionTranslationFactory.create(
            production=production,
            language=language,
            title="Test Title",
        )
        url = reverse(
            "admin:productions_productiontranslation_change", args=[translation.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_changelist_shows_translation_title(self):
        production = ProductionFactory.create()
        language = LanguageFactory.create(code="en", name="English")
        ProductionTranslationFactory.create(
            production=production,
            language=language,
            title="Visible Title",
        )
        url = reverse("admin:productions_productiontranslation_changelist")
        response = self.client.get(url)
        self.assertContains(response, "Visible Title")

    def test_changelist_filter_by_language(self):
        url = reverse("admin:productions_productiontranslation_changelist")
        response = self.client.get(url, {"language__code": "en"})
        self.assertEqual(response.status_code, 200)


class TestProductionGenreAdminChangelist(TestCase):
    """Functional tests for ProductionGenreAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("genre_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self):
        url = reverse("admin:productions_productiongenre_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TestProductionTagAdminChangelist(TestCase):
    """Functional tests for ProductionTagAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("tag_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self):
        url = reverse("admin:productions_productiontag_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_changeform_returns_200(self):
        production = ProductionFactory.create()
        tag = TagFactory.create()
        production_tag = ProductionTagFactory.create(production=production, tag=tag)
        url = reverse(
            "admin:productions_productiontag_change", args=[production_tag.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
