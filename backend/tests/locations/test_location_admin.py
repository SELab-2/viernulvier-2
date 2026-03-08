"""
Tests for apps/locations/admin.py

Covers:
- Admin registrations for Location, Space, Hall and their translations
- Inheritance from BaseAdmin
- Config settings (list_display, filters, search, ordering, inlines)
- Basic functional flows for changelist/add/change/delete
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.locations.admin import (
    HallAdmin,
    HallTranslationAdmin,
    HallTranslationInline,
    LocationAdmin,
    LocationTranslationAdmin,
    LocationTranslationInline,
    SpaceAdmin,
    SpaceTranslationAdmin,
    SpaceTranslationInline,
)
from apps.locations.models import (
    Hall,
    HallTranslation,
    Location,
    LocationTranslation,
    Space,
    SpaceTranslation,
)
from tests.factories.language import LanguageFactory
from tests.factories.location import (
    HallFactory,
    HallTranslationFactory,
    LocationFactory,
    LocationTranslationFactory,
    SpaceFactory,
    SpaceTranslationFactory,
)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestLocationAdminRegistration(TestCase):
    """Verify location-related admins are registered on the default site."""

    def test_location_registered(self):
        self.assertIn(Location, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Location], LocationAdmin)

    def test_location_translation_registered(self):
        self.assertIn(LocationTranslation, admin.site._registry)
        self.assertIsInstance(
            admin.site._registry[LocationTranslation], LocationTranslationAdmin
        )

    def test_space_registered(self):
        self.assertIn(Space, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Space], SpaceAdmin)

    def test_space_translation_registered(self):
        self.assertIn(SpaceTranslation, admin.site._registry)
        self.assertIsInstance(
            admin.site._registry[SpaceTranslation], SpaceTranslationAdmin
        )

    def test_hall_registered(self):
        self.assertIn(Hall, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Hall], HallAdmin)

    def test_hall_translation_registered(self):
        self.assertIn(HallTranslation, admin.site._registry)
        self.assertIsInstance(
            admin.site._registry[HallTranslation], HallTranslationAdmin
        )


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestLocationAdminInheritance(TestCase):
    """Ensure admin classes inherit from BaseAdmin/ModelAdmin."""

    def test_location_inherits(self):
        self.assertTrue(issubclass(LocationAdmin, BaseAdmin))
        self.assertTrue(issubclass(LocationAdmin, admin.ModelAdmin))

    def test_location_translation_inherits(self):
        self.assertTrue(issubclass(LocationTranslationAdmin, BaseAdmin))
        self.assertTrue(issubclass(LocationTranslationAdmin, admin.ModelAdmin))

    def test_space_inherits(self):
        self.assertTrue(issubclass(SpaceAdmin, BaseAdmin))
        self.assertTrue(issubclass(SpaceAdmin, admin.ModelAdmin))

    def test_space_translation_inherits(self):
        self.assertTrue(issubclass(SpaceTranslationAdmin, BaseAdmin))
        self.assertTrue(issubclass(SpaceTranslationAdmin, admin.ModelAdmin))

    def test_hall_inherits(self):
        self.assertTrue(issubclass(HallAdmin, BaseAdmin))
        self.assertTrue(issubclass(HallAdmin, admin.ModelAdmin))

    def test_hall_translation_inherits(self):
        self.assertTrue(issubclass(HallTranslationAdmin, BaseAdmin))
        self.assertTrue(issubclass(HallTranslationAdmin, admin.ModelAdmin))


# ---------------------------------------------------------------------------
# Config checks
# ---------------------------------------------------------------------------


class TestLocationAdminConfig(TestCase):
    def setUp(self):
        self.admin = LocationAdmin(Location, admin.site)

    def test_list_display(self):
        for field in ("id", "city", "street", "number", "country", "is_own_location"):
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self):
        self.assertIn("is_own_location", self.admin.list_filter)

    def test_search_fields(self):
        for field in ("city", "street", "country"):
            self.assertIn(field, self.admin.search_fields)

    def test_inlines(self):
        self.assertIn(LocationTranslationInline, self.admin.inlines)


class TestLocationTranslationInlineConfig(TestCase):
    def setUp(self):
        self.inline = LocationTranslationInline(Location, admin.site)

    def test_model(self):
        self.assertIs(self.inline.model, LocationTranslation)

    def test_fields(self):
        self.assertEqual(tuple(self.inline.fields), ("language", "name"))

    def test_autocomplete_fields(self):
        self.assertIn("language", self.inline.autocomplete_fields)

    def test_extra(self):
        self.assertEqual(self.inline.extra, 1)


class TestLocationTranslationAdminConfig(TestCase):
    def setUp(self):
        self.admin = LocationTranslationAdmin(LocationTranslation, admin.site)

    def test_list_display(self):
        for field in ("id", "language", "location", "name"):
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self):
        self.assertIn("language", self.admin.list_filter)
        self.assertIn("location", self.admin.list_filter)

    def test_search_fields(self):
        self.assertIn("name", self.admin.search_fields)


class TestSpaceAdminConfig(TestCase):
    def setUp(self):
        self.admin = SpaceAdmin(Space, admin.site)

    def test_list_display(self):
        self.assertIn("id", self.admin.list_display)
        self.assertIn("location", self.admin.list_display)

    def test_autocomplete(self):
        self.assertIn("location", self.admin.autocomplete_fields)

    def test_inlines(self):
        self.assertIn(SpaceTranslationInline, self.admin.inlines)


class TestSpaceTranslationInlineConfig(TestCase):
    def setUp(self):
        self.inline = SpaceTranslationInline(Space, admin.site)

    def test_model(self):
        self.assertIs(self.inline.model, SpaceTranslation)

    def test_fields(self):
        self.assertEqual(tuple(self.inline.fields), ("language", "name"))

    def test_extra(self):
        self.assertEqual(self.inline.extra, 1)


class TestSpaceTranslationAdminConfig(TestCase):
    def setUp(self):
        self.admin = SpaceTranslationAdmin(SpaceTranslation, admin.site)

    def test_list_display(self):
        for field in ("id", "language", "space", "name"):
            self.assertIn(field, self.admin.list_display)


class TestHallAdminConfig(TestCase):
    def setUp(self):
        self.admin = HallAdmin(Hall, admin.site)

    def test_list_display(self):
        for field in ("id", "space", "seat_selection", "open_seating"):
            self.assertIn(field, self.admin.list_display)

    def test_autocomplete(self):
        self.assertIn("space", self.admin.autocomplete_fields)

    def test_inlines(self):
        self.assertIn(HallTranslationInline, self.admin.inlines)


class TestHallTranslationInlineConfig(TestCase):
    def setUp(self):
        self.inline = HallTranslationInline(Hall, admin.site)

    def test_model(self):
        self.assertIs(self.inline.model, HallTranslation)

    def test_fields(self):
        self.assertEqual(tuple(self.inline.fields), ("language", "name", "remark"))


class TestHallTranslationAdminConfig(TestCase):
    def setUp(self):
        self.admin = HallTranslationAdmin(HallTranslation, admin.site)

    def test_list_display(self):
        for field in ("id", "language", "hall", "name"):
            self.assertIn(field, self.admin.list_display)


# ---------------------------------------------------------------------------
# Functional admin flows
# ---------------------------------------------------------------------------


class TestLocationAdminFunctional(TestCase):
    """Functional admin flows for location models."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            "admin", "admin@example.com", "password"
        )
        self.client.force_login(self.superuser)

        self.language = LanguageFactory(code="en")
        self.location = LocationFactory()
        self.location_translation = LocationTranslationFactory(
            location=self.location, language=self.language, name="Venue"
        )
        self.space = SpaceFactory(location=self.location)
        self.space_translation = SpaceTranslationFactory(
            space=self.space, language=self.language, name="Room A"
        )
        self.hall = HallFactory(space=self.space)
        self.hall_translation = HallTranslationFactory(
            hall=self.hall, language=self.language, name="Hall 1", remark="Notes"
        )

    # Location -----------------------------------------------------------------

    def test_location_changelist(self):
        url = reverse("admin:locations_location_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_location_add(self):
        url = reverse("admin:locations_location_add")
        response = self.client.post(
            url,
            {
                "street": "Main",
                "number": "10",
                "postal_code": "9000",
                "city": "Gent",
                "country": "Belgium",
                "phone_1": "123",
                "phone_2": "",
                "is_own_location": "on",
                "translations-TOTAL_FORMS": 0,
                "translations-INITIAL_FORMS": 0,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Location.objects.filter(city="Gent", street="Main").exists())

    def test_location_change(self):
        url = reverse("admin:locations_location_change", args=[self.location.pk])
        response = self.client.post(
            url,
            {
                "street": "Updated",
                "number": self.location.number,
                "postal_code": self.location.postal_code,
                "city": self.location.city,
                "country": self.location.country,
                "phone_1": self.location.phone_1 or "",
                "phone_2": self.location.phone_2 or "",
                "is_own_location": "on" if self.location.is_own_location else "",
                "translations-TOTAL_FORMS": 1,
                "translations-INITIAL_FORMS": 1,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
                "translations-0-id": self.location_translation.pk,
                "translations-0-language": self.language.pk,
                "translations-0-name": self.location_translation.name,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.location.refresh_from_db()
        self.assertEqual(self.location.street, "Updated")

    def test_location_delete(self):
        url = reverse("admin:locations_location_delete", args=[self.location.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Location.objects.filter(pk=self.location.pk).exists())

    # LocationTranslation -------------------------------------------------------

    def test_location_translation_changelist(self):
        url = reverse("admin:locations_locationtranslation_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_location_translation_add(self):
        url = reverse("admin:locations_locationtranslation_add")
        new_language = LanguageFactory(code="fr")
        response = self.client.post(
            url,
            {
                "language": new_language.pk,
                "location": self.location.pk,
                "name": "Venue Added",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            LocationTranslation.objects.filter(
                name="Venue Added", language=new_language
            ).exists()
        )

    def test_location_translation_change(self):
        url = reverse(
            "admin:locations_locationtranslation_change",
            args=[self.location_translation.pk],
        )
        response = self.client.post(
            url,
            {
                "language": self.language.pk,
                "location": self.location.pk,
                "name": "Venue Updated",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.location_translation.refresh_from_db()
        self.assertEqual(self.location_translation.name, "Venue Updated")

    def test_location_translation_delete(self):
        url = reverse(
            "admin:locations_locationtranslation_delete",
            args=[self.location_translation.pk],
        )
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            LocationTranslation.objects.filter(pk=self.location_translation.pk).exists()
        )

    # Space ---------------------------------------------------------------------

    def test_space_changelist(self):
        url = reverse("admin:locations_space_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_space_add(self):
        url = reverse("admin:locations_space_add")
        response = self.client.post(
            url,
            {
                "location": self.location.pk,
                "translations-TOTAL_FORMS": 0,
                "translations-INITIAL_FORMS": 0,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Space.objects.filter(location=self.location).count() >= 1)

    def test_space_change(self):
        url = reverse("admin:locations_space_change", args=[self.space.pk])
        response = self.client.post(
            url,
            {
                "location": self.location.pk,
                "translations-TOTAL_FORMS": 1,
                "translations-INITIAL_FORMS": 1,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
                "translations-0-id": self.space_translation.pk,
                "translations-0-language": self.language.pk,
                "translations-0-name": self.space_translation.name,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_space_delete(self):
        url = reverse("admin:locations_space_delete", args=[self.space.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Space.objects.filter(pk=self.space.pk).exists())

    # SpaceTranslation ---------------------------------------------------------

    def test_space_translation_changelist(self):
        url = reverse("admin:locations_spacetranslation_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_space_translation_add(self):
        url = reverse("admin:locations_spacetranslation_add")
        new_language = LanguageFactory(code="de")
        response = self.client.post(
            url,
            {
                "language": new_language.pk,
                "space": self.space.pk,
                "name": "Room B",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SpaceTranslation.objects.filter(
                name="Room B", language=new_language
            ).exists()
        )

    def test_space_translation_change(self):
        url = reverse(
            "admin:locations_spacetranslation_change", args=[self.space_translation.pk]
        )
        response = self.client.post(
            url,
            {
                "language": self.language.pk,
                "space": self.space.pk,
                "name": "Room C",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.space_translation.refresh_from_db()
        self.assertEqual(self.space_translation.name, "Room C")

    def test_space_translation_delete(self):
        url = reverse(
            "admin:locations_spacetranslation_delete", args=[self.space_translation.pk]
        )
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            SpaceTranslation.objects.filter(pk=self.space_translation.pk).exists()
        )

    # Hall ----------------------------------------------------------------------

    def test_hall_changelist(self):
        url = reverse("admin:locations_hall_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_hall_add(self):
        url = reverse("admin:locations_hall_add")
        response = self.client.post(
            url,
            {
                "space": self.space.pk,
                "seat_selection": "on",
                "open_seating": "",
                "translations-TOTAL_FORMS": 0,
                "translations-INITIAL_FORMS": 0,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Hall.objects.filter(space=self.space).count() >= 1)

    def test_hall_change(self):
        url = reverse("admin:locations_hall_change", args=[self.hall.pk])
        response = self.client.post(
            url,
            {
                "space": self.space.pk,
                "seat_selection": "on" if self.hall.seat_selection else "",
                "open_seating": "on" if self.hall.open_seating else "",
                "translations-TOTAL_FORMS": 1,
                "translations-INITIAL_FORMS": 1,
                "translations-MIN_NUM_FORMS": 0,
                "translations-MAX_NUM_FORMS": 1000,
                "translations-0-id": self.hall_translation.pk,
                "translations-0-language": self.language.pk,
                "translations-0-name": self.hall_translation.name,
                "translations-0-remark": self.hall_translation.remark,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_hall_delete(self):
        url = reverse("admin:locations_hall_delete", args=[self.hall.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Hall.objects.filter(pk=self.hall.pk).exists())

    # HallTranslation ----------------------------------------------------------

    def test_hall_translation_changelist(self):
        url = reverse("admin:locations_halltranslation_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_hall_translation_add(self):
        url = reverse("admin:locations_halltranslation_add")
        new_language = LanguageFactory(code="es", name="Spanish")
        response = self.client.post(
            url,
            {
                "language": new_language.pk,
                "hall": self.hall.pk,
                "name": "Hall X",
                "remark": "Remark X",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            HallTranslation.objects.filter(
                name="Hall X", language=new_language
            ).exists()
        )

    def test_hall_translation_change(self):
        url = reverse(
            "admin:locations_halltranslation_change", args=[self.hall_translation.pk]
        )
        response = self.client.post(
            url,
            {
                "language": self.language.pk,
                "hall": self.hall.pk,
                "name": "Hall Y",
                "remark": "Remark Y",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.hall_translation.refresh_from_db()
        self.assertEqual(self.hall_translation.name, "Hall Y")

    def test_hall_translation_delete(self):
        url = reverse(
            "admin:locations_halltranslation_delete", args=[self.hall_translation.pk]
        )
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            HallTranslation.objects.filter(pk=self.hall_translation.pk).exists()
        )
