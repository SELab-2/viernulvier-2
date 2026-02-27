"""Serializers for the locations domain."""

from rest_framework import serializers

from apps.core.serializers import TranslatableSerializerMixin
from .models import Hall, Location, Space


class LocationSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
	"""Serialize Location with translated name and core address fields."""

	name = serializers.SerializerMethodField()

	class Meta:
		model = Location
		fields = [
			"id",
			"street",
			"number",
			"postal_code",
			"city",
			"country",
			"phone_1",
			"phone_2",
			"is_own_location",
			"name",
		]

	def get_name(self, obj):
		return self.get_translated_field(obj, "name")


class SpaceSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
	"""Serialize Space with owning location and translated name."""

	name = serializers.SerializerMethodField()

	class Meta:
		model = Space
		fields = [
			"id",
			"location",
			"name",
		]

	def get_name(self, obj):
		return self.get_translated_field(obj, "name")


class HallSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
	"""Serialize Hall with seating flags and translated fields."""

	name = serializers.SerializerMethodField()
	remark = serializers.SerializerMethodField()

	class Meta:
		model = Hall
		fields = [
			"id",
			"space",
			"seat_selection",
			"open_seating",
			"name",
			"remark",
		]

	def get_name(self, obj):
		return self.get_translated_field(obj, "name")

	def get_remark(self, obj):
		return self.get_translated_field(obj, "remark")

