"""Tests for apps.media_files.admin."""

from unittest.mock import MagicMock

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.core.admin import BaseAdmin
from apps.languages.models import Language
from apps.media_files.admin import (
    MediaFileAdmin,
    MediaFileTranslationAdmin,
    MediaFileTranslationInline,
)
from apps.media_files.models import MediaFile, MediaFileTranslation

pytestmark = pytest.mark.django_db


def make_uploaded_file(
    name: str = "poster.pdf",
    content: bytes = b"dummy content",
    content_type: str = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


@pytest.fixture
def admin_site() -> AdminSite:
    return AdminSite()


@pytest.fixture
def dutch_language() -> Language:
    return Language.objects.create(code="nl", name="Dutch", is_active=True)


@pytest.fixture
def english_language() -> Language:
    return Language.objects.create(code="en", name="English", is_active=True)


@pytest.fixture
def media_file_admin(admin_site: AdminSite) -> MediaFileAdmin:
    return MediaFileAdmin(MediaFile, admin_site)


@pytest.fixture
def media_file_translation_admin(admin_site: AdminSite) -> MediaFileTranslationAdmin:
    return MediaFileTranslationAdmin(MediaFileTranslation, admin_site)


@pytest.fixture
def media_file(dutch_language: Language) -> MediaFile:
    obj = MediaFile.objects.create(file=make_uploaded_file())
    MediaFileTranslation.objects.create(
        media_file=obj,
        language=dutch_language,
        description="Poster voor de seizoenscampagne.",
    )
    return obj


@pytest.fixture
def admin_request(rf):
    request = rf.get("/admin/")
    User = get_user_model()
    request.user = User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="testpass123",
    )
    return request


class TestMediaFileAdminRegistration:
    def test_model_is_registered_in_admin_site(self) -> None:
        assert MediaFile in admin.site._registry

    def test_translation_model_is_registered_in_admin_site(self) -> None:
        assert MediaFileTranslation in admin.site._registry

    def test_registered_admin_is_media_file_admin(self) -> None:
        assert isinstance(admin.site._registry[MediaFile], MediaFileAdmin)

    def test_registered_translation_admin_is_media_file_translation_admin(self) -> None:
        assert isinstance(admin.site._registry[MediaFileTranslation], MediaFileTranslationAdmin)

    def test_admin_inherits_from_base_admin(self, media_file_admin: MediaFileAdmin) -> None:
        assert isinstance(media_file_admin, BaseAdmin)

    def test_translation_admin_inherits_from_base_admin(
        self,
        media_file_translation_admin: MediaFileTranslationAdmin,
    ) -> None:
        assert isinstance(media_file_translation_admin, BaseAdmin)


