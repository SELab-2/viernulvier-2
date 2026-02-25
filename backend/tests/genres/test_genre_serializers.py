"""
Tests for apps/genres/serializers.py

Covers:
- GenreUseAsSerializer serialization/deserialization
- GenreSerializer serialization/deserialization
- GenreTranslationSerializer serialization/deserialization
- Field presence and types
- Invalid data handling
"""

from django.test import TestCase

from apps.genres.models import Genre, GenreTranslation, GenreUseAs
from apps.genres.serializers import (
    GenreSerializer,
    GenreTranslationSerializer,
    GenreUseAsSerializer,
)
from apps.languages.models import Language


class TestGenreUseAsSerializerFields(TestCase):
    """Field exposure for GenreUseAsSerializer."""
    def setUp(self):
        self.use_as = GenreUseAs(name="genre")
        self.use_as.save()

    def test_expected_fields_are_present(self):
        data = GenreUseAsSerializer(self.use_as).data

        self.assertEqual(set(data.keys()), {"id", "name"})
        self.assertEqual(data["name"], "genre")
        self.assertIsInstance(data["id"], int)


class TestGenreUseAsSerializerSerialization(TestCase):
    """Model → dict serialization for GenreUseAsSerializer."""
    def test_serializes_instance(self):
        use_as = GenreUseAs.objects.create(name="tag")
        data = GenreUseAsSerializer(use_as).data

        self.assertEqual(data["name"], "tag")
        self.assertIsInstance(data["id"], int)

    def test_serializes_queryset(self):
        GenreUseAs.objects.create(name="tag")
        GenreUseAs.objects.create(name="genre")

        data = GenreUseAsSerializer(GenreUseAs.objects.all(), many=True).data
        names = {item["name"] for item in data}

        self.assertIn("tag", names)
        self.assertIn("genre", names)


