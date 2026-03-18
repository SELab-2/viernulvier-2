"""
Tests for apps/productions/serializers.py

Covers:
- UitDatabaseThemeSerializer field presence and completeness
- UitDatabaseTypeSerializer field presence and completeness
- ProductionSerializer field presence and completeness
- ProductionSerializer serialization of scalar fields (attendance_mode, performer_type)
- Nested UitDatabaseThemeSerializer output
- Nested UitDatabaseTypeSerializer output
- Nested TagSerializer output
- Translated fields (title, description, teaser, artist_name, tagline) returned as dicts
- Translated fields return empty dict when no translations exist
- Translated fields omit blank/falsy values per language
- Multiple translations are all included in the dict
- ProductionSerializer inherits from TranslatableSerializerMixin
"""

from django.test import TestCase

from apps.core.serializers import TranslatableSerializerMixin
from apps.productions.serializers import (
    ProductionSerializer,
    UitDatabaseThemeSerializer,
    UitDatabaseTypeSerializer,
)
from tests.factories.language import LanguageFactory
from tests.factories.media_library import MediaGalleryFactory
from tests.factories.production import (
    ProductionFactory,
    ProductionTranslationFactory,
    UitDatabaseThemeFactory,
    UitDatabaseTypeFactory,
)
from tests.factories.tag import TagFactory

# ---------------------------------------------------------------------------
# UitDatabaseThemeSerializer
# ---------------------------------------------------------------------------


class TestUitDatabaseThemeSerializerFields(TestCase):
    """Verify field presence and output of UitDatabaseThemeSerializer."""

    def setUp(self):
        self.theme = UitDatabaseThemeFactory.create(name="Drama")

    def test_expected_fields_are_present(self):
        data = UitDatabaseThemeSerializer(self.theme).data
        for field in ("id", "name"):
            self.assertIn(field, data)

    def test_no_extra_fields_are_exposed(self):
        data = UitDatabaseThemeSerializer(self.theme).data
        self.assertEqual(set(data.keys()), {"id", "name"})

    def test_serializes_name_correctly(self):
        data = UitDatabaseThemeSerializer(self.theme).data
        self.assertEqual(data["name"], "Drama")

    def test_serializes_id_correctly(self):
        data = UitDatabaseThemeSerializer(self.theme).data
        self.assertEqual(data["id"], self.theme.id)


# ---------------------------------------------------------------------------
# UitDatabaseTypeSerializer
# ---------------------------------------------------------------------------


class TestUitDatabaseTypeSerializerFields(TestCase):
    """Verify field presence and output of UitDatabaseTypeSerializer."""

    def setUp(self):
        self.db_type = UitDatabaseTypeFactory.create(name="Concert")

    def test_expected_fields_are_present(self):
        data = UitDatabaseTypeSerializer(self.db_type).data
        for field in ("id", "name"):
            self.assertIn(field, data)

    def test_no_extra_fields_are_exposed(self):
        data = UitDatabaseTypeSerializer(self.db_type).data
        self.assertEqual(set(data.keys()), {"id", "name"})

    def test_serializes_name_correctly(self):
        data = UitDatabaseTypeSerializer(self.db_type).data
        self.assertEqual(data["name"], "Concert")

    def test_serializes_id_correctly(self):
        data = UitDatabaseTypeSerializer(self.db_type).data
        self.assertEqual(data["id"], self.db_type.id)


# ---------------------------------------------------------------------------
# ProductionSerializer - field presence
# ---------------------------------------------------------------------------


class TestProductionSerializerFields(TestCase):
    """Verify that exactly the expected fields are exposed."""

    def setUp(self):
        self.production = ProductionFactory.create()

    def test_expected_fields_are_present(self):
        data = ProductionSerializer(self.production).data
        expected = {
            "id",
            "attendance_mode",
            "performer_type",
            "media_gallery",
            "uit_database_theme",
            "uit_database_type",
            "title",
            "description",
            "teaser",
            "artist_name",
            "tagline",
            "tags",
        }
        for field in expected:
            self.assertIn(field, data)

    def test_no_extra_fields_are_exposed(self):
        data = ProductionSerializer(self.production).data
        expected = {
            "id",
            "attendance_mode",
            "performer_type",
            "media_gallery",
            "uit_database_theme",
            "uit_database_type",
            "title",
            "description",
            "teaser",
            "artist_name",
            "tagline",
            "tags",
            "genres",
            "display_title",
            "display_artist_name",
        }
        self.assertEqual(set(data.keys()), expected)


