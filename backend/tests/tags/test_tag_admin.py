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
from apps.tags.admin import TagAdmin, TagTranslationAdmin, TagTranslationInline
from apps.tags.models import Tag, TagTranslation
from tests.factories.language import LanguageFactory
from tests.factories.tag import TagFactory, TagTranslationFactory

# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestTagAdminRegistration(TestCase):
    def test_tag_is_registered(self) -> None:
        assert Tag in admin.site._registry

    def test_registered_admin_is_tag_admin(self) -> None:
        assert isinstance(admin.site._registry[Tag], TagAdmin)

    def test_tag_translation_is_registered(self) -> None:
        assert TagTranslation in admin.site._registry

    def test_registered_admin_is_tag_translation_admin(self) -> None:
        assert isinstance(admin.site._registry[TagTranslation], TagTranslationAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestTagAdminInheritance(TestCase):
    def test_tag_admin_inherits_from_base_admin(self) -> None:
        assert issubclass(TagAdmin, BaseAdmin)

    def test_tag_admin_inherits_from_model_admin(self) -> None:
        assert issubclass(TagAdmin, admin.ModelAdmin)

    def test_tag_translation_admin_inherits_from_base_admin(self) -> None:
        assert issubclass(TagTranslationAdmin, BaseAdmin)

    def test_tag_translation_admin_inherits_from_model_admin(self) -> None:
        assert issubclass(TagTranslationAdmin, admin.ModelAdmin)


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


# ---------------------------------------------------------------------------
# TagTranslationAdmin configuration
# ---------------------------------------------------------------------------


class TestTagTranslationAdminConfiguration(TestCase):
    def setUp(self) -> None:
        self.admin = TagTranslationAdmin(TagTranslation, admin.site)

    # -- list_display ---------------------------------------------------------

    def test_list_display_contains_id(self) -> None:
        assert "id" in self.admin.list_display

    def test_list_display_contains_tag(self) -> None:
        assert "tag" in self.admin.list_display

    def test_list_display_contains_language(self) -> None:
        assert "language" in self.admin.list_display

    def test_list_display_contains_name(self) -> None:
        assert "name" in self.admin.list_display

    def test_list_display_is_tuple_or_list(self) -> None:
        assert isinstance(self.admin.list_display, (tuple, list))

    # -- list_filter ----------------------------------------------------------

    def test_list_filter_contains_language_code(self) -> None:
        """list_filter must use 'language__code', not plain 'language'."""
        assert "language__code" in self.admin.list_filter

    def test_list_filter_does_not_contain_plain_language(self) -> None:
        """plain 'language' was replaced by 'language__code'."""
        assert "language" not in self.admin.list_filter

    # -- search_fields --------------------------------------------------------

    def test_search_fields_contains_name(self) -> None:
        assert "name" in self.admin.search_fields

    def test_search_fields_contains_tag_type(self) -> None:
        assert "tag__type" in self.admin.search_fields

    # -- autocomplete_fields --------------------------------------------------

    def test_autocomplete_fields_contains_tag(self) -> None:
        assert "tag" in self.admin.autocomplete_fields

    def test_autocomplete_fields_contains_language(self) -> None:
        assert "language" in self.admin.autocomplete_fields


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


class TestTagTranslationAdminFunctional(TestCase):
    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(username="admin", password="secret", email="admin@example.com")
        self.client.force_login(self.superuser)
        self.lang = LanguageFactory.create(code="nl", name="Dutch")
        self.tag = TagFactory.create(type="genre")
        self.translation = TagTranslationFactory.create(tag=self.tag, language=self.lang, name="Genre", url_title="genre")

    def test_changelist_returns_200(self) -> None:
        url = reverse("admin:tags_tagtranslation_changelist")
        assert self.client.get(url).status_code == 200

    def test_changeform_returns_200(self) -> None:
        url = reverse("admin:tags_tagtranslation_change", args=[self.translation.pk])
        assert self.client.get(url).status_code == 200

    def test_changelist_filter_by_language_code(self) -> None:
        """Changelist filter must use language__code lookup."""
        url = reverse("admin:tags_tagtranslation_changelist")
        assert self.client.get(url, {"language__code": "nl"}).status_code == 200
