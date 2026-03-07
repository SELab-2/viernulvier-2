"""
Tests for apps/languages/admin.py

Covers:
- LanguageAdmin is registered
- list_display configuration
- list_filter configuration
- search_fields configuration
- ordering configuration
- Inherits from BaseAdmin
- Functional admin changelist and changeform (with superuser)
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.languages.admin import LanguageAdmin
from apps.languages.models import Language
from tests.factories.language import LanguageFactory


class TestLanguageAdminRegistration(TestCase):
    """Verify LanguageAdmin is registered with the default admin site."""

    def test_language_is_registered(self):
        self.assertIn(Language, admin.site._registry)

    def test_registered_admin_is_language_admin(self):
        registered = admin.site._registry[Language]
        self.assertIsInstance(registered, LanguageAdmin)


class TestLanguageAdminInheritance(TestCase):
    """LanguageAdmin must extend BaseAdmin."""

    def test_inherits_from_base_admin(self):
        self.assertTrue(issubclass(LanguageAdmin, BaseAdmin))

    def test_inherits_from_model_admin(self):
        self.assertTrue(issubclass(LanguageAdmin, admin.ModelAdmin))


class TestLanguageAdminConfiguration(TestCase):
    """Tests for individual meta configuration of LanguageAdmin."""

    def setUp(self):
        self.admin = LanguageAdmin(Language, admin.site)

    # -- list_display ---------------------------------------------------------

    def test_list_display_contains_code(self):
        self.assertIn("code", self.admin.list_display)

    def test_list_display_contains_name(self):
        self.assertIn("name", self.admin.list_display)

    def test_list_display_contains_is_active(self):
        self.assertIn("is_active", self.admin.list_display)

    def test_list_display_is_tuple_or_list(self):
        self.assertIsInstance(self.admin.list_display, (tuple, list))

    def test_list_display_has_at_least_three_fields(self):
        self.assertGreaterEqual(len(self.admin.list_display), 3)

    # -- list_filter ----------------------------------------------------------

    def test_list_filter_contains_is_active(self):
        self.assertIn("is_active", self.admin.list_filter)

    def test_list_filter_is_tuple_or_list(self):
        self.assertIsInstance(self.admin.list_filter, (tuple, list))

    # -- search_fields --------------------------------------------------------

    def test_search_fields_contains_code(self):
        self.assertIn("code", self.admin.search_fields)

    def test_search_fields_contains_name(self):
        self.assertIn("name", self.admin.search_fields)

    def test_search_fields_is_tuple_or_list(self):
        self.assertIsInstance(self.admin.search_fields, (tuple, list))

    # -- ordering -------------------------------------------------------------

    def test_ordering_is_set(self):
        self.assertIsNotNone(self.admin.ordering)
        self.assertTrue(len(self.admin.ordering) > 0)

    def test_ordering_contains_code(self):
        self.assertIn("code", self.admin.ordering)


class TestLanguageAdminFunctional(TestCase):
    """Functional admin tests using Django's test client."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", password="password", email="admin@example.com"
        )
        self.client.force_login(self.superuser)
        LanguageFactory(code="nl", name="Dutch", is_active=True)
        LanguageFactory(code="en", name="English", is_active=False)

    # -- Changelist -----------------------------------------------------------

    def test_changelist_returns_200(self):
        url = reverse("admin:languages_language_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_changelist_shows_all_languages(self):
        url = reverse("admin:languages_language_changelist")
        response = self.client.get(url)
        self.assertContains(response, "nl")
        self.assertContains(response, "en")

    def test_changelist_search_by_code(self):
        url = reverse("admin:languages_language_changelist")
        response = self.client.get(url, {"q": "nl"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dutch")

    def test_changelist_search_by_name(self):
        url = reverse("admin:languages_language_changelist")
        response = self.client.get(url, {"q": "English"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "en")

    def test_changelist_filter_active(self):
        url = reverse("admin:languages_language_changelist")
        response = self.client.get(url, {"is_active__exact": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dutch")

    def test_changelist_filter_inactive(self):
        url = reverse("admin:languages_language_changelist")
        response = self.client.get(url, {"is_active__exact": "0"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "English")

    # -- Change form ----------------------------------------------------------

    def test_change_form_returns_200(self):
        lang = Language.objects.get(code="nl")
        url = reverse("admin:languages_language_change", args=[lang.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_change_form_shows_language_data(self):
        lang = Language.objects.get(code="nl")
        url = reverse("admin:languages_language_change", args=[lang.pk])
        response = self.client.get(url)
        self.assertContains(response, "nl")

    # -- Add form -------------------------------------------------------------

    def test_add_form_returns_200(self):
        url = reverse("admin:languages_language_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_language_via_admin(self):
        url = reverse("admin:languages_language_add")
        response = self.client.post(
            url,
            {"code": "de", "name": "German", "is_active": True},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Language.objects.filter(code="de").exists())

    # -- Delete ---------------------------------------------------------------

    def test_delete_language_via_admin(self):
        lang = Language.objects.get(code="en")
        url = reverse("admin:languages_language_delete", args=[lang.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Language.objects.filter(code="en").exists())

    # -- Permissions ----------------------------------------------------------

    def test_anonymous_user_redirected_from_changelist(self):
        self.client.logout()
        url = reverse("admin:languages_language_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
