"""
Covers:
- admin registration
- BaseAdmin inheritance
- list_display configuration
- list_filter configuration
- search_fields configuration
- readonly_fields configuration
- fields order/configuration
- ordering configuration
- get_queryset behaviour
- file_link rendering with and without a file
"""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
import pytest

from apps.core.admin import BaseAdmin
from apps.media_files.admin import MediaFileAdmin
from apps.media_files.models import MediaFile

pytestmark = pytest.mark.django_db

User = get_user_model()


# =====================================================
# Fixtures / helpers
# =====================================================


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def media_file_admin(admin_site):
    return MediaFileAdmin(MediaFile, admin_site)


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password",
    )


@pytest.fixture
def uploader():
    return User.objects.create_user(
        username="uploader",
        email="uploader@example.com",
        password="password",
    )


@pytest.fixture
def media_file(uploader):
    uploaded = SimpleUploadedFile(
        "poster.pdf",
        b"dummy content",
        content_type="application/pdf",
    )
    return MediaFile.objects.create(
        file=uploaded,
        original_name="poster.pdf",
        mime_type="application/pdf",
        size_bytes=123,
        uploaded_by=uploader,
    )


# =====================================================
# Registration / inheritance
# =====================================================


class TestMediaFileAdminRegistration:
    def test_model_is_registered_in_admin_site(self) -> None:
        assert MediaFile in admin.site._registry

    def test_registered_admin_is_media_file_admin(self) -> None:
        registered_admin = admin.site._registry[MediaFile]
        assert isinstance(registered_admin, MediaFileAdmin)

    def test_admin_inherits_from_base_admin(self, media_file_admin) -> None:
        assert isinstance(media_file_admin, BaseAdmin)


# =====================================================
# Static admin configuration
# =====================================================


class TestMediaFileAdminConfiguration:
    def test_list_display_matches_expected_fields(self, media_file_admin) -> None:
        assert media_file_admin.list_display == (
            "id",
            "original_name",
            "file_type",
            "mime_type",
            "size_bytes",
            "uploaded_by",
            "created_at",
            "file_link",
        )

    def test_list_filter_matches_expected_fields(self, media_file_admin) -> None:
        assert media_file_admin.list_filter == (
            "file_type",
            "mime_type",
            "created_at",
        )

    def test_search_fields_matches_expected_fields(self, media_file_admin) -> None:
        assert media_file_admin.search_fields == (
            "original_name",
            "mime_type",
            "external_id",
            "uploaded_by__username",
            "uploaded_by__email",
        )

    def test_readonly_fields_matches_expected_fields(self, media_file_admin) -> None:
        assert media_file_admin.readonly_fields == (
            "id",
            "external_id",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
            "file_link",
        )

    def test_fields_matches_expected_fields(self, media_file_admin) -> None:
        assert media_file_admin.fields == (
            "id",
            "external_id",
            "file",
            "file_link",
            "original_name",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        )

    def test_ordering_matches_expected_fields(self, media_file_admin) -> None:
        assert media_file_admin.ordering == ("-created_at",)

    def test_file_link_is_in_list_display(self, media_file_admin) -> None:
        assert "file_link" in media_file_admin.list_display

    def test_file_field_is_editable_in_form_fields(self, media_file_admin) -> None:
        assert "file" in media_file_admin.fields
        assert "file" not in media_file_admin.readonly_fields


# =====================================================
# get_queryset
# =====================================================


class TestMediaFileAdminQueryset:
    def test_get_queryset_returns_queryset(self, media_file_admin, request_factory, admin_user) -> None:
        request = request_factory.get("/admin/apps/media_files/mediafile/")
        request.user = admin_user

        qs = media_file_admin.get_queryset(request)

        assert qs.model is MediaFile

    def test_get_queryset_evaluates_without_errors(self, media_file_admin, request_factory, admin_user, media_file) -> None:
        request = request_factory.get("/admin/apps/media_files/mediafile/")
        request.user = admin_user

        qs = media_file_admin.get_queryset(request)

        rows = list(qs)
        assert media_file in rows

    def test_get_queryset_includes_uploaded_by_relation(
        self, media_file_admin, request_factory, admin_user, media_file
    ) -> None:
        request = request_factory.get("/admin/apps/media_files/mediafile/")
        request.user = admin_user

        qs = media_file_admin.get_queryset(request)
        obj = qs.get(pk=media_file.pk)

        assert obj.uploaded_by is not None
        assert obj.uploaded_by.username == "uploader"


# =====================================================
# file_link
# =====================================================


class TestMediaFileAdminFileLink:
    def test_file_link_returns_dash_when_no_file(self, media_file_admin) -> None:
        obj = MediaFile(
            original_name="missing-file",
            mime_type="application/pdf",
            size_bytes=0,
            file_type=MediaFile.FileType.PDF,
        )

        assert media_file_admin.file_link(obj) == "-"

    def test_file_link_returns_html_anchor_when_file_exists(self, media_file_admin, media_file) -> None:
        result = media_file_admin.file_link(media_file)

        assert 'href="' in result
        assert "Open file" in result
        assert 'target="_blank"' in result
        assert 'rel="noopener noreferrer"' in result

    def test_file_link_contains_file_url(self, media_file_admin, media_file) -> None:
        result = media_file_admin.file_link(media_file)

        assert media_file.file.url in result

    def test_file_link_description_is_file(self, media_file_admin) -> None:
        assert media_file_admin.file_link.short_description == "File"
