"""Tests for apps.media_files.filters."""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.core.filters import BaseModelFilter
from apps.media_files.filters import MediaFileFilter
from apps.media_files.models import MediaFile

pytestmark = pytest.mark.django_db

User = get_user_model()


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


@pytest.fixture
def user_one():
    return User.objects.create_user(username="user-one", email="user1@example.com", password="password")


@pytest.fixture
def user_two():
    return User.objects.create_user(username="user-two", email="user2@example.com", password="password")


@pytest.fixture
def pdf_file(user_one):
    return MediaFile.objects.create(
        file=make_uploaded_file(name="season-brochure.pdf", content_type="application/pdf"),
        uploaded_by=user_one,
        external_id="ext-pdf-001",
    )


@pytest.fixture
def png_file(user_one):
    return MediaFile.objects.create(
        file=make_uploaded_file(name="MainPoster.PNG", content_type="image/png"),
        uploaded_by=user_one,
        external_id="ext-img-001",
    )


@pytest.fixture
def jpg_file(user_two):
    return MediaFile.objects.create(
        file=make_uploaded_file(name="press-photo.jpg", content_type="image/jpeg"),
        uploaded_by=user_two,
        external_id="ext-img-002",
    )


class TestMediaFileFilterDefinition:
    def test_inherits_from_base_model_filter(self) -> None:
        assert issubclass(MediaFileFilter, BaseModelFilter)

    def test_meta_model_is_media_file(self) -> None:
        assert MediaFileFilter._meta.model is MediaFile

    def test_meta_fields_match_expected_fields(self) -> None:
        assert MediaFileFilter._meta.fields == ["file_type", "mime_type", "filename", "uploaded_by", "external_id"]


class TestMediaFileFilterWorkingFields:
    def test_filters_pdf_file_type(self, pdf_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"file_type": "pdf"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [pdf_file]

    def test_filters_image_file_type(self, png_file: MediaFile, jpg_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"file_type": "image"}, queryset=MediaFile.objects.all()).qs
        assert set(qs) == {png_file, jpg_file}

    def test_file_type_is_case_insensitive_exact(self, pdf_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"file_type": "PDF"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [pdf_file]

    def test_mime_type_filters_exactly(self, pdf_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"mime_type": "application/pdf"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [pdf_file]

    def test_mime_type_is_case_insensitive_exact(self, png_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"mime_type": "IMAGE/PNG"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [png_file]

    def test_filters_by_filename_contains(self, png_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"filename": "Poster"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [png_file]

    def test_filters_by_uploaded_by_username(self, user_two, jpg_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"uploaded_by": user_two.username}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [jpg_file]

    def test_uploaded_by_username_is_case_insensitive_exact(self, user_two, jpg_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"uploaded_by": user_two.username.upper()}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [jpg_file]

    def test_combined_filters_narrow_results(self, user_one, pdf_file: MediaFile) -> None:
        qs = MediaFileFilter(
            data={"file_type": "pdf", "uploaded_by": user_one.pk},
            queryset=MediaFile.objects.all(),
        ).qs
        assert list(qs) == [pdf_file]

    def test_unknown_value_returns_empty_queryset(self) -> None:
        qs = MediaFileFilter(data={"file_type": "unknown"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == []

    def test_empty_filter_returns_all_results(self, pdf_file: MediaFile, png_file: MediaFile, jpg_file: MediaFile) -> None:
        qs = MediaFileFilter(data={}, queryset=MediaFile.objects.all()).qs
        assert set(qs) == {pdf_file, png_file, jpg_file}
