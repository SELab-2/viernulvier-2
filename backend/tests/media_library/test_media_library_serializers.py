"""
Tests for apps/media_library/serializers.py

Covers:
- MediaItemCropSerializer field presence and completeness
- MediaItemSerializer field presence and completeness
- MediaGallerySerializer field presence and completeness
- MediaItemSerializer serialization of scalar fields (type, format, original_filename,
  position, width, height)
- Nested MediaItemCropSerializer output on MediaItemSerializer
- image_url is a computed field derived from the ImageField
- image_url returns None when no image is stored
- image_url builds an absolute URI when a request is in serializer context
- Translated fields (title, description, credits, link) returned as dicts
- Translated fields return empty dict when no translations exist
- Translated fields omit blank/falsy values per language
- Multiple translations are all included in the dict
- MediaItemSerializer inherits from TranslatableSerializerMixin
- MediaGallerySerializer nests MediaItemSerializer via media_items
- MediaGallerySerializer media_items are ordered by position
"""

from django.test import RequestFactory, TestCase, override_settings

from apps.core.serializers import TranslatableSerializerMixin
from apps.media_library.models import (
    MediaGallery,
    MediaItem,
    MediaItemCrop,
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _make_request(url="http://testserver/"):
    """Return a minimal DRF-compatible request object."""
    factory = RequestFactory()
    request = factory.get(url)
    # Wrap in DRF request so build_absolute_uri works
    from rest_framework.request import Request

    return Request(request)


# ---------------------------------------------------------------------------
# MediaItemCropSerializer - field presence
# ---------------------------------------------------------------------------


class TestMediaItemCropSerializerFields(TestCase):
    """Verify field presence and output of MediaItemCropSerializer."""

    def setUp(self):
        gallery = MediaGalleryFactory.create()
        item = MediaItemFactory.create(gallery=gallery)
        # ImageField stores a file path; the URL is derived via storage.
        # In tests with default FileSystemStorage, image.url == MEDIA_URL + name.
        self.crop = MediaItemCropFactory.create(
            media_item=item,
            name="banner",
        )

    def test_expected_fields_are_present(self):
        data = MediaItemCropSerializer(self.crop).data
        for field in ("id", "name", "image_url"):
            with self.subTest(field=field):
                self.assertIn(field, data)

    def test_no_extra_fields_are_exposed(self):
        data = MediaItemCropSerializer(self.crop).data
        self.assertEqual(set(data.keys()), {"id", "name", "image_url"})

    def test_url_field_not_in_output(self):
        """The old 'url' field no longer exists; only 'image_url' is exposed."""
        data = MediaItemCropSerializer(self.crop).data
        self.assertNotIn("url", data)

    def test_image_field_not_exposed_directly(self):
        """The raw 'image' ImageField is not in the serializer output."""
        data = MediaItemCropSerializer(self.crop).data
        self.assertNotIn("image", data)

    def test_name_value_is_correct(self):
        data = MediaItemCropSerializer(self.crop).data
        self.assertEqual(data["name"], "banner")

    def test_image_url_is_none_when_no_image(self):
        """A crop with no image stored returns None for image_url."""
        crop = MediaItemCrop(name="empty")
        data = MediaItemCropSerializer(crop).data
        self.assertIsNone(data["image_url"])

    @override_settings(MEDIA_URL="/media/")
    def test_image_url_contains_path_when_image_set(self):
        """When an image path is stored, image_url returns a non-empty string."""
        data = MediaItemCropSerializer(self.crop).data
        # The crop factory assigns an image; image_url must not be None
        if self.crop.image:
            self.assertIsNotNone(data["image_url"])
            self.assertIsInstance(data["image_url"], str)

    def test_image_url_builds_absolute_uri_with_request_in_context(self):
        """When a request is in the serializer context, image_url is absolute."""
        if not self.crop.image:
            self.skipTest("crop has no image")
        request = _make_request()
        data = MediaItemCropSerializer(self.crop, context={"request": request}).data
        image_url = data["image_url"]
        self.assertIsNotNone(image_url)
        self.assertTrue(image_url.startswith("http"), f"Expected absolute URL, got: {image_url}")

    def test_image_url_without_request_in_context_is_relative_or_absolute(self):
        """Without a request in context, image_url is still a non-empty string."""
        if not self.crop.image:
            self.skipTest("crop has no image")
        data = MediaItemCropSerializer(self.crop, context={}).data
        self.assertIsNotNone(data["image_url"])
        self.assertIsInstance(data["image_url"], str)
        self.assertGreater(len(data["image_url"]), 0)


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
        MediaItemCropFactory.create(media_item=self.item, name="thumbnail")
        MediaItemCropFactory.create(media_item=self.item, name="banner")
        data = serialize_item(self.item)
        self.assertEqual(len(data["crops"]), 2)

    def test_crop_name_field_is_correct(self):
        MediaItemCropFactory.create(media_item=self.item, name="thumbnail")
        data = serialize_item(self.item)
        crop = data["crops"][0]
        self.assertEqual(crop["name"], "thumbnail")

    def test_crop_has_id_field(self):
        MediaItemCropFactory.create(media_item=self.item, name="thumbnail")
        data = serialize_item(self.item)
        self.assertIn("id", data["crops"][0])

    def test_crop_has_image_url_field(self):
        """Crops expose image_url, not url or image directly."""
        MediaItemCropFactory.create(media_item=self.item, name="thumbnail")
        data = serialize_item(self.item)
        self.assertIn("image_url", data["crops"][0])

    def test_crop_does_not_expose_raw_url_field(self):
        MediaItemCropFactory.create(media_item=self.item, name="thumbnail")
        data = serialize_item(self.item)
        self.assertNotIn("url", data["crops"][0])

    def test_crop_does_not_expose_raw_image_field(self):
        """The raw ImageField path must not be directly exposed."""
        MediaItemCropFactory.create(media_item=self.item, name="thumbnail")
        data = serialize_item(self.item)
        self.assertNotIn("image", data["crops"][0])

    def test_crop_uses_media_item_crop_serializer_fields(self):
        MediaItemCropFactory.create(media_item=self.item, name="thumbnail")
        data = serialize_item(self.item)
        self.assertEqual(set(data["crops"][0].keys()), {"id", "name", "image_url"})


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
        MediaItemCropFactory.create(media_item=item, name="thumb")
        data = serialize_gallery(self.gallery)
        self.assertEqual(len(data["media_items"][0]["crops"]), 1)

    def test_nested_crop_exposes_image_url_not_url(self):
        """Nested crops must use the image_url field, not the old url field."""
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemCropFactory.create(media_item=item, name="thumb")
        data = serialize_gallery(self.gallery)
        crop_data = data["media_items"][0]["crops"][0]
        self.assertIn("image_url", crop_data)
        self.assertNotIn("url", crop_data)
        self.assertNotIn("image", crop_data)

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
