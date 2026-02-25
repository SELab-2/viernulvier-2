from rest_framework import serializers
from .models import Genre, GenreTranslation, GenreUseAs


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


class GenreSerializer(serializers.ModelSerializer):
	"""
	Serializer for the Genre model.
	"""

	class Meta:
		model = Genre
		fields = [
			"id",
			"type",
			"use_as",
		]


class GenreTranslationSerializer(serializers.ModelSerializer):
	"""
	Serializer for the GenreTranslation model.
	"""

	class Meta:
		model = GenreTranslation
		fields = [
			"id",
			"name",
			"language",
			"genre",
		]