class TestGenreUseAsSerializerDeserialization(TestCase):
    """dict → model validation for GenreUseAsSerializer."""
    def test_valid_data_creates(self):
        serializer = GenreUseAsSerializer(data={"name": "genre"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        instance = serializer.save()
        self.assertEqual(instance.name, "genre")

    def test_missing_name_is_invalid(self):
        serializer = GenreUseAsSerializer(data={})

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_empty_name_is_invalid(self):
        serializer = GenreUseAsSerializer(data={"name": ""})

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)


class TestGenreSerializerFields(TestCase):
    """Field exposure for GenreSerializer."""
    def setUp(self):
        self.use_as = GenreUseAs.objects.create(name="genre")
        self.genre = Genre.objects.create(type="Theater", use_as=self.use_as)

    def test_expected_fields_are_present(self):
        data = GenreSerializer(self.genre).data
        self.assertEqual(set(data.keys()), {"id", "type", "use_as", "name"})


class TestGenreSerializerSerialization(TestCase):
    """Model → dict serialization for GenreSerializer."""
    def setUp(self):
        self.use_as = GenreUseAs.objects.create(name="genre")
        self.lang_en = Language.objects.create(code="en", name="English", is_active=True)
        self.lang_nl = Language.objects.create(code="nl", name="Dutch", is_active=True)

    def test_serializes_instance(self):
        genre = Genre.objects.create(type="Theater", use_as=self.use_as)
        GenreTranslation.objects.create(name="Theatre", language=self.lang_en, genre=genre)
        GenreTranslation.objects.create(name="Theater", language=self.lang_nl, genre=genre)

        data = GenreSerializer(genre).data

        self.assertEqual(data["type"], "Theater")
        self.assertEqual(data["use_as"], self.use_as.id)
        self.assertIsInstance(data["id"], int)
        self.assertEqual(data["name"], {"en": "Theatre", "nl": "Theater"})

    def test_serializes_queryset(self):
        g1 = Genre.objects.create(type="Festival", use_as=self.use_as)
        g2 = Genre.objects.create(type="Concert", use_as=self.use_as)

        GenreTranslation.objects.create(name="Festival", language=self.lang_en, genre=g1)
        GenreTranslation.objects.create(name="Concert", language=self.lang_en, genre=g2)

        data = GenreSerializer(Genre.objects.all(), many=True).data
        types = {item["type"] for item in data}

        self.assertIn("Festival", types)
        self.assertIn("Concert", types)
        # name field is a dict, ensure present and keyed by language
        for item in data:
            self.assertIsInstance(item["name"], dict)


class TestGenreSerializerDeserialization(TestCase):
    """dict → model validation for GenreSerializer."""
    def setUp(self):
        self.use_as = GenreUseAs.objects.create(name="genre")
        self.lang_en = Language.objects.create(code="en", name="English", is_active=True)

    def test_valid_data_creates(self):
        serializer = GenreSerializer(data={"type": "Theater", "use_as": self.use_as.id})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        instance = serializer.save()
        self.assertEqual(instance.type, "Theater")
        self.assertEqual(instance.use_as, self.use_as)
        # name is read-only (computed), so not required in input

    def test_missing_type_is_invalid(self):
        serializer = GenreSerializer(data={"use_as": self.use_as.id})

        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_missing_use_as_is_invalid(self):
        serializer = GenreSerializer(data={"type": "Concert"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("use_as", serializer.errors)

    def test_empty_type_is_invalid(self):
        serializer = GenreSerializer(data={"type": "", "use_as": self.use_as.id})

        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_partial_update_type_only(self):
        genre = Genre.objects.create(type="Concert", use_as=self.use_as)
        serializer = GenreSerializer(genre, data={"type": "Festival"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated = serializer.save()
        self.assertEqual(updated.type, "Festival")
        self.assertEqual(updated.use_as, self.use_as)


class TestGenreTranslationSerializerFields(TestCase):
    """Field exposure for GenreTranslationSerializer."""
    def setUp(self):
        self.language = Language(code="en", name="English", is_active=True)
        self.use_as = GenreUseAs(name="genre")
        self.genre = Genre(type="Theater", use_as=self.use_as)
        self.translation = GenreTranslation(name="Theater", language=self.language, genre=self.genre)

    def test_expected_fields_are_present(self):
        data = GenreTranslationSerializer(self.translation).data
        self.assertEqual(set(data.keys()), {"id", "name", "language", "genre"})


class TestGenreTranslationSerializerSerialization(TestCase):
    """Model → dict serialization for GenreTranslationSerializer."""
    def setUp(self):
        self.language = Language.objects.create(code="en", name="English", is_active=True)
        self.use_as = GenreUseAs.objects.create(name="genre")
        self.genre = Genre.objects.create(type="Theater", use_as=self.use_as)

    def test_serializes_instance(self):
        translation = GenreTranslation.objects.create(
            name="Theater",
            language=self.language,
            genre=self.genre,
        )
        data = GenreTranslationSerializer(translation).data

        self.assertEqual(data["name"], "Theater")
        self.assertEqual(data["language"], self.language.code)
        self.assertEqual(data["genre"], self.genre.id)
        self.assertIsInstance(data["id"], int)

    def test_serializes_queryset(self):
        GenreTranslation.objects.create(name="Theater", language=self.language, genre=self.genre)
        GenreTranslation.objects.create(name="Teater", language=self.language, genre=self.genre)

        data = GenreTranslationSerializer(GenreTranslation.objects.all(), many=True).data
        names = {item["name"] for item in data}

        self.assertIn("Theater", names)
        self.assertIn("Teater", names)


class TestGenreTranslationSerializerDeserialization(TestCase):
    """dict → model validation for GenreTranslationSerializer."""
    def setUp(self):
        self.language = Language.objects.create(code="en", name="English", is_active=True)
        self.use_as = GenreUseAs.objects.create(name="genre")
        self.genre = Genre.objects.create(type="Theater", use_as=self.use_as)

    def test_valid_data_creates(self):
        serializer = GenreTranslationSerializer(
            data={
                "name": "Theater",
                "language": self.language.code,
                "genre": self.genre.id,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        instance = serializer.save()
        self.assertEqual(instance.name, "Theater")
        self.assertEqual(instance.language, self.language)
        self.assertEqual(instance.genre, self.genre)

    def test_missing_name_is_invalid(self):
        serializer = GenreTranslationSerializer(data={"language": self.language.code, "genre": self.genre.id})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_missing_language_is_invalid(self):
        serializer = GenreTranslationSerializer(data={"name": "Theater", "genre": self.genre.id})
        self.assertFalse(serializer.is_valid())
        self.assertIn("language", serializer.errors)

    def test_missing_genre_is_invalid(self):
        serializer = GenreTranslationSerializer(data={"name": "Theater", "language": self.language.code})
        self.assertFalse(serializer.is_valid())
        self.assertIn("genre", serializer.errors)

    def test_empty_name_is_invalid(self):
        serializer = GenreTranslationSerializer(
            data={"name": "", "language": self.language.code, "genre": self.genre.id}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_partial_update_name_only(self):
        translation = GenreTranslation.objects.create(
            name="Theater",
            language=self.language,
            genre=self.genre,
        )
        serializer = GenreTranslationSerializer(translation, data={"name": "Teater"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated = serializer.save()
        self.assertEqual(updated.name, "Teater")
        self.assertEqual(updated.language, self.language)
        self.assertEqual(updated.genre, self.genre)
