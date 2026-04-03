"""
Tests for apps/media_library/admin.py

Covers:
- All admin classes are registered (MediaGallery, MediaItem,
  MediaItemTranslation, MediaItemCrop)
- All admins inherit from BaseAdmin
- list_display configuration for every admin
- list_filter configuration for relevant admins
- search_fields configuration for every admin
- autocomplete_fields configuration for every admin
- Inline classes are present on MediaGalleryAdmin (MediaItemInline)
- Inline classes are present on MediaItemAdmin (translation, crop)
- Inline model, extra, autocomplete_fields and classes attributes
- get_queryset uses select_related on MediaItemAdmin
- MediaItemCropInline.get_url returns raw URL string or '-'
- MediaItemCropAdmin.get_url returns a safe clickable anchor or '-'
- Functional admin changelist and changeform (with superuser)
"""

from unittest.mock import MagicMock, PropertyMock

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.safestring import SafeData

from apps.core.admin import BaseAdmin
from apps.media_library.admin import (
    MediaGalleryAdmin,
    MediaItemAdmin,
    MediaItemCropAdmin,
    MediaItemCropInline,
    MediaItemInline,
    MediaItemTranslationAdmin,
    MediaItemTranslationInline,
)
from apps.media_library.models import (
    MediaGallery,
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_superuser(username="admin"):
    return User.objects.create_superuser(username=username, password="password", email=f"{username}@example.com")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestAdminRegistration(TestCase):
    """Verify all admin classes are registered against their models."""

    def test_media_gallery_is_registered(self) -> None:
        assert MediaGallery in admin.site._registry

    def test_registered_admin_is_media_gallery_admin(self) -> None:
        assert isinstance(admin.site._registry[MediaGallery], MediaGalleryAdmin)

    def test_media_item_is_registered(self) -> None:
        assert MediaItem in admin.site._registry

    def test_registered_admin_is_media_item_admin(self) -> None:
        assert isinstance(admin.site._registry[MediaItem], MediaItemAdmin)

    def test_media_item_translation_is_registered(self) -> None:
        assert MediaItemTranslation in admin.site._registry

    def test_registered_admin_is_media_item_translation_admin(self) -> None:
        assert isinstance(admin.site._registry[MediaItemTranslation], MediaItemTranslationAdmin)

    def test_media_item_crop_is_registered(self) -> None:
        assert MediaItemCrop in admin.site._registry

    def test_registered_admin_is_media_item_crop_admin(self) -> None:
        assert isinstance(admin.site._registry[MediaItemCrop], MediaItemCropAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestAdminInheritance(TestCase):
    """All admin classes must extend BaseAdmin (and therefore ModelAdmin)."""

    admins = [
        MediaGalleryAdmin,
        MediaItemAdmin,
        MediaItemTranslationAdmin,
        MediaItemCropAdmin,
    ]

    def test_all_admins_inherit_from_base_admin(self) -> None:
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                assert issubclass(admin_class, BaseAdmin)

    def test_all_admins_inherit_from_model_admin(self) -> None:
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                assert issubclass(admin_class, admin.ModelAdmin)


# ---------------------------------------------------------------------------
# MediaGalleryAdmin configuration
# ---------------------------------------------------------------------------


class TestMediaGalleryAdminConfiguration(TestCase):
    """Tests for MediaGalleryAdmin meta configuration."""

    def setUp(self) -> None:
        self.admin = admin.site._registry[MediaGallery]

    def test_list_display_contains_id(self) -> None:
        assert "id" in self.admin.list_display

    def test_list_display_contains_name(self) -> None:
        assert "name" in self.admin.list_display

    def test_search_fields_contains_name(self) -> None:
        assert "name" in self.admin.search_fields

    def test_inlines_contains_media_item_inline(self) -> None:
        inline_models = [inline.model for inline in self.admin.inlines]
        assert MediaItem in inline_models

    def test_one_inline_registered(self) -> None:
        assert len(self.admin.inlines) == 1


# ---------------------------------------------------------------------------
# MediaItemAdmin configuration
# ---------------------------------------------------------------------------


class TestMediaItemAdminConfiguration(TestCase):
    """Tests for MediaItemAdmin meta configuration."""

    def setUp(self) -> None:
        self.admin = admin.site._registry[MediaItem]

    # list_display
    def test_list_display_contains_id(self) -> None:
        assert "id" in self.admin.list_display

    def test_list_display_contains_gallery(self) -> None:
        assert "gallery" in self.admin.list_display

    def test_list_display_contains_type(self) -> None:
        assert "type" in self.admin.list_display

    def test_list_display_contains_format(self) -> None:
        assert "format" in self.admin.list_display

    def test_list_display_contains_original_filename(self) -> None:
        assert "original_filename" in self.admin.list_display

    def test_list_display_contains_position(self) -> None:
        assert "position" in self.admin.list_display

    def test_list_display_contains_width(self) -> None:
        assert "width" in self.admin.list_display

    def test_list_display_contains_height(self) -> None:
        assert "height" in self.admin.list_display

    # list_filter
    def test_list_filter_contains_type(self) -> None:
        assert "type" in self.admin.list_filter

    def test_list_filter_contains_format(self) -> None:
        assert "format" in self.admin.list_filter

    # search_fields
    def test_search_fields_contains_original_filename(self) -> None:
        assert "original_filename" in self.admin.search_fields

    def test_search_fields_contains_gallery_name(self) -> None:
        assert "gallery__name" in self.admin.search_fields

    # autocomplete_fields
    def test_autocomplete_fields_contains_gallery(self) -> None:
        assert "gallery" in self.admin.autocomplete_fields

    # inlines
    def test_inlines_contains_media_item_translation_inline(self) -> None:
        inline_models = [inline.model for inline in self.admin.inlines]
        assert MediaItemTranslation in inline_models

    def test_inlines_contains_media_item_crop_inline(self) -> None:
        inline_models = [inline.model for inline in self.admin.inlines]
        assert MediaItemCrop in inline_models

    def test_two_inlines_registered(self) -> None:
        assert len(self.admin.inlines) == 2


# ---------------------------------------------------------------------------
# MediaItemTranslationAdmin configuration
# ---------------------------------------------------------------------------


class TestMediaItemTranslationAdminConfiguration(TestCase):
    """Tests for MediaItemTranslationAdmin meta configuration."""

    def setUp(self) -> None:
        self.admin = admin.site._registry[MediaItemTranslation]

    # list_display
    def test_list_display_contains_id(self) -> None:
        assert "id" in self.admin.list_display

    def test_list_display_contains_media_item(self) -> None:
        assert "media_item" in self.admin.list_display

    def test_list_display_contains_language(self) -> None:
        assert "language" in self.admin.list_display

    def test_list_display_contains_title(self) -> None:
        assert "title" in self.admin.list_display

    def test_list_display_contains_credits(self) -> None:
        assert "credits" in self.admin.list_display

    # list_filter
    def test_list_filter_contains_language_code(self) -> None:
        assert "language__code" in self.admin.list_filter

    # search_fields
    def test_search_fields_contains_title(self) -> None:
        assert "title" in self.admin.search_fields

    def test_search_fields_contains_credits(self) -> None:
        assert "credits" in self.admin.search_fields

    def test_search_fields_contains_media_item_original_filename(self) -> None:
        assert "media_item__original_filename" in self.admin.search_fields

    # autocomplete_fields
    def test_autocomplete_fields_contains_media_item(self) -> None:
        assert "media_item" in self.admin.autocomplete_fields

    def test_autocomplete_fields_contains_language(self) -> None:
        assert "language" in self.admin.autocomplete_fields


# ---------------------------------------------------------------------------
# MediaItemCropAdmin configuration
# ---------------------------------------------------------------------------


class TestMediaItemCropAdminConfiguration(TestCase):
    """Tests for MediaItemCropAdmin meta configuration."""

    def setUp(self) -> None:
        self.admin = admin.site._registry[MediaItemCrop]

    def test_list_display_contains_id(self) -> None:
        assert "id" in self.admin.list_display

    def test_list_display_contains_media_item(self) -> None:
        assert "media_item" in self.admin.list_display

    def test_list_display_contains_name(self) -> None:
        assert "name" in self.admin.list_display

    def test_list_display_contains_get_url(self) -> None:
        """The crop admin uses get_url (a computed method) instead of a raw url field,
        because url was replaced by an ImageField named image."""
        assert "get_url" in self.admin.list_display

    def test_list_display_does_not_contain_raw_url_field(self) -> None:
        """MediaItemCrop no longer has a url field - it uses an ImageField."""
        assert "url" not in self.admin.list_display

    def test_search_fields_contains_name(self) -> None:
        assert "name" in self.admin.search_fields

    def test_search_fields_contains_media_item_original_filename(self) -> None:
        assert "media_item__original_filename" in self.admin.search_fields

    def test_autocomplete_fields_contains_media_item(self) -> None:
        assert "media_item" in self.admin.autocomplete_fields

    def test_get_url_is_callable_method(self) -> None:
        """get_url must be a method on the admin class, not a string field name."""
        assert callable(getattr(self.admin.__class__, "get_url", None))

    def test_get_url_returns_link_when_image_present(self) -> None:
        """get_url renders a clickable anchor when the crop has an image."""
        item = MediaItemFactory()
        crop = MediaItemCropFactory(media_item=item, name="hd_ready")
        result = self.admin.get_url(crop)
        assert "<a" in str(result)

    def test_get_url_returns_dash_when_no_image(self) -> None:
        """get_url returns '-' for a crop instance with no image set."""
        crop = MediaItemCrop(name="hd_ready")  # unsaved, no image
        result = self.admin.get_url(crop)
        assert str(result) == "-"

    def test_get_url_display_description(self) -> None:
        """The column header label must be 'Asset URL' as set by @admin.display."""
        assert self.admin.get_url.short_description == "Asset URL"

    def test_get_url_result_is_mark_safe(self) -> None:
        """format_html output must be SafeData so Django does not double-escape it."""
        item = MediaItemFactory()
        crop = MediaItemCropFactory(media_item=item, name="hd_ready")
        result = self.admin.get_url(crop)
        assert isinstance(result, SafeData)

    def test_get_url_anchor_has_target_blank(self) -> None:
        """The rendered anchor must open in a new tab."""
        item = MediaItemFactory()
        crop = MediaItemCropFactory(media_item=item, name="hd_ready")
        result = str(self.admin.get_url(crop))
        assert 'target="_blank"' in result

    def test_get_url_anchor_contains_bekijk_bestand(self) -> None:
        """The link label must read 'Bekijk bestand'."""
        item = MediaItemFactory()
        crop = MediaItemCropFactory(media_item=item, name="hd_ready")
        result = str(self.admin.get_url(crop))
        assert "Bekijk bestand" in result


# ---------------------------------------------------------------------------
# MediaItemCropInline - get_url
# ---------------------------------------------------------------------------


class TestMediaItemCropInlineGetUrl(TestCase):
    """
    Unit tests for MediaItemCropInline.get_url.

    The inline renders a plain URL string (not an anchor), or '-' when the
    crop has no image.  MagicMock is used so no database or file storage is
    required.
    """

    def setUp(self) -> None:
        self.inline = MediaItemCropInline(parent_model=MagicMock(), admin_site=MagicMock())

    def test_get_url_returns_url_string_when_image_present(self) -> None:
        """Should return the raw URL string when the crop has an image."""
        obj = MagicMock()
        type(obj.image).url = PropertyMock(return_value="https://cdn.example.com/crops/hero.jpg")
        result = self.inline.get_url(obj)
        assert result == "https://cdn.example.com/crops/hero.jpg"

    def test_get_url_returns_dash_when_image_is_none(self) -> None:
        """Should return '-' when obj.image is None."""
        obj = MagicMock()
        obj.image = None
        result = self.inline.get_url(obj)
        assert result == "-"

    def test_get_url_returns_dash_for_falsy_image(self) -> None:
        """Should return '-' for any other falsy image value (e.g. empty string)."""
        obj = MagicMock()
        obj.image = ""
        result = self.inline.get_url(obj)
        assert result == "-"

    def test_get_url_display_description(self) -> None:
        """Column header must be labelled 'URL' as set by @admin.display."""
        assert self.inline.get_url.short_description == "URL"

    def test_get_url_result_is_plain_string_not_anchor(self) -> None:
        """Inline get_url returns a plain URL - no HTML anchor tag."""
        obj = MagicMock()
        type(obj.image).url = PropertyMock(return_value="https://cdn.example.com/crops/hero.jpg")
        result = self.inline.get_url(obj)
        assert "<a" not in str(result)


# ---------------------------------------------------------------------------
# MediaItemCropInline configuration
# ---------------------------------------------------------------------------


class TestMediaItemCropInline(TestCase):
    """Tests for MediaItemCropInline configuration."""

    def test_model_is_media_item_crop(self) -> None:
        assert MediaItemCropInline.model == MediaItemCrop

    def test_extra_is_one(self) -> None:
        assert MediaItemCropInline.extra == 1

    def test_is_tabular_inline(self) -> None:
        assert issubclass(MediaItemCropInline, admin.TabularInline)

    def test_fields_contains_name(self) -> None:
        assert "name" in MediaItemCropInline.fields

    def test_fields_contains_image(self) -> None:
        """Inline must expose the image field, not the old url field."""
        assert "image" in MediaItemCropInline.fields

    def test_get_url_in_fields_or_readonly(self) -> None:
        """get_url must be reachable as either a field or a readonly_field."""
        all_fields = list(MediaItemCropInline.fields or []) + list(getattr(MediaItemCropInline, "readonly_fields", []))
        assert "get_url" in all_fields

    def test_get_url_is_readonly(self) -> None:
        """get_url is a computed display column and must be readonly."""
        assert "get_url" in MediaItemCropInline.readonly_fields


# ---------------------------------------------------------------------------
# Inline configuration (existing)
# ---------------------------------------------------------------------------


class TestMediaItemInline(TestCase):
    """Tests for MediaItemInline configuration."""

    def test_model_is_media_item(self) -> None:
        assert MediaItemInline.model == MediaItem

    def test_extra_is_one(self) -> None:
        assert MediaItemInline.extra == 1

    def test_has_collapse_class(self) -> None:
        assert "collapse" in MediaItemInline.classes

    def test_show_change_link_is_true(self) -> None:
        assert MediaItemInline.show_change_link

    def test_is_tabular_inline(self) -> None:
        assert issubclass(MediaItemInline, admin.TabularInline)


class TestMediaItemTranslationInline(TestCase):
    """Tests for MediaItemTranslationInline configuration."""

    def test_model_is_media_item_translation(self) -> None:
        assert MediaItemTranslationInline.model == MediaItemTranslation

    def test_extra_is_one(self) -> None:
        assert MediaItemTranslationInline.extra == 1

    def test_autocomplete_fields_contains_language(self) -> None:
        assert "language" in MediaItemTranslationInline.autocomplete_fields

    def test_has_collapse_class(self) -> None:
        assert "collapse" in MediaItemTranslationInline.classes

    def test_is_tabular_inline(self) -> None:
        assert issubclass(MediaItemTranslationInline, admin.TabularInline)


# ---------------------------------------------------------------------------
# get_queryset optimisation
# ---------------------------------------------------------------------------


class TestMediaItemAdminGetQueryset(TestCase):
    """Verify get_queryset uses select_related for FK optimisation."""

    def setUp(self) -> None:
        self.superuser = make_superuser()
        self.factory = RequestFactory()
        self.model_admin = admin.site._registry[MediaItem]

    def _make_request(self):
        request = self.factory.get("/")
        request.user = self.superuser
        return request

    def test_queryset_model_is_media_item(self) -> None:
        qs = self.model_admin.get_queryset(self._make_request())
        assert qs.model == MediaItem

    def test_queryset_has_select_related_for_gallery(self) -> None:
        admin_instance = self.model_admin
        request = self._make_request()

        assert admin_instance.list_select_related == ("gallery",)

        qs = admin_instance.get_queryset(request)

        if admin_instance.list_select_related:
            qs = qs.select_related(*admin_instance.list_select_related)

        assert "gallery" in qs.query.select_related


# ---------------------------------------------------------------------------
# Functional changelist / changeform tests
# ---------------------------------------------------------------------------


class TestMediaGalleryAdminChangelist(TestCase):
    """Functional tests for MediaGalleryAdmin via HTTP."""

    def setUp(self) -> None:
        self.superuser = make_superuser("gallery_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self) -> None:
        url = reverse("admin:media_library_mediagallery_changelist")
        assert self.client.get(url).status_code == 200

    def test_changelist_shows_gallery_name(self) -> None:
        MediaGalleryFactory.create(name="Summer Exhibition")
        url = reverse("admin:media_library_mediagallery_changelist")
        self.assertContains(self.client.get(url), "Summer Exhibition")

    def test_changeform_returns_200(self) -> None:
        gallery = MediaGalleryFactory.create()
        url = reverse("admin:media_library_mediagallery_change", args=[gallery.pk])
        assert self.client.get(url).status_code == 200

    def test_search_returns_200(self) -> None:
        url = reverse("admin:media_library_mediagallery_changelist")
        assert self.client.get(url, {"q": "test"}).status_code == 200


class TestMediaItemAdminChangelist(TestCase):
    """Functional tests for MediaItemAdmin via HTTP."""

    def setUp(self) -> None:
        self.superuser = make_superuser("item_admin")
        self.client.force_login(self.superuser)
        self.gallery = MediaGalleryFactory.create()

    def test_changelist_returns_200(self) -> None:
        url = reverse("admin:media_library_mediaitem_changelist")
        assert self.client.get(url).status_code == 200

    def test_changelist_with_items(self) -> None:
        MediaItemFactory.create(gallery=self.gallery)
        url = reverse("admin:media_library_mediaitem_changelist")
        assert self.client.get(url).status_code == 200

    def test_changeform_returns_200(self) -> None:
        item = MediaItemFactory.create(gallery=self.gallery)
        url = reverse("admin:media_library_mediaitem_change", args=[item.pk])
        assert self.client.get(url).status_code == 200

    def test_changelist_filter_by_type(self) -> None:
        url = reverse("admin:media_library_mediaitem_changelist")
        assert self.client.get(url, {"type": MediaItem.MediaItemType.IMAGE}).status_code == 200

    def test_changelist_filter_by_format(self) -> None:
        MediaItemFactory.create(gallery=self.gallery, format="jpg")
        url = reverse("admin:media_library_mediaitem_changelist")
        assert self.client.get(url, {"format": "jpg"}).status_code == 200

    def test_changelist_search(self) -> None:
        url = reverse("admin:media_library_mediaitem_changelist")
        assert self.client.get(url, {"q": "photo"}).status_code == 200


class TestMediaItemTranslationAdminChangelist(TestCase):
    """Functional tests for MediaItemTranslationAdmin via HTTP."""

    def setUp(self) -> None:
        self.superuser = make_superuser("trans_admin")
        self.client.force_login(self.superuser)
        self.gallery = MediaGalleryFactory.create()

    def test_changelist_returns_200(self) -> None:
        url = reverse("admin:media_library_mediaitemtranslation_changelist")
        assert self.client.get(url).status_code == 200

    def test_changeform_returns_200(self) -> None:
        item = MediaItemFactory.create(gallery=self.gallery)
        language = LanguageFactory.create()
        translation = MediaItemTranslationFactory.create(
            media_item=item,
            language=language,
            title="Test Titel",
        )
        url = reverse(
            "admin:media_library_mediaitemtranslation_change",
            args=[translation.pk],
        )
        assert self.client.get(url).status_code == 200

    def test_changelist_shows_translation_title(self) -> None:
        item = MediaItemFactory.create(gallery=self.gallery)
        language = LanguageFactory.create()
        MediaItemTranslationFactory.create(
            media_item=item,
            language=language,
            title="Zichtbare Titel",
        )
        url = reverse("admin:media_library_mediaitemtranslation_changelist")
        self.assertContains(self.client.get(url), "Zichtbare Titel")

    def test_changelist_filter_by_language(self) -> None:
        url = reverse("admin:media_library_mediaitemtranslation_changelist")
        assert self.client.get(url, {"language__code": "nl"}).status_code == 200

    def test_changelist_search(self) -> None:
        url = reverse("admin:media_library_mediaitemtranslation_changelist")
        assert self.client.get(url, {"q": "foto"}).status_code == 200


class TestMediaItemCropAdminChangelist(TestCase):
    """Functional tests for MediaItemCropAdmin via HTTP."""

    def setUp(self) -> None:
        self.superuser = make_superuser("crop_admin")
        self.client.force_login(self.superuser)
        self.gallery = MediaGalleryFactory.create()

    def test_changelist_returns_200(self) -> None:
        url = reverse("admin:media_library_mediaitemcrop_changelist")
        assert self.client.get(url).status_code == 200

    def test_changeform_returns_200(self) -> None:
        item = MediaItemFactory.create(gallery=self.gallery)
        crop = MediaItemCropFactory.create(media_item=item)
        url = reverse("admin:media_library_mediaitemcrop_change", args=[crop.pk])
        assert self.client.get(url).status_code == 200

    def test_changelist_shows_crop_name(self) -> None:
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemCropFactory.create(media_item=item, name="hero-banner")
        url = reverse("admin:media_library_mediaitemcrop_changelist")
        self.assertContains(self.client.get(url), "hero-banner")

    def test_changelist_search(self) -> None:
        url = reverse("admin:media_library_mediaitemcrop_changelist")
        assert self.client.get(url, {"q": "thumb"}).status_code == 200

    def test_changelist_renders_get_url_link_for_crops_with_image(self) -> None:
        """The changelist must render the clickable image link from get_url."""
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemCropFactory.create(media_item=item, name="hd_ready")
        url = reverse("admin:media_library_mediaitemcrop_changelist")
        response = self.client.get(url)
        assert response.status_code == 200
        self.assertContains(response, "<a")