class TestMediaFileAdminConfiguration:
    def test_list_display_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.list_display == (
            "id",
            "filename",
            "display_description_preview",
            "file_type",
            "mime_type",
            "size_bytes",
            "created_at",
            "file_link",
        )

    def test_list_filter_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.list_filter == ("file_type", "mime_type", "created_at")

    def test_search_fields_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.search_fields == (
            "filename",
            "translations__description",
            "mime_type",
            "external_id",
        )

    def test_readonly_fields_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.readonly_fields == (
            "id",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
            "file_link",
        )

    def test_fields_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.fields == (
            "id",
            "external_id",
            "file",
            "file_link",
            "filename",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
        )

    def test_ordering_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.ordering == ("-created_at",)

    def test_translation_inline_is_configured(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.inlines == [MediaFileTranslationInline]

    def test_description_is_no_longer_direct_field(self, media_file_admin: MediaFileAdmin) -> None:
        assert "description" not in media_file_admin.fields
        assert "description" not in media_file_admin.readonly_fields

    def test_display_description_preview_description_is_description(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.display_description_preview.short_description == "Description"

    def test_file_link_description_is_file(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.file_link.short_description == "File"


class TestMediaFileTranslationAdminConfiguration:
    def test_list_display_matches_expected_fields(
        self,
        media_file_translation_admin: MediaFileTranslationAdmin,
    ) -> None:
        assert media_file_translation_admin.list_display == (
            "id",
            "media_file",
            "language",
            "description",
        )

    def test_list_filter_matches_expected_fields(
        self,
        media_file_translation_admin: MediaFileTranslationAdmin,
    ) -> None:
        assert media_file_translation_admin.list_filter == ("language__code",)

    def test_search_fields_match_expected_fields(
        self,
        media_file_translation_admin: MediaFileTranslationAdmin,
    ) -> None:
        assert media_file_translation_admin.search_fields == ("description", "media_file__filename")

    def test_autocomplete_fields_match_expected_fields(
        self,
        media_file_translation_admin: MediaFileTranslationAdmin,
    ) -> None:
        assert media_file_translation_admin.autocomplete_fields == ("media_file", "language")

    def test_ordering_matches_expected_fields(
        self,
        media_file_translation_admin: MediaFileTranslationAdmin,
    ) -> None:
        assert media_file_translation_admin.ordering == ("media_file", "language__code")


class TestMediaFileTranslationInlineConfiguration:
    def test_inline_model_is_translation(self) -> None:
        assert MediaFileTranslationInline.model is MediaFileTranslation

    def test_inline_fields_match_expected_fields(self) -> None:
        assert MediaFileTranslationInline.fields == ("language", "description")

    def test_inline_autocomplete_fields_match_expected_fields(self) -> None:
        assert MediaFileTranslationInline.autocomplete_fields == ("language",)

    def test_inline_ordering_matches_expected_fields(self) -> None:
        assert MediaFileTranslationInline.ordering == ("language__code",)

    def test_inline_extra_is_one(self) -> None:
        assert MediaFileTranslationInline.extra == 1


class TestMediaFileAdminDescriptionPreview:
    def test_returns_dash_when_no_translation(self, media_file_admin: MediaFileAdmin) -> None:
        obj = MediaFile(filename="poster.pdf")
        assert media_file_admin.display_description_preview(obj) == "-"

    def test_returns_full_description_when_short(self, media_file_admin: MediaFileAdmin) -> None:
        obj = MediaFile(filename="poster.pdf")
        obj.get_base_display_name = lambda **_: "Korte context"  # type: ignore[method-assign]
        assert media_file_admin.display_description_preview(obj) == "Korte context"

    def test_truncates_long_description(self, media_file_admin: MediaFileAdmin) -> None:
        description = "x" * 81
        obj = MediaFile(filename="poster.pdf")
        obj.get_base_display_name = lambda **_: description  # type: ignore[method-assign]
        result = media_file_admin.display_description_preview(obj)

        assert result.endswith("...")
        assert len(result) == 80
        assert result == f"{'x' * 77}..."


class TestMediaFileAdminQuerysets:
    def test_inline_get_queryset_selects_related_language(
        self,
        admin_request,
        admin_site: AdminSite,
    ) -> None:
        inline = MediaFileTranslationInline(MediaFile, admin_site)
        qs = inline.get_queryset(admin_request)
        assert qs is not None

    def test_media_file_translation_admin_get_queryset_selects_related(
        self,
        admin_request,
        media_file_translation_admin: MediaFileTranslationAdmin,
    ) -> None:
        qs = media_file_translation_admin.get_queryset(admin_request)
        assert qs is not None

    def test_media_file_admin_get_queryset_prefetches_translations_language(
        self,
        media_file_admin: MediaFileAdmin,
        admin_request,
    ) -> None:
        qs = media_file_admin.get_queryset(admin_request)
        assert "translations__language" in qs._prefetch_related_lookups


class TestMediaFileAdminFileLink:
    def test_file_link_returns_dash_when_no_file(self, media_file_admin: MediaFileAdmin) -> None:
        obj = MediaFile(filename="missing-file", mime_type="application/pdf", size_bytes=0)
        assert media_file_admin.file_link(obj) == "-"

    def test_file_link_returns_html_anchor_when_file_exists(
        self,
        media_file_admin: MediaFileAdmin,
        media_file: MediaFile,
    ) -> None:
        result = media_file_admin.file_link(media_file)

        assert 'href="' in result
        assert "Open file" in result
        assert 'target="_blank"' in result
        assert 'rel="noopener noreferrer"' in result
        assert media_file.file.url in result

    def test_file_link_handles_file_without_url(self, media_file_admin):
        obj = MediaFile(filename="test.pdf")
        mock_file = MagicMock()
        mock_file.url = ""
        obj.file = mock_file

        result = media_file_admin.file_link(obj)

        assert "href" in result

    def test_file_link_with_explicit_none(self, media_file_admin):
        obj = MediaFile(filename="x")
        obj.file = None
        assert media_file_admin.file_link(obj) == "-"
