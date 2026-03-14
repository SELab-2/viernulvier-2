"""
Tests for apps/media_library/serializers.py

Covers:
- MediaItemCropSerializer field presence and completeness
- MediaItemSerializer field presence and completeness
- MediaGallerySerializer field presence and completeness
- MediaItemSerializer serialization of scalar fields (type, format, original_filename,
  position, width, height)
- Nested MediaItemCropSerializer output on MediaItemSerializer
- Translated fields (title, description, credits, link) returned as dicts
- Translated fields return empty dict when no translations exist
- Translated fields omit blank/falsy values per language
- Multiple translations are all included in the dict
- MediaItemSerializer inherits from TranslatableSerializerMixin
- MediaGallerySerializer nests MediaItemSerializer via media_items
- MediaGallerySerializer media_items are ordered by position
"""

from django.test import TestCase

from apps.core.serializers import TranslatableSerializerMixin
from apps.media_library.models import (
    MediaGallery,
    MediaItem,
)
from apps.media_library.serializers import (
    MediaGallerySerializer,
    MediaItemCropSerializer,
    MediaItemSerializer,
)
from tests.factories.language import LanguageFactory
from tests.factories.media_library import (
    MediaGalleryFactory,
    MediaItemCropFactory,
    MediaItemFactory,
    MediaItemTranslationFactory,
)


def serialize_item(item):
    """Re-fetch item with all relations to mirror the viewset queryset."""
    item_qs = MediaItem.objects.prefetch_related(
        "translations__language",
        "crops",
    ).get(pk=item.pk)
    return MediaItemSerializer(item_qs).data


def serialize_gallery(gallery):
    """Re-fetch gallery with all relations to mirror the viewset queryset."""
    gallery_qs = MediaGallery.objects.prefetch_related(
        "media_items",
        "media_items__translations__language",
        "media_items__crops",
    ).get(pk=gallery.pk)
    return MediaGallerySerializer(gallery_qs).data


# ---------------------------------------------------------------------------
# MediaItemCropSerializer
# ---------------------------------------------------------------------------


class TestMediaItemCropSerializerFields(TestCase):
    """Verify field presence and output of MediaItemCropSerializer."""

    def setUp(self):
        gallery = MediaGalleryFactory.create()
        item = MediaItemFactory.create(gallery=gallery)
        self.crop = MediaItemCropFactory.create(
            media_item=item,
            name="banner",
            url="https://example.com/banner.jpg",
        )

    def test_expected_fields_are_present(self):
        data = MediaItemCropSerializer(self.crop).data
        for field in ("id", "name", "url"):
            with self.subTest(field=field):
                self.assertIn(field, data)

    def test_no_extra_fields_are_exposed(self):
        data = MediaItemCropSerializer(self.crop).data
        self.assertEqual(set(data.keys()), {"id", "name", "url"})

    def test_name_value_is_correct(self):
        data = MediaItemCropSerializer(self.crop).data
        self.assertEqual(data["name"], "banner")

    def test_url_value_is_correct(self):
        data = MediaItemCropSerializer(self.crop).data
        self.assertEqual(data["url"], "https://example.com/banner.jpg")


# ---------------------------------------------------------------------------
# MediaItemSerializer - field presence
# ---------------------------------------------------------------------------


class TestMediaItemSerializerFields(TestCase):
    """Verify all expected fields are present on MediaItemSerializer."""

    def setUp(self):
        gallery = MediaGalleryFactory.create()
        self.item = MediaItemFactory.create(gallery=gallery)

    def test_expected_fields_are_present(self):
        data = serialize_item(self.item)
        expected = {
            "id",
            "type",
            "format",
            "original_filename",
            "position",
            "width",
            "height",
            "title",
            "display_title",
            "description",
            "credits",
            "link",
            "crops",
        }
        for field in expected:
            with self.subTest(field=field):
                self.assertIn(field, data)

    def test_no_extra_fields_are_exposed(self):
        data = serialize_item(self.item)
        expected = {
            "id",
            "gallery",
            "type",
            "format",
            "original_filename",
            "position",
            "width",
            "height",
            "title",
            "display_title",
            "description",
            "credits",
            "link",
            "crops",
        }
        self.assertEqual(set(data.keys()), expected)


# ---------------------------------------------------------------------------
# MediaItemSerializer - scalar fields
# ---------------------------------------------------------------------------


