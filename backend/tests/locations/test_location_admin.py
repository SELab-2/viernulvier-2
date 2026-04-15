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

    def test_location_registered(self) -> None:
        assert Location in admin.site._registry
        assert isinstance(admin.site._registry[Location], LocationAdmin)

    def test_location_translation_registered(self) -> None:
        assert LocationTranslation in admin.site._registry
        assert isinstance(admin.site._registry[LocationTranslation], LocationTranslationAdmin)

    def test_space_registered(self) -> None:
        assert Space in admin.site._registry
        assert isinstance(admin.site._registry[Space], SpaceAdmin)

    def test_space_translation_registered(self) -> None:
        assert SpaceTranslation in admin.site._registry
        assert isinstance(admin.site._registry[SpaceTranslation], SpaceTranslationAdmin)

    def test_hall_registered(self) -> None:
        assert Hall in admin.site._registry
        assert isinstance(admin.site._registry[Hall], HallAdmin)

    def test_hall_translation_registered(self) -> None:
        assert HallTranslation in admin.site._registry
        assert isinstance(admin.site._registry[HallTranslation], HallTranslationAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestLocationAdminInheritance(TestCase):
    """Ensure admin classes inherit from BaseAdmin/ModelAdmin."""

    def test_location_inherits(self) -> None:
        assert issubclass(LocationAdmin, BaseAdmin)
        assert issubclass(LocationAdmin, admin.ModelAdmin)

    def test_location_translation_inherits(self) -> None:
        assert issubclass(LocationTranslationAdmin, BaseAdmin)
        assert issubclass(LocationTranslationAdmin, admin.ModelAdmin)

    def test_space_inherits(self) -> None:
        assert issubclass(SpaceAdmin, BaseAdmin)
        assert issubclass(SpaceAdmin, admin.ModelAdmin)

    def test_space_translation_inherits(self) -> None:
        assert issubclass(SpaceTranslationAdmin, BaseAdmin)
        assert issubclass(SpaceTranslationAdmin, admin.ModelAdmin)

    def test_hall_inherits(self) -> None:
        assert issubclass(HallAdmin, BaseAdmin)
        assert issubclass(HallAdmin, admin.ModelAdmin)

    def test_hall_translation_inherits(self) -> None:
        assert issubclass(HallTranslationAdmin, BaseAdmin)
        assert issubclass(HallTranslationAdmin, admin.ModelAdmin)


# ---------------------------------------------------------------------------
# Config checks
# ---------------------------------------------------------------------------


class TestLocationAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = LocationAdmin(Location, admin.site)

    def test_list_display(self) -> None:
        for field in ("id", "city", "street", "number", "country", "is_own_location"):
            assert field in self.admin.list_display

    def test_list_filter(self) -> None:
        assert "is_own_location" in self.admin.list_filter

    def test_search_fields(self) -> None:
        for field in ("city", "street", "country"):
            assert field in self.admin.search_fields

    def test_inlines(self) -> None:
        assert LocationTranslationInline in self.admin.inlines


class TestLocationTranslationInlineConfig(TestCase):
    def setUp(self) -> None:
        self.inline = LocationTranslationInline(Location, admin.site)

    def test_model(self) -> None:
        assert self.inline.model is LocationTranslation

    def test_fields(self) -> None:
        assert tuple(self.inline.fields) == ("language", "name")

    def test_autocomplete_fields(self) -> None:
        assert "language" in self.inline.autocomplete_fields

    def test_extra(self) -> None:
        assert self.inline.extra == 1


class TestLocationTranslationAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = LocationTranslationAdmin(LocationTranslation, admin.site)

    def test_list_display(self) -> None:
        for field in ("id", "language", "location", "name"):
            assert field in self.admin.list_display

    def test_list_filter(self) -> None:
        assert "language" in self.admin.list_filter
        assert "location" in self.admin.list_filter

    def test_search_fields(self) -> None:
        assert "name" in self.admin.search_fields


class TestSpaceAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = SpaceAdmin(Space, admin.site)

    def test_list_display(self) -> None:
        assert "id" in self.admin.list_display
        assert "location" in self.admin.list_display

    def test_autocomplete(self) -> None:
        assert "location" in self.admin.autocomplete_fields

    def test_inlines(self) -> None:
        assert SpaceTranslationInline in self.admin.inlines


class TestSpaceTranslationInlineConfig(TestCase):
    def setUp(self) -> None:
        self.inline = SpaceTranslationInline(Space, admin.site)

    def test_model(self) -> None:
        assert self.inline.model is SpaceTranslation

    def test_fields(self) -> None:
        assert tuple(self.inline.fields) == ("language", "name")

    def test_extra(self) -> None:
        assert self.inline.extra == 1


class TestSpaceTranslationAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = SpaceTranslationAdmin(SpaceTranslation, admin.site)

    def test_list_display(self) -> None:
        for field in ("id", "language", "space", "name"):
            assert field in self.admin.list_display


class TestHallAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = HallAdmin(Hall, admin.site)

    def test_list_display(self) -> None:
        for field in ("id", "space", "seat_selection", "open_seating"):
            assert field in self.admin.list_display

    def test_autocomplete(self) -> None:
        assert "space" in self.admin.autocomplete_fields

    def test_inlines(self) -> None:
        assert HallTranslationInline in self.admin.inlines


class TestHallTranslationInlineConfig(TestCase):
    def setUp(self) -> None:
        self.inline = HallTranslationInline(Hall, admin.site)

    def test_model(self) -> None:
        assert self.inline.model is HallTranslation

    def test_fields(self) -> None:
        assert tuple(self.inline.fields) == ("language", "name", "remark")


class TestHallTranslationAdminConfig(TestCase):
    def setUp(self) -> None:
        self.admin = HallTranslationAdmin(HallTranslation, admin.site)

    def test_list_display(self) -> None:
        for field in ("id", "language", "hall", "name"):
            assert field in self.admin.list_display


# ---------------------------------------------------------------------------
# Functional admin flows
# ---------------------------------------------------------------------------


class TestLocationAdminFunctional(TestCase):
    """Functional admin flows for location models."""

    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(self.superuser)

        self.language = LanguageFactory(code="en")
        self.location = LocationFactory()
        self.location_translation = LocationTranslationFactory(location=self.location, language=self.language, name="Venue")
        self.space = SpaceFactory(location=self.location)
        self.space_translation = SpaceTranslationFactory(space=self.space, language=self.language, name="Room A")
        self.hall = HallFactory(space=self.space)
        self.hall_translation = HallTranslationFactory(hall=self.hall, language=self.language, name="Hall 1", remark="Notes")

    # Location -----------------------------------------------------------------

    def test_location_changelist(self) -> None:
        url = reverse("admin:locations_location_changelist")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_location_add(self) -> None:
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
        assert response.status_code == 200
        assert Location.objects.filter(city="Gent", street="Main").exists()

    def test_location_change(self) -> None:
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
        assert response.status_code == 200
        self.location.refresh_from_db()
        assert self.location.street == "Updated"

    def test_location_delete(self) -> None:
        url = reverse("admin:locations_location_delete", args=[self.location.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not Location.objects.filter(pk=self.location.pk).exists()

    # LocationTranslation -------------------------------------------------------

    def test_location_translation_changelist(self) -> None:
        url = reverse("admin:locations_locationtranslation_changelist")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_location_translation_add(self) -> None:
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
        assert response.status_code == 200
        assert LocationTranslation.objects.filter(name="Venue Added", language=new_language).exists()

    def test_location_translation_change(self) -> None:
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
        assert response.status_code == 200
        self.location_translation.refresh_from_db()
        assert self.location_translation.name == "Venue Updated"

    def test_location_translation_delete(self) -> None:
        url = reverse(
            "admin:locations_locationtranslation_delete",
            args=[self.location_translation.pk],
        )
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not LocationTranslation.objects.filter(pk=self.location_translation.pk).exists()

    # Space ---------------------------------------------------------------------

    def test_space_changelist(self) -> None:
        url = reverse("admin:locations_space_changelist")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_space_add(self) -> None:
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
        assert response.status_code == 200
        assert Space.objects.filter(location=self.location).count() >= 1

    def test_space_change(self) -> None:
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
        assert response.status_code == 200

    def test_space_delete(self) -> None:
        url = reverse("admin:locations_space_delete", args=[self.space.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not Space.objects.filter(pk=self.space.pk).exists()

    # SpaceTranslation ---------------------------------------------------------

    def test_space_translation_changelist(self) -> None:
        url = reverse("admin:locations_spacetranslation_changelist")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_space_translation_add(self) -> None:
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
        assert response.status_code == 200
        assert SpaceTranslation.objects.filter(name="Room B", language=new_language).exists()

    def test_space_translation_change(self) -> None:
        url = reverse("admin:locations_spacetranslation_change", args=[self.space_translation.pk])
        response = self.client.post(
            url,
            {
                "language": self.language.pk,
                "space": self.space.pk,
                "name": "Room C",
            },
            follow=True,
        )
        assert response.status_code == 200
        self.space_translation.refresh_from_db()
        assert self.space_translation.name == "Room C"

    def test_space_translation_delete(self) -> None:
        url = reverse("admin:locations_spacetranslation_delete", args=[self.space_translation.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not SpaceTranslation.objects.filter(pk=self.space_translation.pk).exists()

    # Hall ----------------------------------------------------------------------

    def test_hall_changelist(self) -> None:
        url = reverse("admin:locations_hall_changelist")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_hall_add(self) -> None:
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
        assert response.status_code == 200
        assert Hall.objects.filter(space=self.space).count() >= 1

    def test_hall_change(self) -> None:
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
        assert response.status_code == 200

    def test_hall_delete(self) -> None:
        url = reverse("admin:locations_hall_delete", args=[self.hall.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not Hall.objects.filter(pk=self.hall.pk).exists()

    # HallTranslation ----------------------------------------------------------

    def test_hall_translation_changelist(self) -> None:
        url = reverse("admin:locations_halltranslation_changelist")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_hall_translation_add(self) -> None:
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
        assert response.status_code == 200
        assert HallTranslation.objects.filter(name="Hall X", language=new_language).exists()

    def test_hall_translation_change(self) -> None:
        url = reverse("admin:locations_halltranslation_change", args=[self.hall_translation.pk])
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
        assert response.status_code == 200
        self.hall_translation.refresh_from_db()
        assert self.hall_translation.name == "Hall Y"

    def test_hall_translation_delete(self) -> None:
        url = reverse("admin:locations_halltranslation_delete", args=[self.hall_translation.pk])
        response = self.client.post(url, {"post": "yes"}, follow=True)
        assert response.status_code == 200
        assert not HallTranslation.objects.filter(pk=self.hall_translation.pk).exists()
