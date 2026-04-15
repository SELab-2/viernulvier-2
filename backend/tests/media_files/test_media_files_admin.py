"""Tests for apps.media_files.admin."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ModelForm
from django.test import RequestFactory
import pytest

from apps.core.admin import BaseAdmin
from apps.media_files.admin import MediaFileAdmin
from apps.media_files.models import MediaFile

pytestmark = pytest.mark.django_db

User = get_user_model()


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
def request_factory() -> RequestFactory:
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
    return MediaFile.objects.create(
        file=make_uploaded_file(),
        uploaded_by=uploader,
    )


class DummyForm(ModelForm):
    class Meta:
        model = MediaFile
        fields = ["file", "filename", "uploaded_by"]


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
            "file_type",
            "mime_type",
            "size_bytes",
            "uploaded_by",
            "created_at",
            "file_link",
        )

    def test_list_filter_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.list_filter == ("file_type", "mime_type", "created_at")

    def test_search_fields_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.search_fields == (
            "filename",
            "mime_type",
            "external_id",
            "uploaded_by__username",
            "uploaded_by__email",
        )

    def test_readonly_fields_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
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
            "uploaded_by",
            "created_at",
        )

    def test_ordering_matches_expected_fields(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.ordering == ("-created_at",)

    def test_file_is_editable(self, media_file_admin: MediaFileAdmin) -> None:
        assert "file" in media_file_admin.fields
        assert "file" not in media_file_admin.readonly_fields

    def test_filename_is_editable(self, media_file_admin: MediaFileAdmin) -> None:
        assert "filename" in media_file_admin.fields
        assert "filename" not in media_file_admin.readonly_fields

    def test_file_link_description_is_file(self, media_file_admin: MediaFileAdmin) -> None:
        assert media_file_admin.file_link.short_description == "File"


class TestMediaFileAdminQueryset:
    def test_get_queryset_returns_mediafile_queryset(
        self,
        media_file_admin: MediaFileAdmin,
        request_factory: RequestFactory,
        admin_user,
    ) -> None:
        request = request_factory.get("/admin/media_files/mediafile/")
        request.user = admin_user

        qs = media_file_admin.get_queryset(request)

        assert qs.model is MediaFile

    def test_get_queryset_evaluates_without_errors(
        self,
        media_file_admin: MediaFileAdmin,
        request_factory: RequestFactory,
        admin_user,
        media_file: MediaFile,
    ) -> None:
        request = request_factory.get("/admin/media_files/mediafile/")
        request.user = admin_user

        assert media_file in list(media_file_admin.get_queryset(request))

    def test_get_queryset_selects_related_uploaded_by(
        self,
        media_file_admin: MediaFileAdmin,
        request_factory: RequestFactory,
        admin_user,
        media_file: MediaFile,
    ) -> None:
        request = request_factory.get("/admin/media_files/mediafile/")
        request.user = admin_user

        obj = media_file_admin.get_queryset(request).get(pk=media_file.pk)

        assert obj.uploaded_by is not None
        assert obj.uploaded_by.username == "uploader"


class TestMediaFileAdminSaveModel:
    def test_save_model_sets_uploaded_by_when_missing(
        self,
        media_file_admin: MediaFileAdmin,
        request_factory: RequestFactory,
        admin_user,
    ) -> None:
        request = request_factory.post("/admin/media_files/mediafile/add/")
        request.user = admin_user
        obj = MediaFile(file=make_uploaded_file(), filename="poster.pdf")

        media_file_admin.save_model(request, obj, form=DummyForm(), change=False)

        obj.refresh_from_db()
        assert obj.uploaded_by == admin_user

    def test_save_model_preserves_existing_uploaded_by(
        self,
        media_file_admin: MediaFileAdmin,
        request_factory: RequestFactory,
        admin_user,
        uploader,
        media_file: MediaFile,
    ) -> None:
        request = request_factory.post(f"/admin/media_files/mediafile/{media_file.pk}/change/")
        request.user = admin_user

        media_file_admin.save_model(request, media_file, form=DummyForm(), change=True)

        media_file.refresh_from_db()
        assert media_file.uploaded_by == uploader


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
