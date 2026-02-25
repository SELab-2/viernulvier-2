from django.contrib import admin

from apps.core.admin import BaseAdmin
from .models import Genre, GenreTranslation, GenreUseAs


class GenreTranslationInline(admin.TabularInline):
	model = GenreTranslation
	extra = 1
	fields = ("language", "name")
	autocomplete_fields = ("language",)


@admin.register(GenreUseAs)
class GenreUseAsAdmin(BaseAdmin):
	"""Admin config for genre use-cases."""

	list_display = ("id", "name")
	search_fields = ("name",)
	ordering = ("name",)


@admin.register(Genre)
class GenreAdmin(BaseAdmin):
	"""Admin config for genres."""

	list_display = ("id", "type", "use_as")
	list_filter = ("use_as",)
	search_fields = ("type",)
	ordering = ("id",)
	autocomplete_fields = ("use_as",)


@admin.register(GenreTranslation)
class GenreTranslationAdmin(BaseAdmin):
	"""Admin config for genre translations."""

	list_display = ("id", "name", "language", "genre")
	list_filter = ("language", "genre")
	search_fields = ("name",)
	ordering = ("id",)
	autocomplete_fields = ("language", "genre")