class TestMediaItemSerializerScalarFields(TestCase):
    """Verify scalar fields are serialized correctly on MediaItemSerializer."""

    def setUp(self):
        gallery = MediaGalleryFactory.create()
        self.item = MediaItemFactory.create(
            gallery=gallery,
            type=MediaItem.MediaItemType.VIDEO,
            format="mp4",
            original_filename="clip.mp4",
            position=3,
            width=1920,
            height=1080,
        )
        self.data = serialize_item(self.item)

    def test_type_is_correct(self):
        self.assertEqual(self.data["type"], "video")

    def test_format_is_correct(self):
        self.assertEqual(self.data["format"], "mp4")

    def test_original_filename_is_correct(self):
        self.assertEqual(self.data["original_filename"], "clip.mp4")

    def test_position_is_correct(self):
        self.assertEqual(self.data["position"], 3)

    def test_width_is_correct(self):
        self.assertEqual(self.data["width"], 1920)

    def test_height_is_correct(self):
        self.assertEqual(self.data["height"], 1080)

    def test_width_is_none_when_not_set(self):
        gallery = MediaGalleryFactory.create(name="no-dims")
        item = MediaItemFactory.create(
            gallery=gallery,
            original_filename="nodims.jpg",
            width=None,
        )
        data = serialize_item(item)
        self.assertIsNone(data["width"])

    def test_height_is_none_when_not_set(self):
        gallery = MediaGalleryFactory.create(name="no-dims-2")
        item = MediaItemFactory.create(
            gallery=gallery,
            original_filename="nodims2.jpg",
            height=None,
        )
        data = serialize_item(item)
        self.assertIsNone(data["height"])


# ---------------------------------------------------------------------------
# MediaItemSerializer - crops
# ---------------------------------------------------------------------------


class TestMediaItemSerializerCrops(TestCase):
    """Verify nested crops are serialized correctly."""

    def setUp(self):
        gallery = MediaGalleryFactory.create()
        self.item = MediaItemFactory.create(gallery=gallery)

    def test_crops_is_empty_list_when_no_crops(self):
        data = serialize_item(self.item)
        self.assertEqual(data["crops"], [])

    def test_crops_contains_one_crop(self):
        MediaItemCropFactory.create(media_item=self.item, name="thumbnail")
        data = serialize_item(self.item)
        self.assertEqual(len(data["crops"]), 1)

    def test_crops_contains_multiple_crops(self):
        MediaItemCropFactory.create(
            media_item=self.item,
            name="thumbnail",
            url="https://example.com/thumb.jpg",
        )
        MediaItemCropFactory.create(
            media_item=self.item,
            name="banner",
            url="https://example.com/banner.jpg",
        )
        data = serialize_item(self.item)
        self.assertEqual(len(data["crops"]), 2)

    def test_crop_fields_are_correct(self):
        MediaItemCropFactory.create(
            media_item=self.item,
            name="thumbnail",
            url="https://example.com/thumb.jpg",
        )
        data = serialize_item(self.item)
        crop = data["crops"][0]
        self.assertEqual(crop["name"], "thumbnail")
        self.assertEqual(crop["url"], "https://example.com/thumb.jpg")
        self.assertIn("id", crop)

    def test_crop_uses_media_item_crop_serializer_fields(self):
        MediaItemCropFactory.create(media_item=self.item)
        data = serialize_item(self.item)
        self.assertEqual(set(data["crops"][0].keys()), {"id", "name", "url"})


# ---------------------------------------------------------------------------
# MediaItemSerializer - translated fields
# ---------------------------------------------------------------------------


class TestMediaItemSerializerTranslatedFields(TestCase):
    """Verify translated fields are returned as language-keyed dicts."""

    def setUp(self):
        self.gallery = MediaGalleryFactory.create()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        self.en = LanguageFactory.create(code="en", name="English")

    def test_title_is_dict(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.nl,
            title="NL Titel",
        )
        data = serialize_item(item)
        self.assertIsInstance(data["title"], dict)

    def test_title_contains_correct_value(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.nl,
            title="NL Titel",
        )
        data = serialize_item(item)
        self.assertEqual(data["title"]["nl"], "NL Titel")

    def test_description_contains_correct_value(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.nl,
            description="Omschrijving",
        )
        data = serialize_item(item)
        self.assertEqual(data["description"]["nl"], "Omschrijving")

    def test_credits_contains_correct_value(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.nl,
            credits="Foto: Jan",
        )
        data = serialize_item(item)
        self.assertEqual(data["credits"]["nl"], "Foto: Jan")

    def test_link_contains_correct_value(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.nl,
            link="https://example.com/nl",
        )
        data = serialize_item(item)
        self.assertEqual(data["link"]["nl"], "https://example.com/nl")

    def test_translated_field_returns_empty_dict_when_no_translations(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        data = serialize_item(item)
        self.assertEqual(data["title"], {})
        self.assertEqual(data["description"], {})
        self.assertEqual(data["credits"], {})
        self.assertEqual(data["link"], {})

    def test_blank_field_is_omitted_from_dict(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.nl,
            title="",
            description="Omschrijving",
        )
        data = serialize_item(item)
        self.assertNotIn("nl", data["title"])
        self.assertIn("nl", data["description"])

    def test_multiple_languages_are_included(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.nl,
            title="NL Titel",
        )
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.en,
            title="EN Title",
        )
        data = serialize_item(item)
        self.assertIn("nl", data["title"])
        self.assertIn("en", data["title"])

    def test_multiple_languages_have_correct_values(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.nl,
            title="NL Titel",
        )
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.en,
            title="EN Title",
        )
        data = serialize_item(item)
        self.assertEqual(data["title"]["nl"], "NL Titel")
        self.assertEqual(data["title"]["en"], "EN Title")

    def test_only_languages_with_values_are_included(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.nl,
            title="NL Titel",
        )
        MediaItemTranslationFactory.create(
            media_item=item,
            language=self.en,
            title="",
        )
        data = serialize_item(item)
        self.assertIn("nl", data["title"])
        self.assertNotIn("en", data["title"])


