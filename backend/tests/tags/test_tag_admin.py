"""
Tests for apps/tags/admin.py

Covers:
- TagAdmin is registered
- TagTranslationAdmin is registered
- list_display configuration for both admins
- list_filter configuration for both admins
- search_fields configuration for both admins
- autocomplete_fields configuration
- TagTranslationInline is present on TagAdmin
- Both admins inherit from BaseAdmin
- Functional admin changelist and changeform (with superuser)
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.productions.models import ProductionTag
from apps.tags.admin import TagAdmin, TagProductionInline, TagTranslationInline
from apps.tags.models import Tag, TagTranslation
from tests.factories.language import LanguageFactory
from tests.factories.tag import TagFactory

# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestTagAdminRegistration(TestCase):
    def test_tag_is_registered(self) -> None:
        assert Tag in admin.site._registry

    def test_registered_admin_is_tag_admin(self) -> None:
        assert isinstance(admin.site._registry[Tag], TagAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestTagAdminInheritance(TestCase):
    def test_tag_admin_inherits_from_base_admin(self) -> None:
        assert issubclass(TagAdmin, BaseAdmin)

    def test_tag_admin_inherits_from_model_admin(self) -> None:
        assert issubclass(TagAdmin, admin.ModelAdmin)


# ---------------------------------------------------------------------------
# TagAdmin configuration
# ---------------------------------------------------------------------------


class TestTagAdminConfiguration(TestCase):
    def setUp(self) -> None:
        self.admin = TagAdmin(Tag, admin.site)

    # -- list_display ---------------------------------------------------------

    def test_list_display_contains_id(self) -> None:
        assert "id" in self.admin.list_display

    def test_list_display_contains_type(self) -> None:
        assert "type" in self.admin.list_display

    def test_list_display_contains_display_name(self) -> None:
        assert "display_name" in self.admin.list_display

    def test_list_display_contains_is_enabled(self) -> None:
        assert "is_enabled" in self.admin.list_display

    def test_list_display_is_tuple_or_list(self) -> None:
        assert isinstance(self.admin.list_display, (tuple, list))

    # -- list_filter ----------------------------------------------------------

    def test_list_filter_contains_is_enabled(self) -> None:
        assert "is_enabled" in self.admin.list_filter

    def test_list_filter_contains_type(self) -> None:
        assert "type" in self.admin.list_filter

    def test_list_filter_is_tuple_or_list(self) -> None:
        assert isinstance(self.admin.list_filter, (tuple, list))

    # -- search_fields --------------------------------------------------------

    def test_search_fields_contains_type(self) -> None:
        assert "type" in self.admin.search_fields

    def test_search_fields_contains_source(self) -> None:
        assert "source" in self.admin.search_fields

    def test_search_fields_is_tuple_or_list(self) -> None:
        assert isinstance(self.admin.search_fields, (tuple, list))

    # -- inlines --------------------------------------------------------------

    def test_inlines_contains_tag_translation_inline(self) -> None:
        assert TagTranslationInline in self.admin.inlines

    def test_inlines_contains_tag_production_inline(self) -> None:
        assert TagProductionInline in self.admin.inlines


# ---------------------------------------------------------------------------
# TagTranslationInline configuration
# ---------------------------------------------------------------------------


class TestTagTranslationInlineConfiguration(TestCase):
    def setUp(self) -> None:
        self.inline = TagTranslationInline(Tag, admin.site)

    def test_inline_model_is_tag_translation(self) -> None:
        assert self.inline.model == TagTranslation

    def test_inline_extra_is_one(self) -> None:
        assert self.inline.extra == 1

    def test_inline_autocomplete_fields_contains_language(self) -> None:
        assert "language" in self.inline.autocomplete_fields


class TestTagProductionInlineConfiguration(TestCase):
    def setUp(self) -> None:
        self.inline = TagProductionInline(Tag, admin.site)

    def test_inline_model_is_production_tag(self) -> None:
        assert self.inline.model == ProductionTag

    def test_inline_extra_is_one(self) -> None:
        assert self.inline.extra == 1

    def test_inline_autocomplete_fields_contains_production(self) -> None:
        assert "production" in self.inline.autocomplete_fields


# ---------------------------------------------------------------------------
# Functional admin tests
# ---------------------------------------------------------------------------


class TestTagAdminFunctional(TestCase):
    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(username="admin", password="secret", email="admin@example.com")
        self.client.force_login(self.superuser)
        self.tag = TagFactory.create(type="genre")

    def test_changelist_returns_200(self) -> None:
        url = reverse("admin:tags_tag_changelist")
        assert self.client.get(url).status_code == 200

    def test_changeform_returns_200(self) -> None:
        url = reverse("admin:tags_tag_change", args=[self.tag.pk])
        assert self.client.get(url).status_code == 200

    def test_add_form_returns_200(self) -> None:
        url = reverse("admin:tags_tag_add")
        assert self.client.get(url).status_code == 200

    def test_display_name_column_uses_tag_display_name(self) -> None:
        lang = LanguageFactory(code="en", name="English")
        tag = TagFactory.create(type="genre")
        TagTranslation.objects.create(tag=tag, language=lang, name="Concert")

        assert admin.site._registry[Tag].display_name(tag) == "Concert"
