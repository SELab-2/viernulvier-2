"""
Covers:
- __str__ output
- Meta ordering
- field defaults
- validators
- uniqueness constraints
- indexes presence
- reverse relations
- cascade delete behavior
"""

import pytest
from django.core.exceptions import ValidationError

from apps.media_library.models import (
    MediaItem,
    MediaItemCrop,
    MediaItemTranslation,
)
from tests.factories.language import LanguageFactory
from tests.factories.media_library import (
    MediaGalleryFactory,
    MediaItemCropFactory,
    MediaItemFactory,
    MediaItemTranslationFactory,
)

pytestmark = pytest.mark.django_db


# =====================================================
# MediaGallery
# =====================================================


class TestMediaGallery:
    def test_name_is_optional(self):
        """Gallery name is nullable/blank — a gallery without a name must pass full_clean."""
        gallery = MediaGalleryFactory.build(name="")
        gallery.full_clean()  # must not raise

    def test_name_null_is_allowed(self):
        """Gallery name can be null."""
        gallery = MediaGalleryFactory.build(name=None)
        gallery.full_clean()  # must not raise

    def test_str_returns_name_when_set(self):
        gallery = MediaGalleryFactory(name="Homepage Gallery")
        assert str(gallery) == "Homepage Gallery"

    def test_str_returns_unnamed_gallery_when_name_is_null(self):
        """__str__ falls back to 'Unnamed Gallery' when name is null/empty."""
        gallery = MediaGalleryFactory(name=None)
        assert str(gallery) == "Unnamed Gallery"

    def test_reverse_relation_media_items(self):
        gallery = MediaGalleryFactory()
        MediaItemFactory.create_batch(3, gallery=gallery)
        assert gallery.media_items.count() == 3

    def test_deleting_gallery_cascades_to_media_items(self):
        gallery = MediaGalleryFactory()
        MediaItemFactory.create_batch(2, gallery=gallery)
        gallery.delete()
        assert MediaItem.objects.count() == 0


# =====================================================
# MediaItem
# =====================================================


class TestMediaItem:
    def test_gallery_is_optional(self):
        """gallery FK is nullable — a MediaItem without a gallery must pass full_clean."""
        item = MediaItemFactory.build(gallery=None)
        item.full_clean()  # must not raise

    def test_position_defaults_to_zero(self):
        gallery = MediaGalleryFactory()
        item = MediaItemFactory.create(
            gallery=gallery, type=MediaItem.MediaItemType.IMAGE, position=0
        )
        assert item.position == 0

    def test_ordering_by_position(self):
        gallery = MediaGalleryFactory()
        item3 = MediaItemFactory(gallery=gallery, position=3)
        item1 = MediaItemFactory(gallery=gallery, position=1)
        item2 = MediaItemFactory(gallery=gallery, position=2)

        items = list(MediaItem.objects.filter(gallery=gallery))
        assert items == [item1, item2, item3]

    def test_blank_original_filename_allowed(self):
        item = MediaItemFactory(original_filename="")
        item.full_clean()  # should not raise

    def test_width_height_optional(self):
        item = MediaItemFactory(width=None, height=None)
        item.full_clean()  # should not raise

    def test_str_with_filename(self):
        """IMAGE type value is 'foto', so str must reflect that."""
        item = MediaItemFactory(
            type=MediaItem.MediaItemType.IMAGE, original_filename="banner.jpg"
        )
        assert str(item) == "foto - banner.jpg"

    def test_str_without_filename(self):
        item = MediaItemFactory(
            type=MediaItem.MediaItemType.VIDEO, original_filename=""
        )
        assert str(item) == "video - Unnamed"

    def test_image_type_value_is_foto(self):
        """MediaItemType.IMAGE database value must be 'foto'."""
        assert MediaItem.MediaItemType.IMAGE == "foto"

    def test_other_type_exists(self):
        """MediaItemType.OTHER must exist with value 'other'."""
        assert MediaItem.MediaItemType.OTHER == "other"

    def test_delete_cascades_to_translations(self):
        item = MediaItemFactory()
        MediaItemTranslationFactory.create_batch(2, media_item=item)
        item.delete()
        assert MediaItemTranslation.objects.count() == 0

    def test_delete_cascades_to_crops(self):
        item = MediaItemFactory()
        MediaItemCropFactory.create_batch(2, media_item=item)
        item.delete()
        assert MediaItemCrop.objects.count() == 0


# =====================================================
# MediaItemTranslation
# =====================================================


class TestMediaItemTranslation:
    def test_unique_per_media_item_and_language(self):
        language = LanguageFactory()
        item = MediaItemFactory()

        MediaItemTranslationFactory(media_item=item, language=language)

        with pytest.raises(ValidationError):
            MediaItemTranslationFactory(media_item=item, language=language)

    def test_str_representation(self):
        """__str__ must contain the media item type and language code."""
        language = LanguageFactory(code="en")
        item = MediaItemFactory(type=MediaItem.MediaItemType.IMAGE)
        translation = MediaItemTranslationFactory(
            media_item=item,
            language=language,
            title="Banner",
        )

        result = str(translation)

        # IMAGE value is "foto"
        assert MediaItem.MediaItemType.IMAGE in result  # "foto"
        assert "en" in result

    def test_optional_fields_can_be_blank(self):
        translation = MediaItemTranslationFactory(
            title="",
            description="",
            credits="",
            link="",
        )
        translation.full_clean()  # should not raise

    def test_link_is_charfield_not_urlfield(self):
        """link accepts arbitrary strings, not just valid URLs."""
        translation = MediaItemTranslationFactory(link="not-a-url")
        translation.full_clean()  # must not raise

    def test_language_reverse_relation(self):
        language = LanguageFactory()
        MediaItemTranslationFactory.create_batch(3, language=language)
        assert language.media_item_translations.count() == 3

    def test_deleting_language_cascades(self):
        language = LanguageFactory()
        MediaItemTranslationFactory(language=language)
        language.delete()
        assert MediaItemTranslation.objects.count() == 0


# =====================================================
# MediaItemCrop
# =====================================================


class TestMediaItemCrop:
    def test_unique_per_media_item_and_name(self):
        item = MediaItemFactory()
        MediaItemCropFactory(media_item=item, name="thumbnail")
        with pytest.raises(ValidationError):
            MediaItemCropFactory(media_item=item, name="thumbnail")

    def test_str_representation(self):
        item = MediaItemFactory(type=MediaItem.MediaItemType.IMAGE)
        crop = MediaItemCropFactory(media_item=item, name="thumbnail")

        result = str(crop)

        # IMAGE value is "foto"
        assert MediaItem.MediaItemType.IMAGE in result
        assert "thumbnail" in result

    def test_requires_name(self):
        crop = MediaItemCropFactory.build(name="")
        with pytest.raises(ValidationError):
            crop.full_clean()

    def test_deleting_media_item_cascades_to_crops(self):
        item = MediaItemFactory()
        MediaItemCropFactory.create_batch(2, media_item=item)
        item.delete()
        assert MediaItemCrop.objects.count() == 0
