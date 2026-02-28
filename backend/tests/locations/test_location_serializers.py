"""
Tests for apps/locations/serializers.py

Covers:
- Field exposure for LocationSerializer, SpaceSerializer, HallSerializer
- Translation rendering via TranslatableSerializerMixin
- Queryset serialization for many=True
"""

from django.test import TestCase

from apps.locations.models import Hall, Location, Space
from apps.locations.serializers import HallSerializer, LocationSerializer, SpaceSerializer
from tests.factories.language import LanguageFactory
from tests.factories.location import (
	HallFactory,
	HallTranslationFactory,
	LocationFactory,
	LocationTranslationFactory,
	SpaceFactory,
	SpaceTranslationFactory,
)


class TestLocationSerializerFields(TestCase):
	"""Field exposure for LocationSerializer."""

	def setUp(self):
		self.location = LocationFactory()

	def test_expected_fields_present(self):
		data = LocationSerializer(self.location).data
		self.assertEqual(
			set(data.keys()),
			{
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
			},
		)


class TestLocationSerializerTranslations(TestCase):
	"""Translation rendering for LocationSerializer."""

	def setUp(self):
		self.lang_en = LanguageFactory(code="en", name="English")
		self.lang_nl = LanguageFactory(code="nl", name="Dutch")
		self.location = LocationFactory()
		LocationTranslationFactory(location=self.location, language=self.lang_en, name="Main Hall")
		LocationTranslationFactory(location=self.location, language=self.lang_nl, name="Hoofdzaal")

	def test_translated_name_dict(self):
		data = LocationSerializer(self.location).data
		self.assertEqual(data["name"], {"en": "Main Hall", "nl": "Hoofdzaal"})

	def test_queryset_serialization_many(self):
		data = LocationSerializer(Location.objects.all(), many=True).data
		self.assertIsInstance(data, list)
		self.assertIsInstance(data[0]["name"], dict)


class TestSpaceSerializerFields(TestCase):
	"""Field exposure for SpaceSerializer."""

	def setUp(self):
		self.space = SpaceFactory()

	def test_expected_fields_present(self):
		data = SpaceSerializer(self.space).data
		self.assertEqual(set(data.keys()), {"id", "location", "name"})


class TestSpaceSerializerTranslations(TestCase):
	"""Translation rendering for SpaceSerializer."""

	def setUp(self):
		self.lang = LanguageFactory(code="en")
		self.space = SpaceFactory()
		SpaceTranslationFactory(space=self.space, language=self.lang, name="Room A")

	def test_translated_name_dict(self):
		data = SpaceSerializer(self.space).data
		self.assertEqual(data["name"], {"en": "Room A"})


class TestHallSerializerFields(TestCase):
	"""Field exposure for HallSerializer."""

	def setUp(self):
		self.hall = HallFactory()

	def test_expected_fields_present(self):
		data = HallSerializer(self.hall).data
		self.assertEqual(
			set(data.keys()),
			{"id", "space", "seat_selection", "open_seating", "name", "remark"},
		)


class TestHallSerializerTranslations(TestCase):
	"""Translation rendering for HallSerializer."""

	def setUp(self):
		self.lang_en = LanguageFactory(code="en")
		self.lang_fr = LanguageFactory(code="fr")
		self.hall = HallFactory()
		HallTranslationFactory(hall=self.hall, language=self.lang_en, name="Blue Hall", remark="Front stage")
		HallTranslationFactory(hall=self.hall, language=self.lang_fr, name="Salle Bleue", remark="Avant scène")

	def test_translated_name_and_remark_dicts(self):
		data = HallSerializer(self.hall).data
		self.assertEqual(data["name"], {"en": "Blue Hall", "fr": "Salle Bleue"})
		self.assertEqual(data["remark"], {"en": "Front stage", "fr": "Avant scène"})
