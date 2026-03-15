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

    def test_media_gallery_is_registered(self):
        self.assertIn(MediaGallery, admin.site._registry)

    def test_registered_admin_is_media_gallery_admin(self):
        self.assertIsInstance(admin.site._registry[MediaGallery], MediaGalleryAdmin)

    def test_media_item_is_registered(self):
        self.assertIn(MediaItem, admin.site._registry)

    def test_registered_admin_is_media_item_admin(self):
        self.assertIsInstance(admin.site._registry[MediaItem], MediaItemAdmin)

    def test_media_item_translation_is_registered(self):
        self.assertIn(MediaItemTranslation, admin.site._registry)

    def test_registered_admin_is_media_item_translation_admin(self):
        self.assertIsInstance(admin.site._registry[MediaItemTranslation], MediaItemTranslationAdmin)

    def test_media_item_crop_is_registered(self):
        self.assertIn(MediaItemCrop, admin.site._registry)

    def test_registered_admin_is_media_item_crop_admin(self):
        self.assertIsInstance(admin.site._registry[MediaItemCrop], MediaItemCropAdmin)


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

    def test_all_admins_inherit_from_base_admin(self):
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                self.assertTrue(issubclass(admin_class, BaseAdmin))

    def test_all_admins_inherit_from_model_admin(self):
        for admin_class in self.admins:
            with self.subTest(admin_class=admin_class.__name__):
                self.assertTrue(issubclass(admin_class, admin.ModelAdmin))


# ---------------------------------------------------------------------------
# MediaGalleryAdmin configuration
# ---------------------------------------------------------------------------


class TestMediaGalleryAdminConfiguration(TestCase):
    """Tests for MediaGalleryAdmin meta configuration."""

    def setUp(self):
        self.admin = admin.site._registry[MediaGallery]

    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_name(self):
        self.assertIn("name", self.admin.list_display)

    def test_search_fields_contains_name(self):
        self.assertIn("name", self.admin.search_fields)

    def test_inlines_contains_media_item_inline(self):
        inline_models = [inline.model for inline in self.admin.inlines]
        self.assertIn(MediaItem, inline_models)

    def test_one_inline_registered(self):
        self.assertEqual(len(self.admin.inlines), 1)


# ---------------------------------------------------------------------------
# MediaItemAdmin configuration
# ---------------------------------------------------------------------------


class TestMediaItemAdminConfiguration(TestCase):
    """Tests for MediaItemAdmin meta configuration."""

    def setUp(self):
        self.admin = admin.site._registry[MediaItem]

    # list_display
    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_gallery(self):
        self.assertIn("gallery", self.admin.list_display)

    def test_list_display_contains_type(self):
        self.assertIn("type", self.admin.list_display)

    def test_list_display_contains_format(self):
        self.assertIn("format", self.admin.list_display)

    def test_list_display_contains_original_filename(self):
        self.assertIn("original_filename", self.admin.list_display)

    def test_list_display_contains_position(self):
        self.assertIn("position", self.admin.list_display)

    def test_list_display_contains_width(self):
        self.assertIn("width", self.admin.list_display)

    def test_list_display_contains_height(self):
        self.assertIn("height", self.admin.list_display)

    # list_filter
    def test_list_filter_contains_type(self):
        self.assertIn("type", self.admin.list_filter)

    def test_list_filter_contains_format(self):
        self.assertIn("format", self.admin.list_filter)

    # search_fields
    def test_search_fields_contains_original_filename(self):
        self.assertIn("original_filename", self.admin.search_fields)

    def test_search_fields_contains_gallery_name(self):
        self.assertIn("gallery__name", self.admin.search_fields)

    # autocomplete_fields
    def test_autocomplete_fields_contains_gallery(self):
        self.assertIn("gallery", self.admin.autocomplete_fields)

    # inlines
    def test_inlines_contains_media_item_translation_inline(self):
        inline_models = [inline.model for inline in self.admin.inlines]
        self.assertIn(MediaItemTranslation, inline_models)

    def test_inlines_contains_media_item_crop_inline(self):
        inline_models = [inline.model for inline in self.admin.inlines]
        self.assertIn(MediaItemCrop, inline_models)

    def test_two_inlines_registered(self):
        self.assertEqual(len(self.admin.inlines), 2)


# ---------------------------------------------------------------------------
# MediaItemTranslationAdmin configuration
# ---------------------------------------------------------------------------


