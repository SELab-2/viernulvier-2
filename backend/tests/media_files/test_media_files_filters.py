"""Tests for apps.media_files.filters."""

from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.core.filters import BaseModelFilter
from apps.languages.models import Language
from apps.media_files.filters import MediaFileFilter
from apps.media_files.models import MediaFile, MediaFileTranslation

pytestmark = pytest.mark.django_db


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


@pytest.fixture
def languages() -> tuple[Language, Language]:
    return (
        Language.objects.create(code="nl", name="Dutch", is_active=True),
        Language.objects.create(code="en", name="English", is_active=True),
    )


@pytest.fixture
def pdf_file(languages: tuple[Language, Language]) -> MediaFile:
    nl, en = languages
    obj = MediaFile.objects.create(
        file=make_uploaded_file(name="season-brochure.pdf", content_type="application/pdf"),
        external_id="ext-pdf-001",
    )
    MediaFileTranslation.objects.create(media_file=obj, language=nl, description="Programmabrochure voor het voorjaar.")
    MediaFileTranslation.objects.create(media_file=obj, language=en, description="Spring season brochure.")
    return obj


@pytest.fixture
def png_file(languages: tuple[Language, Language]) -> MediaFile:
    nl, _ = languages
    obj = MediaFile.objects.create(
        file=make_uploaded_file(name="MainPoster.PNG", content_type="image/png"),
        external_id="ext-img-001",
    )
    MediaFileTranslation.objects.create(media_file=obj, language=nl, description="Premièreposter voor social campagne.")
    return obj


@pytest.fixture
def jpg_file(languages: tuple[Language, Language]) -> MediaFile:
    _, en = languages
    obj = MediaFile.objects.create(
        file=make_uploaded_file(name="press-photo.jpg", content_type="image/jpeg"),
        external_id="ext-img-002",
    )
    MediaFileTranslation.objects.create(media_file=obj, language=en, description="Press photo with cast.")
    return obj


class TestMediaFileFilterDefinition:
    def test_inherits_from_base_model_filter(self) -> None:
        assert issubclass(MediaFileFilter, BaseModelFilter)

    def test_meta_model_is_media_file(self) -> None:
        assert MediaFileFilter._meta.model is MediaFile

    def test_meta_fields_match_expected_fields(self) -> None:
        assert MediaFileFilter._meta.fields == ["file_type", "mime_type", "filename", "description", "external_id"]

    def test_description_filter_targets_translations_field(self) -> None:
        assert MediaFileFilter.base_filters["description"].field_name == "translations__description"

    def test_description_filter_is_distinct(self) -> None:
        assert MediaFileFilter.base_filters["description"].distinct is True


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

    def test_filters_by_translated_description_contains(self, pdf_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"description": "voorjaar"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [pdf_file]

    def test_description_filter_matches_any_language(self, pdf_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"description": "Spring season"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [pdf_file]

    def test_description_filter_is_case_insensitive(self, png_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"description": "SOCIAL"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [png_file]

    def test_description_filter_distinct_prevents_duplicates(self, pdf_file: MediaFile) -> None:
        qs = MediaFileFilter(data={"description": "brochure"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == [pdf_file]

    def test_combined_filters_narrow_results(self, pdf_file: MediaFile) -> None:
        qs = MediaFileFilter(
            data={"file_type": "pdf", "description": "programma"},
            queryset=MediaFile.objects.all(),
        ).qs
        assert list(qs) == [pdf_file]

    def test_unknown_value_returns_empty_queryset(self) -> None:
        qs = MediaFileFilter(data={"file_type": "unknown"}, queryset=MediaFile.objects.all()).qs
        assert list(qs) == []

    def test_empty_filter_returns_all_results(self, pdf_file: MediaFile, png_file: MediaFile, jpg_file: MediaFile) -> None:
        qs = MediaFileFilter(data={}, queryset=MediaFile.objects.all()).qs
        assert set(qs) == {pdf_file, png_file, jpg_file}
