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

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.db.models import Max, Min
from django.test import TestCase

from apps.core.serializers import TranslatableSerializerMixin
from apps.productions.models import Production
from apps.productions.serializers import (
    ProductionSerializer,
    ProductionSeriesSerializer,
    ProductionTagSerializer,
    RelatedProductionSerializer,
    RelatedTagSerializer,
    UitDatabaseThemeSerializer,
    UitDatabaseTypeSerializer,
)
from tests.factories.event import EventFactory
from tests.factories.language import LanguageFactory
from tests.factories.media_library import MediaGalleryFactory
from tests.factories.production import (
    ProductionFactory,
    ProductionTagFactory,
    ProductionTagTranslationFactory,
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

    def setUp(self) -> None:
        self.theme = UitDatabaseThemeFactory.create(name="Drama")

    def test_expected_fields_are_present(self) -> None:
        data = UitDatabaseThemeSerializer(self.theme).data
        for field in ("id", "name"):
            assert field in data

    def test_no_extra_fields_are_exposed(self) -> None:
        data = UitDatabaseThemeSerializer(self.theme).data
        assert set(data.keys()) == {"id", "name"}

    def test_serializes_name_correctly(self) -> None:
        data = UitDatabaseThemeSerializer(self.theme).data
        assert data["name"] == "Drama"

    def test_serializes_id_correctly(self) -> None:
        data = UitDatabaseThemeSerializer(self.theme).data
        assert data["id"] == self.theme.id


# ---------------------------------------------------------------------------
# UitDatabaseTypeSerializer
# ---------------------------------------------------------------------------


class TestUitDatabaseTypeSerializerFields(TestCase):
    """Verify field presence and output of UitDatabaseTypeSerializer."""

    def setUp(self) -> None:
        self.db_type = UitDatabaseTypeFactory.create(name="Concert")

    def test_expected_fields_are_present(self) -> None:
        data = UitDatabaseTypeSerializer(self.db_type).data
        for field in ("id", "name"):
            assert field in data

    def test_no_extra_fields_are_exposed(self) -> None:
        data = UitDatabaseTypeSerializer(self.db_type).data
        assert set(data.keys()) == {"id", "name"}

    def test_serializes_name_correctly(self) -> None:
        data = UitDatabaseTypeSerializer(self.db_type).data
        assert data["name"] == "Concert"

    def test_serializes_id_correctly(self) -> None:
        data = UitDatabaseTypeSerializer(self.db_type).data
        assert data["id"] == self.db_type.id


# ---------------------------------------------------------------------------
# ProductionSerializer - field presence
# ---------------------------------------------------------------------------


class TestProductionSerializerFields(TestCase):
    """Verify that exactly the expected fields are exposed."""

    def setUp(self) -> None:
        self.production = ProductionFactory.create()

    def test_expected_fields_are_present(self) -> None:
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
            assert field in data

    def test_no_extra_fields_are_exposed(self) -> None:
        data = ProductionSerializer(self.production).data
        expected = {
            "id",
            "attendance_mode",
            "performer_type",
            "first_event_start",
            "last_event_end",
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
        assert set(data.keys()) == expected


class TestRelatedProductionSerializerFields(TestCase):
    """Verify the compact serializer used for related productions."""

    def setUp(self) -> None:
        self.production = ProductionFactory.create()
        self.language = LanguageFactory.create(code="nl", name="Dutch")
        ProductionTranslationFactory.create(
            production=self.production,
            language=self.language,
            title="Related productie",
            artist_name="Related maker",
        )

    def test_expected_fields_are_present(self) -> None:
        data = RelatedProductionSerializer(self.production).data
        assert set(data.keys()) == {"id", "title", "display_title", "artist_name", "display_artist_name", "media_gallery"}

    def test_display_title_uses_base_language_fallback(self) -> None:
        data = RelatedProductionSerializer(self.production).data
        assert data["display_title"] == "Related productie"


class TestRelatedTagSerializerFields(TestCase):
    """Verify the compact tag serializer used for related productions."""

    def setUp(self) -> None:
        self.tag = TagFactory.create(type="theme")

    def test_expected_fields_are_present(self) -> None:
        data = RelatedTagSerializer(self.tag).data
        assert set(data.keys()) == {"id", "name", "display_name"}


class TestProductionSeriesSerializer(TestCase):
    """Cover edge branches for aggregated series serialization."""

    def test_get_last_production_image_returns_none_without_last_production_id(self) -> None:
        tag = TagFactory.create()
        serializer = ProductionSeriesSerializer(context={"last_production_image_by_production_id": {1: "img"}})

        assert serializer.get_last_production_image(tag) is None


class TestProductionSerializerRelated(TestCase):
    """Cover the related-production fallback and deduplication logic."""

    def setUp(self) -> None:
        self.production = ProductionFactory.create()
        self.language = LanguageFactory.create(code="nl", name="Dutch")
        ProductionTranslationFactory.create(
            production=self.production,
            language=self.language,
            title="Hoofdproductie",
            artist_name="Hoofdmaker",
        )
        self.tag = TagFactory.create(type="theme")
        self.production.tags.add(self.tag)

        self.related_production = ProductionFactory.create()
        ProductionTranslationFactory.create(
            production=self.related_production,
            language=self.language,
            title="Gerelateerde productie",
            artist_name="Gerelateerde maker",
        )
        self.related_production.tags.add(self.tag)

    def test_related_falls_back_to_live_tags_and_deduplicates_rows(self) -> None:
        class FakeQueryset:
            def __init__(self, rows):
                self.rows = rows

            def exclude(self, **_kwargs):
                return self

            def select_related(self, *_args, **_kwargs):
                return self

            def prefetch_related(self, *_args, **_kwargs):
                return self

            def order_by(self, *_args, **_kwargs):
                return self

            def __iter__(self):
                return iter(self.rows)

        duplicate_rows = [
            SimpleNamespace(production=self.related_production, tag_id=self.tag.id),
            SimpleNamespace(production=self.related_production, tag_id=self.tag.id),
        ]

        with patch("apps.productions.serializers.ProductionTag.objects.filter", return_value=FakeQueryset(duplicate_rows)):
            data = ProductionSerializer(self.production, context={"include": {"related"}}).data

        assert "related" in data
        assert len(data["related"]) == 1
        assert data["related"][0]["tag"]["id"] == self.tag.id
        assert len(data["related"][0]["productions"]) == 1
        assert data["related"][0]["productions"][0]["id"] == self.related_production.id


# ---------------------------------------------------------------------------
# ProductionSerializer - scalar fields
# ---------------------------------------------------------------------------


class TestProductionSerializerScalarFields(TestCase):
    """Model -> dict for non-translated, non-nested fields."""

    def test_serializes_media_gallery_correctly(self) -> None:
        gallery = MediaGalleryFactory.create()
        production = ProductionFactory.create(media_gallery=gallery)
        data = ProductionSerializer(production).data
        assert data["media_gallery"] == {"id": gallery.pk, "name": gallery.name, "media_items": []}

    def test_serializes_null_media_gallery_correctly(self) -> None:
        production = ProductionFactory.create(media_gallery=None)
        data = ProductionSerializer(production).data
        assert data["media_gallery"] is None

    def test_serializes_attendance_mode_correctly(self) -> None:
        production = ProductionFactory.create(attendance_mode="offline")
        data = ProductionSerializer(production).data
        assert data["attendance_mode"] == "offline"

    def test_serializes_online_attendance_mode_correctly(self) -> None:
        production = ProductionFactory.create(attendance_mode="online")
        data = ProductionSerializer(production).data
        assert data["attendance_mode"] == "online"

    def test_serializes_blank_attendance_mode_correctly(self) -> None:
        production = ProductionFactory.create(attendance_mode="")
        data = ProductionSerializer(production).data
        assert data["attendance_mode"] == ""

    def test_serializes_performer_type_group_correctly(self) -> None:
        production = ProductionFactory.create(performer_type="group")
        data = ProductionSerializer(production).data
        assert data["performer_type"] == "group"

    def test_serializes_performer_type_solo_correctly(self) -> None:
        production = ProductionFactory.create(performer_type="solo")
        data = ProductionSerializer(production).data
        assert data["performer_type"] == "solo"


# ---------------------------------------------------------------------------
# ProductionSerializer - nested fields
# ---------------------------------------------------------------------------


class TestProductionSerializerNestedUitDatabaseTheme(TestCase):
    """Verify nested UitDatabaseTheme serialization."""

    def test_uit_database_theme_is_null_when_not_set(self) -> None:
        production = ProductionFactory.create(uit_database_theme=None)
        data = ProductionSerializer(production).data
        assert data["uit_database_theme"] is None

    def test_uit_database_theme_contains_id_and_name(self) -> None:
        theme = UitDatabaseThemeFactory.create(name="Jazz")
        production = ProductionFactory.create(uit_database_theme=theme)
        data = ProductionSerializer(production).data
        assert data["uit_database_theme"]["id"] == theme.id
        assert data["uit_database_theme"]["name"] == "Jazz"


class TestProductionSerializerNestedUitDatabaseType(TestCase):
    """Verify nested UitDatabaseType serialization."""

    def test_uit_database_type_is_null_when_not_set(self) -> None:
        production = ProductionFactory.create(uit_database_type=None)
        data = ProductionSerializer(production).data
        assert data["uit_database_type"] is None

    def test_uit_database_type_contains_id_and_name(self) -> None:
        db_type = UitDatabaseTypeFactory.create(name="Theater")
        production = ProductionFactory.create(uit_database_type=db_type)
        data = ProductionSerializer(production).data
        assert data["uit_database_type"]["id"] == db_type.id
        assert data["uit_database_type"]["name"] == "Theater"


class TestProductionSerializerNestedTags(TestCase):
    """Verify nested Tags serialization."""

    def test_tags_is_empty_list_when_no_tags(self) -> None:
        production = ProductionFactory.create()
        data = ProductionSerializer(production).data
        assert data["tags"] == []

    def test_tags_contains_tag_data(self) -> None:
        production = ProductionFactory.create()
        tag = TagFactory.create(type="theme")
        production.tags.add(tag)
        data = ProductionSerializer(production).data
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == tag.id

    def test_tags_contains_multiple_tags(self) -> None:
        production = ProductionFactory.create()
        tag_a = TagFactory.create(type="genre")
        tag_b = TagFactory.create(type="mood")
        production.tags.add(tag_a, tag_b)
        data = ProductionSerializer(production).data
        assert len(data["tags"]) == 2


# ---------------------------------------------------------------------------
# ProductionSerializer - translated fields (empty state)
# ---------------------------------------------------------------------------


class TestProductionSerializerTranslatedFieldsEmpty(TestCase):
    """Translated fields return an empty dict when no translations exist."""

    def setUp(self) -> None:
        self.production = ProductionFactory.create()

    def test_title_is_empty_dict_without_translations(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["title"] == {}

    def test_description_is_empty_dict_without_translations(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["description"] == {}

    def test_teaser_is_empty_dict_without_translations(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["teaser"] == {}

    def test_artist_name_is_empty_dict_without_translations(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["artist_name"] == {}

    def test_tagline_is_empty_dict_without_translations(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["tagline"] == {}


# ---------------------------------------------------------------------------
# ProductionSerializer - translated fields (populated state)
# ---------------------------------------------------------------------------


class TestProductionSerializerTranslatedFieldsPopulated(TestCase):
    """Translated fields return a dict keyed by language code when translations exist."""

    def setUp(self) -> None:
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

    def test_title_contains_language_code_key(self) -> None:
        data = ProductionSerializer(self.production).data
        assert "nl" in data["title"]

    def test_title_value_matches_translation(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["title"]["nl"] == "Nederlandse Titel"

    def test_description_value_matches_translation(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["description"]["nl"] == "Nederlandse beschrijving"

    def test_teaser_value_matches_translation(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["teaser"]["nl"] == "Nederlandse teaser"

    def test_artist_name_value_matches_translation(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["artist_name"]["nl"] == "Artiest NL"

    def test_tagline_value_matches_translation(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["tagline"]["nl"] == "Tagline NL"


# ---------------------------------------------------------------------------
# ProductionSerializer - translated fields (multiple languages)
# ---------------------------------------------------------------------------


class TestProductionSerializerMultipleTranslations(TestCase):
    """Multiple language translations are all present in the output dict."""

    def setUp(self) -> None:
        self.production = ProductionFactory.create()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        self.en = LanguageFactory.create(code="en", name="English")
        ProductionTranslationFactory.create(production=self.production, language=self.nl, title="Titel NL")
        ProductionTranslationFactory.create(production=self.production, language=self.en, title="Title EN")

    def test_title_contains_both_language_codes(self) -> None:
        data = ProductionSerializer(self.production).data
        assert "nl" in data["title"]
        assert "en" in data["title"]

    def test_title_nl_value_is_correct(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["title"]["nl"] == "Titel NL"

    def test_title_en_value_is_correct(self) -> None:
        data = ProductionSerializer(self.production).data
        assert data["title"]["en"] == "Title EN"

    def test_title_dict_has_exactly_two_entries(self) -> None:
        data = ProductionSerializer(self.production).data
        assert len(data["title"]) == 2


# ---------------------------------------------------------------------------
# ProductionSerializer - translated fields (blank values are omitted)
# ---------------------------------------------------------------------------


class TestProductionSerializerTranslatedFieldsOmitBlanks(TestCase):
    """Blank translated field values must not appear in the output dict."""

    def setUp(self) -> None:
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

    def test_blank_description_is_omitted_from_dict(self) -> None:
        data = ProductionSerializer(self.production).data
        assert "nl" not in data["description"]

    def test_non_blank_title_is_present_in_dict(self) -> None:
        data = ProductionSerializer(self.production).data
        assert "nl" in data["title"]


# ---------------------------------------------------------------------------
# Mixin inheritance
# ---------------------------------------------------------------------------


class TestProductionSerializerInheritance(TestCase):
    """ProductionSerializer must use TranslatableSerializerMixin."""

    def test_inherits_from_translatable_serializer_mixin(self) -> None:
        assert issubclass(ProductionSerializer, TranslatableSerializerMixin)


# ---------------------------------------------------------------------------
# ProductionTagSerializer - description field (empty state)
# ---------------------------------------------------------------------------


class TestProductionTagSerializerDescriptionEmpty(TestCase):
    """description is an empty dict when no translations exist."""

    def setUp(self) -> None:
        self.production_tag = ProductionTagFactory.create()

    def test_description_is_empty_dict_without_translations(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert data["description"] == {}

    def test_description_key_is_always_present(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert "description" in data


class TestProductionTagSerializerDescriptionPopulated(TestCase):
    """description returns a language-code dict when translations exist."""

    def setUp(self) -> None:
        self.production_tag = ProductionTagFactory.create()
        self.nl = LanguageFactory.create(code="nl")
        self.en = LanguageFactory.create(code="en")
        ProductionTagTranslationFactory.create(
            production_tag=self.production_tag,
            language=self.nl,
            description="Nederlandse context.",
        )
        ProductionTagTranslationFactory.create(
            production_tag=self.production_tag,
            language=self.en,
            description="English context.",
        )

    def test_description_contains_nl_key(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert "nl" in data["description"]

    def test_description_contains_en_key(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert "en" in data["description"]

    def test_description_nl_value_is_correct(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert data["description"]["nl"] == "Nederlandse context."

    def test_description_en_value_is_correct(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert data["description"]["en"] == "English context."

    def test_description_has_exactly_two_entries(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert len(data["description"]) == 2


class TestProductionTagSerializerToRepresentation(TestCase):
    """to_representation merges Tag fields first, then through-table fields."""

    def setUp(self) -> None:
        self.tag = TagFactory.create(type="theme")
        self.production_tag = ProductionTagFactory.create(tag=self.tag)

    def test_output_contains_tag_id(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert data["id"] == self.tag.id

    def test_output_contains_tag_type(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert data["type"] == "theme"

    def test_output_contains_description_from_through_table(self) -> None:
        data = ProductionTagSerializer(self.production_tag).data
        assert "description" in data

    def test_tag_fields_come_before_description_in_key_order(self) -> None:
        """description must not shadow a tag field with the same name."""
        data = ProductionTagSerializer(self.production_tag).data
        keys = list(data.keys())
        # id (from Tag) must appear before description (from through-table)
        assert keys.index("id") < keys.index("description")


class TestProductionSerializerTagsDescriptionEmpty(TestCase):
    def test_tag_entry_has_description_key(self) -> None:
        production = ProductionFactory.create()
        tag = TagFactory.create()
        production.tags.add(tag)
        data = ProductionSerializer(production).data
        assert "description" in data["tags"][0]

    def test_tag_entry_description_is_empty_dict_when_no_translations(self) -> None:
        production = ProductionFactory.create()
        tag = TagFactory.create()
        production.tags.add(tag)
        data = ProductionSerializer(production).data
        assert data["tags"][0]["description"] == {}


class TestProductionSerializerTagsDescriptionPopulated(TestCase):
    def setUp(self) -> None:
        self.production = ProductionFactory.create()
        self.tag = TagFactory.create(type="theme")
        self.production_tag = ProductionTagFactory.create(production=self.production, tag=self.tag)
        self.nl = LanguageFactory.create(code="nl")
        self.en = LanguageFactory.create(code="en")
        ProductionTagTranslationFactory.create(
            production_tag=self.production_tag,
            language=self.nl,
            description="Thema in NL context.",
        )
        ProductionTagTranslationFactory.create(
            production_tag=self.production_tag,
            language=self.en,
            description="Theme in EN context.",
        )

    def _tag_data(self):
        return ProductionSerializer(self.production).data["tags"][0]

    def test_description_nl_is_correct(self) -> None:
        assert self._tag_data()["description"]["nl"] == "Thema in NL context."

    def test_description_en_is_correct(self) -> None:
        assert self._tag_data()["description"]["en"] == "Theme in EN context."

    def test_description_has_two_entries(self) -> None:
        assert len(self._tag_data()["description"]) == 2

    def test_tag_id_is_still_present(self) -> None:
        assert self._tag_data()["id"] == self.tag.id

    def test_description_is_production_scoped(self) -> None:
        """A second production with the same tag gets its own (empty) description."""
        other_production = ProductionFactory.create()
        ProductionTagFactory.create(production=other_production, tag=self.tag)
        data = ProductionSerializer(other_production).data
        assert data["tags"][0]["description"] == {}


class TestProductionSerializerTagsMultipleTags(TestCase):
    def test_each_tag_entry_has_independent_description(self) -> None:
        production = ProductionFactory.create()
        tag_a = TagFactory.create(type="genre")
        tag_b = TagFactory.create(type="mood")
        pt_a = ProductionTagFactory.create(production=production, tag=tag_a)
        _pt_b = ProductionTagFactory.create(production=production, tag=tag_b)
        nl = LanguageFactory.create(code="nl")
        ProductionTagTranslationFactory.create(production_tag=pt_a, language=nl, description="Beschrijving A.")

        tags_data = {t["id"]: t for t in ProductionSerializer(production).data["tags"]}

        assert tags_data[tag_a.id]["description"]["nl"] == "Beschrijving A."
        assert tags_data[tag_b.id]["description"] == {}


# ---------------------------------------------------------------------------
# ProductionSerializer - first_event_start / last_event_end
# ---------------------------------------------------------------------------


def _dt(year, month, day, hour=0):
    return datetime(year, month, day, hour, tzinfo=UTC)


def _annotated(production):
    qs = Production.objects.annotate(
        first_event_start=Min("events__starts_at"),
        last_event_end=Max("events__ends_at"),
    )
    return ProductionSerializer(qs.get(pk=production.pk)).data


class TestProductionSerializerEventDateFieldsEmpty(TestCase):
    """Both fields are null when the production has no linked events."""

    def setUp(self) -> None:
        self.production = ProductionFactory.create()

    def test_first_event_start_is_null_without_events(self) -> None:
        assert _annotated(self.production)["first_event_start"] is None

    def test_last_event_end_is_null_without_events(self) -> None:
        assert _annotated(self.production)["last_event_end"] is None

    def test_first_event_start_key_is_present(self) -> None:
        assert "first_event_start" in _annotated(self.production)

    def test_last_event_end_key_is_present(self) -> None:
        assert "last_event_end" in _annotated(self.production)


class TestProductionSerializerEventDateFieldsPopulated(TestCase):
    """Fields reflect min(starts_at) and max(ends_at) over all linked events."""

    def setUp(self) -> None:
        self.production = ProductionFactory.create()
        EventFactory.create(production=self.production, starts_at=_dt(2025, 9, 20), ends_at=_dt(2025, 9, 20, 22))
        EventFactory.create(production=self.production, starts_at=_dt(2025, 9, 15), ends_at=_dt(2025, 9, 15, 21))
        EventFactory.create(production=self.production, starts_at=_dt(2025, 11, 1), ends_at=_dt(2025, 11, 1, 23))
        self.data = _annotated(self.production)

    def _parse(self, value):
        return datetime.fromisoformat(value)

    def test_first_event_start_is_the_earliest_starts_at(self) -> None:
        assert self._parse(self.data["first_event_start"]) == _dt(2025, 9, 15)

    def test_last_event_end_is_the_latest_ends_at(self) -> None:
        assert self._parse(self.data["last_event_end"]) == _dt(2025, 11, 1, 23)

    def test_first_event_start_is_not_the_last_inserted(self) -> None:
        assert self._parse(self.data["first_event_start"]) != _dt(2025, 11, 1)

    def test_timestamps_are_iso8601_strings(self) -> None:
        for field in ("first_event_start", "last_event_end"):
            value = self.data[field]
            assert isinstance(value, str)
            parsed = datetime.fromisoformat(value)
            assert parsed.tzinfo is not None