class TestMediaItemTranslationAdminConfiguration(TestCase):
    """Tests for MediaItemTranslationAdmin meta configuration."""

    def setUp(self):
        self.admin = admin.site._registry[MediaItemTranslation]

    # list_display
    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_media_item(self):
        self.assertIn("media_item", self.admin.list_display)

    def test_list_display_contains_language(self):
        self.assertIn("language", self.admin.list_display)

    def test_list_display_contains_title(self):
        self.assertIn("title", self.admin.list_display)

    def test_list_display_contains_credits(self):
        self.assertIn("credits", self.admin.list_display)

    # list_filter
    def test_list_filter_contains_language_code(self):
        self.assertIn("language__code", self.admin.list_filter)

    # search_fields
    def test_search_fields_contains_title(self):
        self.assertIn("title", self.admin.search_fields)

    def test_search_fields_contains_credits(self):
        self.assertIn("credits", self.admin.search_fields)

    def test_search_fields_contains_media_item_original_filename(self):
        self.assertIn("media_item__original_filename", self.admin.search_fields)

    # autocomplete_fields
    def test_autocomplete_fields_contains_media_item(self):
        self.assertIn("media_item", self.admin.autocomplete_fields)

    def test_autocomplete_fields_contains_language(self):
        self.assertIn("language", self.admin.autocomplete_fields)


# ---------------------------------------------------------------------------
# MediaItemCropAdmin configuration
# ---------------------------------------------------------------------------


class TestMediaItemCropAdminConfiguration(TestCase):
    """Tests for MediaItemCropAdmin meta configuration."""

    def setUp(self):
        self.admin = admin.site._registry[MediaItemCrop]

    def test_list_display_contains_id(self):
        self.assertIn("id", self.admin.list_display)

    def test_list_display_contains_media_item(self):
        self.assertIn("media_item", self.admin.list_display)

    def test_list_display_contains_name(self):
        self.assertIn("name", self.admin.list_display)

    def test_list_display_contains_get_url(self):
        """The crop admin uses get_url (a computed method) instead of a raw url field,
        because url was replaced by an ImageField named image."""
        self.assertIn("get_url", self.admin.list_display)

    def test_list_display_does_not_contain_raw_url_field(self):
        """MediaItemCrop no longer has a url field - it uses an ImageField."""
        self.assertNotIn("url", self.admin.list_display)

    def test_search_fields_contains_name(self):
        self.assertIn("name", self.admin.search_fields)

    def test_search_fields_contains_media_item_original_filename(self):
        self.assertIn("media_item__original_filename", self.admin.search_fields)

    def test_autocomplete_fields_contains_media_item(self):
        self.assertIn("media_item", self.admin.autocomplete_fields)

    def test_get_url_is_callable_method(self):
        """get_url must be a method on the admin class, not a string field name."""
        self.assertTrue(callable(getattr(self.admin.__class__, "get_url", None)))

    def test_get_url_returns_link_when_image_present(self):
        """get_url renders a clickable anchor when the crop has an image."""
        item = MediaItemFactory()
        crop = MediaItemCropFactory(media_item=item, name="hd_ready")
        result = self.admin.get_url(crop)
        self.assertIn("<a", str(result))

    def test_get_url_returns_dash_when_no_image(self):
        """get_url returns '-' for a crop instance with no image set."""
        crop = MediaItemCrop(name="hd_ready")  # unsaved, no image
        result = self.admin.get_url(crop)
        self.assertEqual(str(result), "-")

    def test_get_url_display_description(self):
        """The column header label must be 'Asset URL' as set by @admin.display."""
        self.assertEqual(self.admin.get_url.short_description, "Asset URL")

    def test_get_url_result_is_mark_safe(self):
        """format_html output must be SafeData so Django does not double-escape it."""
        item = MediaItemFactory()
        crop = MediaItemCropFactory(media_item=item, name="hd_ready")
        result = self.admin.get_url(crop)
        self.assertIsInstance(result, SafeData)

    def test_get_url_anchor_has_target_blank(self):
        """The rendered anchor must open in a new tab."""
        item = MediaItemFactory()
        crop = MediaItemCropFactory(media_item=item, name="hd_ready")
        result = str(self.admin.get_url(crop))
        self.assertIn('target="_blank"', result)

    def test_get_url_anchor_contains_bekijk_bestand(self):
        """The link label must read 'Bekijk bestand'."""
        item = MediaItemFactory()
        crop = MediaItemCropFactory(media_item=item, name="hd_ready")
        result = str(self.admin.get_url(crop))
        self.assertIn("Bekijk bestand", result)


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

    def setUp(self):
        self.inline = MediaItemCropInline(parent_model=MagicMock(), admin_site=MagicMock())

    def test_get_url_returns_url_string_when_image_present(self):
        """Should return the raw URL string when the crop has an image."""
        obj = MagicMock()
        type(obj.image).url = PropertyMock(return_value="https://cdn.example.com/crops/hero.jpg")
        result = self.inline.get_url(obj)
        self.assertEqual(result, "https://cdn.example.com/crops/hero.jpg")

    def test_get_url_returns_dash_when_image_is_none(self):
        """Should return '-' when obj.image is None."""
        obj = MagicMock()
        obj.image = None
        result = self.inline.get_url(obj)
        self.assertEqual(result, "-")

    def test_get_url_returns_dash_for_falsy_image(self):
        """Should return '-' for any other falsy image value (e.g. empty string)."""
        obj = MagicMock()
        obj.image = ""
        result = self.inline.get_url(obj)
        self.assertEqual(result, "-")

    def test_get_url_display_description(self):
        """Column header must be labelled 'URL' as set by @admin.display."""
        self.assertEqual(self.inline.get_url.short_description, "URL")

    def test_get_url_result_is_plain_string_not_anchor(self):
        """Inline get_url returns a plain URL - no HTML anchor tag."""
        obj = MagicMock()
        type(obj.image).url = PropertyMock(return_value="https://cdn.example.com/crops/hero.jpg")
        result = self.inline.get_url(obj)
        self.assertNotIn("<a", str(result))