# ---------------------------------------------------------------------------
# ProductionSerializer - scalar fields
# ---------------------------------------------------------------------------


class TestProductionSerializerScalarFields(TestCase):
    """Model -> dict for non-translated, non-nested fields."""

    def test_serializes_media_gallery_correctly(self):
        gallery = MediaGalleryFactory.create()
        production = ProductionFactory.create(media_gallery=gallery)
        data = ProductionSerializer(production).data
        self.assertEqual(data["media_gallery"], {"id": 1, "name": "Gallery_456", "media_items": []})

    def test_serializes_null_media_gallery_correctly(self):
        production = ProductionFactory.create(media_gallery=None)
        data = ProductionSerializer(production).data
        self.assertIsNone(data["media_gallery"])

    def test_serializes_attendance_mode_correctly(self):
        production = ProductionFactory.create(attendance_mode="offline")
        data = ProductionSerializer(production).data
        self.assertEqual(data["attendance_mode"], "offline")

    def test_serializes_online_attendance_mode_correctly(self):
        production = ProductionFactory.create(attendance_mode="online")
        data = ProductionSerializer(production).data
        self.assertEqual(data["attendance_mode"], "online")

    def test_serializes_blank_attendance_mode_correctly(self):
        production = ProductionFactory.create(attendance_mode="")
        data = ProductionSerializer(production).data
        self.assertEqual(data["attendance_mode"], "")

    def test_serializes_performer_type_group_correctly(self):
        production = ProductionFactory.create(performer_type="group")
        data = ProductionSerializer(production).data
        self.assertEqual(data["performer_type"], "group")

    def test_serializes_performer_type_solo_correctly(self):
        production = ProductionFactory.create(performer_type="solo")
        data = ProductionSerializer(production).data
        self.assertEqual(data["performer_type"], "solo")


# ---------------------------------------------------------------------------
# ProductionSerializer - nested fields
# ---------------------------------------------------------------------------


class TestProductionSerializerNestedUitDatabaseTheme(TestCase):
    """Verify nested UitDatabaseTheme serialization."""

    def test_uit_database_theme_is_null_when_not_set(self):
        production = ProductionFactory.create(uit_database_theme=None)
        data = ProductionSerializer(production).data
        self.assertIsNone(data["uit_database_theme"])

    def test_uit_database_theme_contains_id_and_name(self):
        theme = UitDatabaseThemeFactory.create(name="Jazz")
        production = ProductionFactory.create(uit_database_theme=theme)
        data = ProductionSerializer(production).data
        self.assertEqual(data["uit_database_theme"]["id"], theme.id)
        self.assertEqual(data["uit_database_theme"]["name"], "Jazz")


class TestProductionSerializerNestedUitDatabaseType(TestCase):
    """Verify nested UitDatabaseType serialization."""

    def test_uit_database_type_is_null_when_not_set(self):
        production = ProductionFactory.create(uit_database_type=None)
        data = ProductionSerializer(production).data
        self.assertIsNone(data["uit_database_type"])

    def test_uit_database_type_contains_id_and_name(self):
        db_type = UitDatabaseTypeFactory.create(name="Theater")
        production = ProductionFactory.create(uit_database_type=db_type)
        data = ProductionSerializer(production).data
        self.assertEqual(data["uit_database_type"]["id"], db_type.id)
        self.assertEqual(data["uit_database_type"]["name"], "Theater")


class TestProductionSerializerNestedTags(TestCase):
    """Verify nested Tags serialization."""

    def test_tags_is_empty_list_when_no_tags(self):
        production = ProductionFactory.create()
        data = ProductionSerializer(production).data
        self.assertEqual(data["tags"], [])

    def test_tags_contains_tag_data(self):
        production = ProductionFactory.create()
        tag = TagFactory.create(type="theme")
        production.tags.add(tag)
        data = ProductionSerializer(production).data
        self.assertEqual(len(data["tags"]), 1)
        self.assertEqual(data["tags"][0]["id"], tag.id)

    def test_tags_contains_multiple_tags(self):
        production = ProductionFactory.create()
        tag_a = TagFactory.create(type="genre")
        tag_b = TagFactory.create(type="mood")
        production.tags.add(tag_a, tag_b)
        data = ProductionSerializer(production).data
        self.assertEqual(len(data["tags"]), 2)


