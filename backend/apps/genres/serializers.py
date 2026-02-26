from rest_framework import serializers
from .models import Genre, GenreTranslation, GenreUseAs
from apps.core.serializers import TranslatableSerializerMixin


class GenreUseAsSerializer(serializers.ModelSerializer):
	"""
	Serializer for the GenreUseAs model.
	"""

	class Meta:
		model = GenreUseAs
		fields = [
			"id",
			"name",
		]


class GenreSerializer(serializers.ModelSerializer, TranslatableSerializerMixin):
	"""
	Serializer for the Genre model.
	"""

	name = serializers.SerializerMethodField()

	class Meta:
		model = Genre
		fields = [
			"id",
			"type",
			"use_as",
			"name",
		]

	def get_name(self, obj):
		return self.get_translated_field(obj, "name")