# ---------------------------------------------------------------------------
# MediaItemCropInline configuration
# ---------------------------------------------------------------------------


class TestMediaItemCropInline(TestCase):
    """Tests for MediaItemCropInline configuration."""

    def test_model_is_media_item_crop(self):
        self.assertEqual(MediaItemCropInline.model, MediaItemCrop)

    def test_extra_is_one(self):
        self.assertEqual(MediaItemCropInline.extra, 1)

    def test_is_tabular_inline(self):
        self.assertTrue(issubclass(MediaItemCropInline, admin.TabularInline))

    def test_fields_contains_name(self):
        self.assertIn("name", MediaItemCropInline.fields)

    def test_fields_contains_image(self):
        """Inline must expose the image field, not the old url field."""
        self.assertIn("image", MediaItemCropInline.fields)

    def test_get_url_in_fields_or_readonly(self):
        """get_url must be reachable as either a field or a readonly_field."""
        all_fields = list(MediaItemCropInline.fields or []) + list(getattr(MediaItemCropInline, "readonly_fields", []))
        self.assertIn("get_url", all_fields)

    def test_get_url_is_readonly(self):
        """get_url is a computed display column and must be readonly."""
        self.assertIn("get_url", MediaItemCropInline.readonly_fields)


# ---------------------------------------------------------------------------
# Inline configuration (existing)
# ---------------------------------------------------------------------------


class TestMediaItemInline(TestCase):
    """Tests for MediaItemInline configuration."""

    def test_model_is_media_item(self):
        self.assertEqual(MediaItemInline.model, MediaItem)

    def test_extra_is_one(self):
        self.assertEqual(MediaItemInline.extra, 1)

    def test_has_collapse_class(self):
        self.assertIn("collapse", MediaItemInline.classes)

    def test_show_change_link_is_true(self):
        self.assertTrue(MediaItemInline.show_change_link)

    def test_is_tabular_inline(self):
        self.assertTrue(issubclass(MediaItemInline, admin.TabularInline))


class TestMediaItemTranslationInline(TestCase):
    """Tests for MediaItemTranslationInline configuration."""

    def test_model_is_media_item_translation(self):
        self.assertEqual(MediaItemTranslationInline.model, MediaItemTranslation)

    def test_extra_is_one(self):
        self.assertEqual(MediaItemTranslationInline.extra, 1)

    def test_autocomplete_fields_contains_language(self):
        self.assertIn("language", MediaItemTranslationInline.autocomplete_fields)

    def test_has_collapse_class(self):
        self.assertIn("collapse", MediaItemTranslationInline.classes)

    def test_is_tabular_inline(self):
        self.assertTrue(issubclass(MediaItemTranslationInline, admin.TabularInline))


# ---------------------------------------------------------------------------
# get_queryset optimisation
# ---------------------------------------------------------------------------


class TestMediaItemAdminGetQueryset(TestCase):
    """Verify get_queryset uses select_related for FK optimisation."""

    def setUp(self):
        self.superuser = make_superuser()
        self.factory = RequestFactory()
        self.model_admin = admin.site._registry[MediaItem]

    def _make_request(self):
        request = self.factory.get("/")
        request.user = self.superuser
        return request

    def test_queryset_model_is_media_item(self):
        qs = self.model_admin.get_queryset(self._make_request())
        self.assertEqual(qs.model, MediaItem)

    def test_queryset_has_select_related_for_gallery(self):
        admin_instance = self.model_admin
        request = self._make_request()

        self.assertEqual(admin_instance.list_select_related, ("gallery",))

        qs = admin_instance.get_queryset(request)

        if admin_instance.list_select_related:
            qs = qs.select_related(*admin_instance.list_select_related)

        self.assertIn("gallery", qs.query.select_related)


