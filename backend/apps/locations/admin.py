"""Admin configuration for location-related models."""

from django.contrib import admin

from apps.core.admin import BaseAdmin
from .models import (
	Hall,
	HallTranslation,
	Location,
	LocationTranslation,
	Space,
	SpaceTranslation,
)


class LocationTranslationInline(admin.TabularInline):
	model = LocationTranslation
	extra = 1
	fields = ("language", "name")
	autocomplete_fields = ("language",)


@admin.register(Location)
class LocationAdmin(BaseAdmin):
	"""Admin config for locations with translation inline."""

	list_display = ("id", "city", "street", "number", "country", "is_own_location")
	search_fields = ("city", "street", "country")
	list_filter = ("is_own_location",)
	inlines = [LocationTranslationInline]


@admin.register(LocationTranslation)
class LocationTranslationAdmin(BaseAdmin):
	"""Admin config for location translations."""

	list_display = ("id", "language", "location", "name")
	list_filter = ("language", "location")
	search_fields = ("name", "location__city", "location__street")
	ordering = ("id",)
	autocomplete_fields = ("language", "location")


class SpaceTranslationInline(admin.TabularInline):
	model = SpaceTranslation
	extra = 1
	fields = ("language", "name")
	autocomplete_fields = ("language",)


@admin.register(Space)
class SpaceAdmin(BaseAdmin):
	"""Admin config for spaces with translation inline."""

	list_display = ("id", "location")
	search_fields = ("location__city", "location__street")
	autocomplete_fields = ("location",)
	list_select_related = ("location",)
	inlines = [SpaceTranslationInline]


@admin.register(SpaceTranslation)
class SpaceTranslationAdmin(BaseAdmin):
	"""Admin config for space translations."""

	list_display = ("id", "language", "space", "name")
	list_filter = ("language", "space")
	search_fields = ("name", "space__location__city")
	ordering = ("id",)
	autocomplete_fields = ("language", "space")


class HallTranslationInline(admin.TabularInline):
	model = HallTranslation
	extra = 1
	fields = ("language", "name", "remark")
	autocomplete_fields = ("language",)


@admin.register(Hall)
class HallAdmin(BaseAdmin):
	"""Admin config for halls with translation inline."""

	list_display = ("id", "space", "seat_selection", "open_seating")
	list_filter = ("seat_selection", "open_seating")
	search_fields = ("space__location__city", "space__location__street")
	autocomplete_fields = ("space",)
	list_select_related = ("space", "space__location")
	inlines = [HallTranslationInline]


@admin.register(HallTranslation)
class HallTranslationAdmin(BaseAdmin):
	"""Admin config for hall translations."""

	list_display = ("id", "language", "hall", "name")
	list_filter = ("language", "hall")
	search_fields = ("name", "hall__space__location__city")
	ordering = ("id",)
	autocomplete_fields = ("language", "hall")
