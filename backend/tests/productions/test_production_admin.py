"""
Tests for apps/productions/admin.py

Covers:
- All admin classes are registered
- All admins inherit from BaseAdmin
- list_display, list_filter, search_fields, autocomplete_fields configuration
- Inline classes are present on ProductionAdmin
- Inline model, extra and autocomplete_fields attributes
- get_queryset uses select_related on ProductionAdmin
- Functional admin changelist and changeform (with superuser)
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.productions.admin import (
    ProductionAdmin,
    ProductionGenreInline,
    ProductionTagInline,
    ProductionTagTranslationInline,
    ProductionTranslationInline,
    UitDatabaseTypeAdmin,
)
from apps.productions.models import (
    Production,
    ProductionGenre,
    ProductionTag,
    ProductionTagTranslation,
    ProductionTranslation,
    UitDatabaseType,
)
from tests.factories.media_library import MediaItemFactory
from tests.factories.production import (
    ProductionFactory,
    UitDatabaseTypeFactory,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_superuser(username="admin"):
    return User.objects.create_superuser(username=username, password="password", email=f"{username}@example.com")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestAdminRegistration(TestCase):
    def test_production_is_registered(self) -> None:
        assert Production in admin.site._registry

    def test_registered_admin_is_production_admin(self) -> None:
        assert isinstance(admin.site._registry[Production], ProductionAdmin)

    def test_uit_database_type_is_registered(self) -> None:
        assert UitDatabaseType in admin.site._registry

    def test_registered_admin_is_uit_database_type_admin(self) -> None:
        assert isinstance(admin.site._registry[UitDatabaseType], UitDatabaseTypeAdmin)

    def test_production_inlines_present_on_production_admin(self) -> None:
        # Models that no longer have top-level admins should still be available
        # as inlines on the Production admin.
        inline_models = [inline.model for inline in admin.site._registry[Production].inlines]
        assert ProductionTranslation in inline_models
        assert ProductionGenre in inline_models
        assert ProductionTag in inline_models


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestAdminInheritance(TestCase):
    admins = [ProductionAdmin, UitDatabaseTypeAdmin]

    def test_all_admins_inherit_from_base_admin(self) -> None:
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                assert issubclass(admin_class, BaseAdmin)

    def test_all_admins_inherit_from_model_admin(self) -> None:
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                assert issubclass(admin_class, admin.ModelAdmin)


# ---------------------------------------------------------------------------
# UitDatabaseTypeAdmin configuration
# ---------------------------------------------------------------------------


class TestUitDatabaseTypeAdminConfiguration(TestCase):
    def setUp(self) -> None:
        self.admin = admin.site._registry[UitDatabaseType]

    def test_list_display_contains_id(self) -> None:
        assert "id" in self.admin.list_display

    def test_list_display_contains_name(self) -> None:
        assert "name" in self.admin.list_display

    def test_search_fields_contains_name(self) -> None:
        assert "name" in self.admin.search_fields


# ---------------------------------------------------------------------------
# ProductionAdmin configuration
# ---------------------------------------------------------------------------


class TestProductionAdminConfiguration(TestCase):
    def setUp(self) -> None:
        self.admin = admin.site._registry[Production]

    # list_display
    def test_list_display_contains_id(self) -> None:
        assert "id" in self.admin.list_display

    def test_list_display_contains_attendance_mode(self) -> None:
        assert "attendance_mode" in self.admin.list_display

    def test_list_display_contains_performer_type(self) -> None:
        assert "performer_type" in self.admin.list_display

    def test_list_display_does_not_contain_uit_database_theme(self) -> None:
        assert "uit_database_theme" not in self.admin.list_display

    def test_list_display_contains_uit_database_type(self) -> None:
        assert "uit_database_type" in self.admin.list_display

    # list_filter
    def test_list_filter_contains_attendance_mode(self) -> None:
        assert "attendance_mode" in self.admin.list_filter

    def test_list_filter_contains_performer_type(self) -> None:
        assert "performer_type" in self.admin.list_filter

    def test_list_filter_does_not_contain_uit_database_theme(self) -> None:
        """uit_database_theme was removed from ProductionAdmin.list_filter."""
        assert "uit_database_theme" not in self.admin.list_filter

    # search_fields
    def test_search_fields_contains_id(self) -> None:
        assert "id" in self.admin.search_fields

    def test_search_fields_contains_translations_title(self) -> None:
        assert "translations__title" in self.admin.search_fields

    # autocomplete_fields
    def test_autocomplete_fields_does_not_contain_uit_database_theme(self) -> None:
        assert "uit_database_theme" not in self.admin.autocomplete_fields

    def test_autocomplete_fields_contains_uit_database_type(self) -> None:
        assert "uit_database_type" in self.admin.autocomplete_fields

    # inlines
    def test_inlines_contains_production_translation_inline(self) -> None:
        inline_classes = [inline.model for inline in self.admin.inlines]
        assert ProductionTranslation in inline_classes

    def test_inlines_contains_production_genre_inline(self) -> None:
        inline_classes = [inline.model for inline in self.admin.inlines]
        assert ProductionGenre in inline_classes

    def test_inlines_contains_production_tag_inline(self) -> None:
        inline_classes = [inline.model for inline in self.admin.inlines]
        assert ProductionTag in inline_classes

    def test_three_inlines_registered(self) -> None:
        assert len(self.admin.inlines) == 3


class TestProductionTagTranslationInlineClass(TestCase):
    def test_model_is_production_tag_translation(self) -> None:
        assert ProductionTagTranslationInline.model == ProductionTagTranslation

    def test_extra_is_one(self) -> None:
        assert ProductionTagTranslationInline.extra == 1

    def test_autocomplete_fields_contains_language(self) -> None:
        assert "language" in ProductionTagTranslationInline.autocomplete_fields

    def test_has_collapse_class(self) -> None:
        assert "collapse" in ProductionTagTranslationInline.classes

    def test_fields_contains_language(self) -> None:
        assert "language" in ProductionTagTranslationInline.fields

    def test_fields_contains_description(self) -> None:
        assert "description" in ProductionTagTranslationInline.fields

    def test_is_tabular_inline(self) -> None:
        assert issubclass(ProductionTagTranslationInline, admin.TabularInline)


class TestProductionTagTranslationInlineGetQueryset(TestCase):
    def setUp(self) -> None:
        self.superuser = make_superuser("tag_translation_inline_admin")
        self.factory = RequestFactory()
        self.inline = ProductionTagTranslationInline(parent_model=ProductionTag, admin_site=admin.site)

    def _make_request(self):
        request = self.factory.get("/")
        request.user = self.superuser
        return request

    def test_queryset_model_is_production_tag_translation(self) -> None:
        """Inline queryset should target ProductionTagTranslation."""
        qs = self.inline.get_queryset(self._make_request())
        assert qs.model == ProductionTagTranslation

    def test_queryset_has_select_related_for_language(self) -> None:
        """Inline queryset should select_related language for efficiency."""
        qs = self.inline.get_queryset(self._make_request())
        assert "language" in qs.query.select_related


# ---------------------------------------------------------------------------
# Inline configuration
# ---------------------------------------------------------------------------


class TestProductionTranslationInline(TestCase):
    def test_model_is_production_translation(self) -> None:
        assert ProductionTranslationInline.model == ProductionTranslation

    def test_extra_is_one(self) -> None:
        assert ProductionTranslationInline.extra == 1

    def test_autocomplete_fields_contains_language(self) -> None:
        assert "language" in ProductionTranslationInline.autocomplete_fields

    def test_has_collapse_class(self) -> None:
        assert "collapse" in ProductionTranslationInline.classes

    def test_is_tabular_inline(self) -> None:
        assert issubclass(ProductionTranslationInline, admin.StackedInline)


class TestProductionGenreInline(TestCase):
    def test_model_is_production_genre(self) -> None:
        assert ProductionGenreInline.model == ProductionGenre

    def test_extra_is_one(self) -> None:
        assert ProductionGenreInline.extra == 1

    def test_is_tabular_inline(self) -> None:
        assert issubclass(ProductionGenreInline, admin.TabularInline)


class TestProductionTagInline(TestCase):
    def test_model_is_production_tag(self) -> None:
        assert ProductionTagInline.model == ProductionTag

    def test_extra_is_one(self) -> None:
        assert ProductionTagInline.extra == 1

    def test_autocomplete_fields_contains_tag(self) -> None:
        assert "tag" in ProductionTagInline.autocomplete_fields

    def test_is_tabular_inline(self) -> None:
        assert issubclass(ProductionTagInline, admin.TabularInline)


# ---------------------------------------------------------------------------
# get_queryset optimisation
# ---------------------------------------------------------------------------


class TestProductionAdminGetQueryset(TestCase):
    def setUp(self) -> None:
        self.superuser = make_superuser()
        self.factory = RequestFactory()
        self.model_admin = admin.site._registry[Production]

    def _make_request(self):
        request = self.factory.get("/")
        request.user = self.superuser
        return request

    def test_queryset_is_production_queryset(self) -> None:
        qs = self.model_admin.get_queryset(self._make_request())
        assert qs.model == Production

    def test_queryset_does_not_have_select_related_for_uit_database_theme(self) -> None:
        qs = self.model_admin.get_queryset(self._make_request())
        assert "uit_database_theme" not in qs.query.select_related

    def test_queryset_has_select_related_for_uit_database_type(self) -> None:
        qs = self.model_admin.get_queryset(self._make_request())
        assert "uit_database_type" in qs.query.select_related


class TestProductionAdminMediaItemsWidget(TestCase):
    def setUp(self) -> None:
        self.model_admin = admin.site._registry[Production]

    def test_returns_dash_without_media_gallery(self) -> None:
        production = ProductionFactory(media_gallery=None)

        assert self.model_admin.media_items_admin(production) == "-"

    def test_renders_add_button_for_empty_gallery(self) -> None:
        production = ProductionFactory()

        html = str(self.model_admin.media_items_admin(production))

        assert "No images in gallery." in html
        assert "Add image" in html
        assert f"?gallery={production.media_gallery.id}" in html

    def test_renders_item_links_and_add_button_for_non_empty_gallery(self) -> None:
        production = ProductionFactory()
        media_item = MediaItemFactory(gallery=production.media_gallery, original_filename="hero.jpg")

        html = str(self.model_admin.media_items_admin(production))

        assert "hero.jpg" in html
        assert f"/admin/media_library/mediaitem/{media_item.id}/change/" in html
        assert "Add image to gallery" in html


# ---------------------------------------------------------------------------
# Functional changelist / changeform tests
# ---------------------------------------------------------------------------


class TestUitDatabaseTypeAdminChangelist(TestCase):
    def setUp(self) -> None:
        self.superuser = make_superuser("type_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self) -> None:
        url = reverse("admin:productions_uitdatabasetype_changelist")
        assert self.client.get(url).status_code == 200

    def test_changelist_shows_type(self) -> None:
        UitDatabaseTypeFactory.create(name="Concert")
        url = reverse("admin:productions_uitdatabasetype_changelist")
        self.assertContains(self.client.get(url), "Concert")

    def test_changeform_returns_200(self) -> None:
        db_type = UitDatabaseTypeFactory.create(name="Test Type")
        url = reverse("admin:productions_uitdatabasetype_change", args=[db_type.pk])
        assert self.client.get(url).status_code == 200


class TestProductionAdminChangelist(TestCase):
    def setUp(self) -> None:
        self.superuser = make_superuser("prod_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self) -> None:
        url = reverse("admin:productions_production_changelist")
        assert self.client.get(url).status_code == 200

    def test_changelist_with_production(self) -> None:
        ProductionFactory.create()
        url = reverse("admin:productions_production_changelist")
        assert self.client.get(url).status_code == 200

    def test_changeform_returns_200(self) -> None:
        production = ProductionFactory.create()
        url = reverse("admin:productions_production_change", args=[production.pk])
        assert self.client.get(url).status_code == 200

    def test_changelist_filter_by_attendance_mode(self) -> None:
        ProductionFactory.create(attendance_mode="offline")
        url = reverse("admin:productions_production_changelist")
        assert self.client.get(url, {"attendance_mode": "offline"}).status_code == 200

    def test_changelist_filter_by_performer_type(self) -> None:
        ProductionFactory.create(performer_type="solo")
        url = reverse("admin:productions_production_changelist")
        assert self.client.get(url, {"performer_type": "solo"}).status_code == 200

    def test_changelist_search(self) -> None:
        url = reverse("admin:productions_production_changelist")
        assert self.client.get(url, {"q": "test"}).status_code == 200