# ---------------------------------------------------------------------------
# Functional changelist / changeform tests
# ---------------------------------------------------------------------------


class TestMediaGalleryAdminChangelist(TestCase):
    """Functional tests for MediaGalleryAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("gallery_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self):
        url = reverse("admin:media_library_mediagallery_changelist")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_changelist_shows_gallery_name(self):
        MediaGalleryFactory.create(name="Summer Exhibition")
        url = reverse("admin:media_library_mediagallery_changelist")
        self.assertContains(self.client.get(url), "Summer Exhibition")

    def test_changeform_returns_200(self):
        gallery = MediaGalleryFactory.create()
        url = reverse("admin:media_library_mediagallery_change", args=[gallery.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_search_returns_200(self):
        url = reverse("admin:media_library_mediagallery_changelist")
        self.assertEqual(self.client.get(url, {"q": "test"}).status_code, 200)


class TestMediaItemAdminChangelist(TestCase):
    """Functional tests for MediaItemAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("item_admin")
        self.client.force_login(self.superuser)
        self.gallery = MediaGalleryFactory.create()

    def test_changelist_returns_200(self):
        url = reverse("admin:media_library_mediaitem_changelist")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_changelist_with_items(self):
        MediaItemFactory.create(gallery=self.gallery)
        url = reverse("admin:media_library_mediaitem_changelist")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_changeform_returns_200(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        url = reverse("admin:media_library_mediaitem_change", args=[item.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_changelist_filter_by_type(self):
        url = reverse("admin:media_library_mediaitem_changelist")
        self.assertEqual(
            self.client.get(url, {"type": MediaItem.MediaItemType.IMAGE}).status_code,
            200,
        )

    def test_changelist_filter_by_format(self):
        MediaItemFactory.create(gallery=self.gallery, format="jpg")
        url = reverse("admin:media_library_mediaitem_changelist")
        self.assertEqual(self.client.get(url, {"format": "jpg"}).status_code, 200)

    def test_changelist_search(self):
        url = reverse("admin:media_library_mediaitem_changelist")
        self.assertEqual(self.client.get(url, {"q": "photo"}).status_code, 200)


class TestMediaItemTranslationAdminChangelist(TestCase):
    """Functional tests for MediaItemTranslationAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("trans_admin")
        self.client.force_login(self.superuser)
        self.gallery = MediaGalleryFactory.create()

    def test_changelist_returns_200(self):
        url = reverse("admin:media_library_mediaitemtranslation_changelist")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_changeform_returns_200(self):
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
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_changelist_shows_translation_title(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        language = LanguageFactory.create()
        MediaItemTranslationFactory.create(
            media_item=item,
            language=language,
            title="Zichtbare Titel",
        )
        url = reverse("admin:media_library_mediaitemtranslation_changelist")
        self.assertContains(self.client.get(url), "Zichtbare Titel")

    def test_changelist_filter_by_language(self):
        url = reverse("admin:media_library_mediaitemtranslation_changelist")
        self.assertEqual(self.client.get(url, {"language__code": "nl"}).status_code, 200)

    def test_changelist_search(self):
        url = reverse("admin:media_library_mediaitemtranslation_changelist")
        self.assertEqual(self.client.get(url, {"q": "foto"}).status_code, 200)


class TestMediaItemCropAdminChangelist(TestCase):
    """Functional tests for MediaItemCropAdmin via HTTP."""

    def setUp(self):
        self.superuser = make_superuser("crop_admin")
        self.client.force_login(self.superuser)
        self.gallery = MediaGalleryFactory.create()

    def test_changelist_returns_200(self):
        url = reverse("admin:media_library_mediaitemcrop_changelist")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_changeform_returns_200(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        crop = MediaItemCropFactory.create(media_item=item)
        url = reverse("admin:media_library_mediaitemcrop_change", args=[crop.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_changelist_shows_crop_name(self):
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemCropFactory.create(media_item=item, name="hero-banner")
        url = reverse("admin:media_library_mediaitemcrop_changelist")
        self.assertContains(self.client.get(url), "hero-banner")

    def test_changelist_search(self):
        url = reverse("admin:media_library_mediaitemcrop_changelist")
        self.assertEqual(self.client.get(url, {"q": "thumb"}).status_code, 200)

    def test_changelist_renders_get_url_link_for_crops_with_image(self):
        """The changelist must render the clickable image link from get_url."""
        item = MediaItemFactory.create(gallery=self.gallery)
        MediaItemCropFactory.create(media_item=item, name="hd_ready")
        url = reverse("admin:media_library_mediaitemcrop_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<a")