# ---------------------------------------------------------------------------
# MediaItemSerializer - inheritance
# ---------------------------------------------------------------------------


class TestMediaItemSerializerInheritance(TestCase):
    """MediaItemSerializer must inherit from TranslatableSerializerMixin."""

    def test_inherits_from_translatable_serializer_mixin(self):
        self.assertTrue(issubclass(MediaItemSerializer, TranslatableSerializerMixin))


# ---------------------------------------------------------------------------
# MediaGallerySerializer - field presence
# ---------------------------------------------------------------------------


class TestMediaGallerySerializerFields(TestCase):
    """Verify all expected fields are present on MediaGallerySerializer."""

    def setUp(self):
        self.gallery = MediaGalleryFactory.create(name="My Gallery")

    def test_expected_fields_are_present(self):
        data = serialize_gallery(self.gallery)
        for field in ("id", "name", "media_items"):
            with self.subTest(field=field):
                self.assertIn(field, data)

    def test_no_extra_fields_are_exposed(self):
        data = serialize_gallery(self.gallery)
        self.assertEqual(set(data.keys()), {"id", "name", "media_items"})

    def test_name_value_is_correct(self):
        data = serialize_gallery(self.gallery)
        self.assertEqual(data["name"], "My Gallery")


# ---------------------------------------------------------------------------
# MediaGallerySerializer - nested media_items
# ---------------------------------------------------------------------------


class TestMediaGallerySerializerMediaItems(TestCase):
    """Verify nested media_items are serialized correctly on MediaGallerySerializer."""

    def setUp(self):
        self.gallery = MediaGalleryFactory.create()

    def test_media_items_is_empty_list_when_no_items(self):
        data = serialize_gallery(self.gallery)
        self.assertEqual(data["media_items"], [])

    def test_media_items_contains_one_item(self):
        MediaItemFactory.create(gallery=self.gallery)
        data = serialize_gallery(self.gallery)
        self.assertEqual(len(data["media_items"]), 1)

    def test_media_items_contains_multiple_items(self):
        MediaItemFactory.create(gallery=self.gallery, position=0, original_filename="a.jpg")
        MediaItemFactory.create(gallery=self.gallery, position=1, original_filename="b.jpg")
        data = serialize_gallery(self.gallery)
        self.assertEqual(len(data["media_items"]), 2)

    def test_media_items_uses_media_item_serializer_fields(self):
        MediaItemFactory.create(gallery=self.gallery)
        data = serialize_gallery(self.gallery)
        expected = {
            "id",
            "gallery",
            "type",
            "format",
            "original_filename",
            "position",
            "width",
            "height",
            "title",
            "display_title",
            "description",
            "credits",
            "link",
            "crops",
        }
        self.assertEqual(set(data["media_items"][0].keys()), expected)

    def test_media_items_are_ordered_by_position(self):
        MediaItemFactory.create(gallery=self.gallery, position=2, original_filename="second.jpg")
        MediaItemFactory.create(gallery=self.gallery, position=0, original_filename="first.jpg")
        MediaItemFactory.create(gallery=self.gallery, position=1, original_filename="middle.jpg")
        data = serialize_gallery(self.gallery)
        positions = [item["position"] for item in data["media_items"]]
        self.assertEqual(positions, sorted(positions))

    def test_nested_item_includes_crops(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemCropFactory.create(
            media_item=item,
            name="thumb",
            url="https://example.com/t.jpg",
        )
        data = serialize_gallery(self.gallery)
        self.assertEqual(len(data["media_items"][0]["crops"]), 1)

    def test_nested_item_includes_translated_title(self):
        nl = LanguageFactory.create(code="nl")
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemTranslationFactory.create(
            media_item=item,
            language=nl,
            title="Geneste Titel",
        )
        data = serialize_gallery(self.gallery)
        self.assertEqual(data["media_items"][0]["title"]["nl"], "Geneste Titel")
