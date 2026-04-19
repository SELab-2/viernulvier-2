"""Tests for apps.media_files.admin."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.core.admin import BaseAdmin
from apps.media_files.admin import MediaFileAdmin
from apps.media_files.models import MediaFile

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
def media_file_admin(admin_site: AdminSite) -> MediaFileAdmin:
    return MediaFileAdmin(MediaFile, admin_site)


@pytest.fixture
def media_file() -> MediaFile:
    return MediaFile.objects.create(
        file=make_uploaded_file(),
        description="Poster voor de seizoenscampagne.",
    )


class TestMediaFileAdminRegistration:
    def test_model_is_registered_in_admin_site(self) -> None:
        assert MediaFile in admin.site._registry

    def test_registered_admin_is_media_file_admin(self) -> None:
        assert isinstance(admin.site._registry[MediaFile], MediaFileAdmin)

    def test_admin_inherits_from_base_admin(self, media_file_admin: MediaFileAdmin) -> None:
        assert isinstance(media_file_admin, BaseAdmin)


class TestMediaFileAdminConfiguration:
    def test_list_display_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.list_display == (
            "id",
            "filename",
            "description_preview",
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
            "description",
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
            "description",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
        )

    def test_ordering_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.ordering == ("-created_at",)

    def test_description_is_editable(self, media_file_admin: MediaFileAdmin) -> None:
        assert "description" in media_file_admin.fields
        assert "description" not in media_file_admin.readonly_fields

    def test_description_preview_description_is_description(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.description_preview.short_description == "Description"

    def test_file_link_description_is_file(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.file_link.short_description == "File"


class TestMediaFileAdminDescriptionPreview:
    def test_returns_dash_when_no_description(self, media_file_admin: MediaFileAdmin) -> None:
        obj = MediaFile(filename="poster.pdf", description="")
        assert media_file_admin.description_preview(obj) == "-"

    def test_returns_full_description_when_short(self, media_file_admin: MediaFileAdmin) -> None:
        obj = MediaFile(filename="poster.pdf", description="Korte context")
        assert media_file_admin.description_preview(obj) == "Korte context"

    def test_truncates_long_description(self, media_file_admin: MediaFileAdmin) -> None:
        description = "x" * 81
        obj = MediaFile(filename="poster.pdf", description=description)
        result = media_file_admin.description_preview(obj)

        assert result.endswith("...")
        assert len(result) == 80
        assert result == f"{'x' * 77}..."


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