# ---------------------------------------------------------------------------
# ProductionSerializer - translated fields (empty state)
# ---------------------------------------------------------------------------


class TestProductionSerializerTranslatedFieldsEmpty(TestCase):
    """Translated fields return an empty dict when no translations exist."""

    def setUp(self):
        self.production = ProductionFactory.create()

    def test_title_is_empty_dict_without_translations(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["title"], {})

    def test_description_is_empty_dict_without_translations(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["description"], {})

    def test_teaser_is_empty_dict_without_translations(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["teaser"], {})

    def test_artist_name_is_empty_dict_without_translations(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["artist_name"], {})

    def test_tagline_is_empty_dict_without_translations(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["tagline"], {})


# ---------------------------------------------------------------------------
# ProductionSerializer - translated fields (populated state)
# ---------------------------------------------------------------------------


class TestProductionSerializerTranslatedFieldsPopulated(TestCase):
    """Translated fields return a dict keyed by language code when translations exist."""

    def setUp(self):
        self.production = ProductionFactory.create()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        ProductionTranslationFactory.create(
            production=self.production,
            language=self.nl,
            title="Nederlandse Titel",
            description="Nederlandse beschrijving",
            teaser="Nederlandse teaser",
            artist_name="Artiest NL",
            tagline="Tagline NL",
        )

    def test_title_contains_language_code_key(self):
        data = ProductionSerializer(self.production).data
        self.assertIn("nl", data["title"])

    def test_title_value_matches_translation(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["title"]["nl"], "Nederlandse Titel")

    def test_description_value_matches_translation(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["description"]["nl"], "Nederlandse beschrijving")

    def test_teaser_value_matches_translation(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["teaser"]["nl"], "Nederlandse teaser")

    def test_artist_name_value_matches_translation(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["artist_name"]["nl"], "Artiest NL")

    def test_tagline_value_matches_translation(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["tagline"]["nl"], "Tagline NL")


# ---------------------------------------------------------------------------
# ProductionSerializer - translated fields (multiple languages)
# ---------------------------------------------------------------------------


class TestProductionSerializerMultipleTranslations(TestCase):
    """Multiple language translations are all present in the output dict."""

    def setUp(self):
        self.production = ProductionFactory.create()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        self.en = LanguageFactory.create(code="en", name="English")
        ProductionTranslationFactory.create(production=self.production, language=self.nl, title="Titel NL")
        ProductionTranslationFactory.create(production=self.production, language=self.en, title="Title EN")

    def test_title_contains_both_language_codes(self):
        data = ProductionSerializer(self.production).data
        self.assertIn("nl", data["title"])
        self.assertIn("en", data["title"])

    def test_title_nl_value_is_correct(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["title"]["nl"], "Titel NL")

    def test_title_en_value_is_correct(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(data["title"]["en"], "Title EN")

    def test_title_dict_has_exactly_two_entries(self):
        data = ProductionSerializer(self.production).data
        self.assertEqual(len(data["title"]), 2)


# ---------------------------------------------------------------------------
# ProductionSerializer - translated fields (blank values are omitted)
# ---------------------------------------------------------------------------


class TestProductionSerializerTranslatedFieldsOmitBlanks(TestCase):
    """Blank translated field values must not appear in the output dict."""

    def setUp(self):
        self.production = ProductionFactory.create()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        # Only title is set; description, teaser etc. are blank
        ProductionTranslationFactory.create(
            production=self.production,
            language=self.nl,
            title="Titel NL",
            description="",
            teaser="",
            artist_name="",
            tagline="",
        )

    def test_blank_description_is_omitted_from_dict(self):
        data = ProductionSerializer(self.production).data
        self.assertNotIn("nl", data["description"])

    def test_non_blank_title_is_present_in_dict(self):
        data = ProductionSerializer(self.production).data
        self.assertIn("nl", data["title"])


# ---------------------------------------------------------------------------
# Mixin inheritance
# ---------------------------------------------------------------------------


class TestProductionSerializerInheritance(TestCase):
    """ProductionSerializer must use TranslatableSerializerMixin."""

    def test_inherits_from_translatable_serializer_mixin(self):
        self.assertTrue(issubclass(ProductionSerializer, TranslatableSerializerMixin))
