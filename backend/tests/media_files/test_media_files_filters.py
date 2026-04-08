"""
Covers:
- filter inheritance from BaseModelFilter
- Meta model and fields
- file_type filtering (case-insensitive exact)
- mime_type filtering (case-insensitive exact)
- original_name filtering (case-insensitive contains)
- uploaded_by filtering by user id
- external_id filtering inherited from BaseModelFilter
- combined filters
- unknown/empty filter values
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.core.filters import BaseModelFilter
from apps.media_files.filters import MediaFileFilter
from apps.media_files.models import MediaFile

pytestmark = pytest.mark.django_db

User = get_user_model()


# =====================================================
# Helpers
# =====================================================


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


# =====================================================
# Fixtures
# =====================================================


@pytest.fixture
def user_one():
    return User.objects.create_user(
        username="user-one",
        email="user1@example.com",
        password="password",
    )


@pytest.fixture
def user_two():
    return User.objects.create_user(
        username="user-two",
        email="user2@example.com",
        password="password",
    )


@pytest.fixture
def pdf_file(user_one):
    return MediaFile.objects.create(
        file=make_uploaded_file(name="season-brochure.pdf", content_type="application/pdf"),
        original_name="season-brochure.pdf",
        mime_type="application/pdf",
        size_bytes=100,
        uploaded_by=user_one,
        external_id="ext-pdf-001",
    )


@pytest.fixture
def png_file(user_one):
    return MediaFile.objects.create(
        file=make_uploaded_file(name="MainPoster.PNG", content_type="image/png"),
        original_name="MainPoster.PNG",
        mime_type="image/png",
        size_bytes=200,
        uploaded_by=user_one,
        external_id="ext-img-001",
    )


@pytest.fixture
def jpg_file(user_two):
    return MediaFile.objects.create(
        file=make_uploaded_file(name="press-photo.jpg", content_type="image/jpeg"),
        original_name="press-photo.jpg",
        mime_type="image/jpeg",
        size_bytes=300,
        uploaded_by=user_two,
        external_id="ext-img-002",
    )


# =====================================================
# Filter definition
# =====================================================


class TestMediaFileFilterDefinition:
    def test_inherits_from_base_model_filter(self) -> None:
        assert issubclass(MediaFileFilter, BaseModelFilter)

    def test_meta_model_is_media_file(self) -> None:
        assert MediaFileFilter._meta.model is MediaFile

    def test_meta_fields_match_expected_fields(self) -> None:
        assert MediaFileFilter._meta.fields == [
            "file_type",
            "mime_type",
            "original_name",
            "uploaded_by",
            "external_id",
        ]


# =====================================================
# file_type
# =====================================================


class TestMediaFileFilterFileType:
    def test_filters_pdf_file_type(self, pdf_file) -> None:
        qs = MediaFileFilter(
            data={"file_type": "pdf"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [pdf_file]

    def test_filters_image_file_type(self, png_file, jpg_file) -> None:
        qs = MediaFileFilter(
            data={"file_type": "image"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert set(qs) == {png_file, jpg_file}

    def test_file_type_is_case_insensitive_exact(self, pdf_file) -> None:
        qs = MediaFileFilter(
            data={"file_type": "PDF"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [pdf_file]

    def test_file_type_exact_match_does_not_match_partial_value(self) -> None:
        qs = MediaFileFilter(
            data={"file_type": "pd"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == []


# =====================================================
# mime_type
# =====================================================


class TestMediaFileFilterMimeType:
    def test_filters_mime_type_exactly(self, pdf_file) -> None:
        qs = MediaFileFilter(
            data={"mime_type": "application/pdf"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [pdf_file]

    def test_mime_type_is_case_insensitive_exact(self, png_file) -> None:
        qs = MediaFileFilter(
            data={"mime_type": "IMAGE/PNG"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [png_file]

    def test_mime_type_exact_match_does_not_match_partial_value(self) -> None:
        qs = MediaFileFilter(
            data={"mime_type": "image"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == []


# =====================================================
# original_name
# =====================================================


class TestMediaFileFilterOriginalName:
    def test_filters_by_original_name_contains(self, png_file) -> None:
        qs = MediaFileFilter(
            data={"original_name": "poster"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [png_file]

    def test_original_name_filter_is_case_insensitive(self, png_file) -> None:
        qs = MediaFileFilter(
            data={"original_name": "mainposter"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [png_file]

    def test_original_name_filter_can_match_multiple_rows(self, user_one):
        first = MediaFile.objects.create(
            file=make_uploaded_file(name="poster-one.png", content_type="image/png"),
            original_name="poster-one.png",
            mime_type="image/png",
            size_bytes=100,
            uploaded_by=user_one,
        )
        second = MediaFile.objects.create(
            file=make_uploaded_file(name="poster-two.jpg", content_type="image/jpeg"),
            original_name="poster-two.jpg",
            mime_type="image/jpeg",
            size_bytes=100,
            uploaded_by=user_one,
        )
        MediaFile.objects.create(
            file=make_uploaded_file(name="brochure.pdf", content_type="application/pdf"),
            original_name="brochure.pdf",
            mime_type="application/pdf",
            size_bytes=100,
            uploaded_by=user_one,
        )

        qs = MediaFileFilter(
            data={"original_name": "poster"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert set(qs) == {first, second}

    def test_original_name_filter_returns_empty_when_no_match(self) -> None:
        qs = MediaFileFilter(
            data={"original_name": "nonexistent"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == []


# =====================================================
# uploaded_by
# =====================================================


class TestMediaFileFilterUploadedBy:
    def test_filters_by_uploaded_by_id(self, pdf_file, png_file, user_one) -> None:
        qs = MediaFileFilter(
            data={"uploaded_by": user_one.id},
            queryset=MediaFile.objects.all(),
        ).qs

        assert set(qs) == {pdf_file, png_file}

    def test_uploaded_by_returns_empty_when_no_match(self) -> None:
        qs = MediaFileFilter(
            data={"uploaded_by": 999999},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == []

    def test_uploaded_by_only_matches_exact_user_id(self, jpg_file, user_two) -> None:
        qs = MediaFileFilter(
            data={"uploaded_by": user_two.id},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [jpg_file]


# =====================================================
# external_id
# =====================================================


class TestMediaFileFilterExternalId:
    def test_filters_by_external_id(self, pdf_file) -> None:
        qs = MediaFileFilter(
            data={"external_id": "ext-pdf-001"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [pdf_file]

    def test_external_id_filter_is_case_insensitive_exact(self, png_file) -> None:
        qs = MediaFileFilter(
            data={"external_id": "EXT-IMG-001"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [png_file]

    def test_external_id_exact_match_does_not_match_partial_value(self) -> None:
        qs = MediaFileFilter(
            data={"external_id": "ext-img"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == []


# =====================================================
# combined / empty filters
# =====================================================


class TestMediaFileFilterCombined:
    def test_combines_multiple_filters(self, png_file, user_one) -> None:
        qs = MediaFileFilter(
            data={
                "file_type": "image",
                "mime_type": "image/png",
                "uploaded_by": user_one.id,
                "original_name": "poster",
            },
            queryset=MediaFile.objects.all(),
        ).qs

        assert list(qs) == [png_file]

    def test_empty_filter_data_returns_all_rows(self, pdf_file, png_file, jpg_file) -> None:
        qs = MediaFileFilter(
            data={},
            queryset=MediaFile.objects.all(),
        ).qs

        assert set(qs) == {pdf_file, png_file, jpg_file}

    def test_unknown_filter_parameter_is_ignored(self, pdf_file, png_file, jpg_file) -> None:
        qs = MediaFileFilter(
            data={"unknown": "value"},
            queryset=MediaFile.objects.all(),
        ).qs

        assert set(qs) == {pdf_file, png_file, jpg_file}
