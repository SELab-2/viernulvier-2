"""Tests for apps.media_files.models."""

from io import BytesIO
import os
from unittest.mock import MagicMock, patch
import uuid

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import pytest

from apps.languages.models import Language
from apps.media_files.models import (
    DESCRIPTION_MAX_LENGTH,
    MediaFile,
    MediaFileTranslation,
    upload_to_media,
)

pytestmark = pytest.mark.django_db


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str | None = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


def make_png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color=(255, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def dutch_language() -> Language:
    return Language.objects.create(code="nl", name="Dutch", is_active=True)


@pytest.fixture
def english_language() -> Language:
    return Language.objects.create(code="en", name="English", is_active=True)


class TestUploadToMedia:
    def test_upload_path_uses_uploads_prefix(self) -> None:
        path = upload_to_media(instance=None, filename="poster.png")
        assert path.startswith("uploads/")

    def test_upload_path_preserves_extension(self) -> None:
        path = upload_to_media(instance=None, filename="poster.png")
        assert path.endswith(".png")

    def test_upload_path_generates_uuid_filename(self) -> None:
        path = upload_to_media(instance=None, filename="brochure.pdf")
        filename = os.path.basename(path)
        stem, ext = os.path.splitext(filename)
        assert ext == ".pdf"
        uuid.UUID(stem)


class TestMediaFileDerivedMethods:
    def test_derive_filename_returns_empty_string_without_file(self) -> None:
        assert MediaFile()._derive_filename() == ""

    def test_derive_mime_type_returns_empty_string_without_file(self) -> None:
        assert MediaFile()._derive_mime_type() == ""

    def test_derive_size_bytes_returns_zero_without_file(self) -> None:
        assert MediaFile()._derive_size_bytes() == 0

    def test_derive_mime_type_falls_back_to_guess_type(self) -> None:
        obj = MediaFile(file=make_uploaded_file(name="poster.png", content_type=None))
        assert obj._derive_mime_type() == "image/png"

    def test_derive_mime_type_falls_back_to_octet_stream(self) -> None:
        obj = MediaFile(file=make_uploaded_file(name="poster.unknownext", content_type=None))
        assert obj._derive_mime_type() == "application/octet-stream"

    def test_derive_file_type_recognizes_pdf(self) -> None:
        assert MediaFile()._derive_file_type("application/pdf") == MediaFile.FileType.PDF

    def test_derive_file_type_defaults_to_other(self) -> None:
        assert MediaFile()._derive_file_type("application/octet-stream") == MediaFile.FileType.OTHER

    def test_file_has_changed_is_false_for_unsaved_object(self) -> None:
        assert MediaFile(file=make_uploaded_file())._file_has_changed() is False

    def test_file_has_changed_is_false_when_object_missing_in_db(self) -> None:
        obj = MediaFile(file=make_uploaded_file())
        obj.pk = uuid.uuid4()
        obj._state.adding = False
        assert obj._file_has_changed() is False

    def test_derive_mime_type_uses_content_type_when_present(self) -> None:
        obj = MediaFile()
        mock_file = MagicMock()
        mock_file.content_type = "image/png"
        obj.file = mock_file
        assert obj._derive_mime_type() == "image/png"

    def test_populate_derived_fields_does_nothing_without_file(self) -> None:
        obj = MediaFile()
        obj._populate_derived_fields()
        assert obj.mime_type == ""

    def test_populate_derived_fields_handles_missing_previous_filename_record(self) -> None:
        obj = MediaFile(
            file=make_uploaded_file(name="poster.png", content=b"abc", content_type="image/png"),
            filename="custom-name.png",
        )
        obj.pk = uuid.uuid4()
        obj._state.adding = False

        obj._populate_derived_fields()

        assert obj.filename == "custom-name.png"
        assert obj.mime_type == "image/png"
        assert obj.size_bytes == 3
        assert obj.file_type == MediaFile.FileType.IMAGE


class TestMediaFileModel:
    def test_id_is_uuid(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file())
        assert isinstance(obj.id, uuid.UUID)

    def test_media_file_meta_configuration(self) -> None:
        assert MediaFile._meta.db_table == "media_file"
        assert MediaFile._meta.verbose_name == "Media file"
        assert MediaFile._meta.verbose_name_plural == "Media files"
        assert list(MediaFile._meta.ordering) == ["-created_at"]

    def test_str_returns_filename(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="season-brochure.pdf"))
        assert str(obj) == "season-brochure.pdf"

    def test_file_is_stored_under_upload_prefix(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="season-brochure.pdf"))
        assert obj.file.name.startswith("uploads/")
        assert obj.file.name.endswith(".pdf")

    def test_pdf_mime_type_sets_pdf_file_type(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="brochure.pdf", content_type="application/pdf"))
        assert obj.file_type == MediaFile.FileType.PDF

    def test_png_mime_type_sets_image_file_type(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="poster.png", content_type="image/png"))
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_jpeg_mime_type_sets_image_file_type(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="poster.jpg", content_type="image/jpeg"))
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_unknown_mime_type_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc:
            MediaFile.objects.create(file=make_uploaded_file(name="archive.bin", content_type=None))
        assert "file" in exc.value.message_dict

    def test_filename_is_derived_from_uploaded_file(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="poster.png", content_type="image/png"))
        assert obj.filename == "poster.png"

    def test_clean_requires_file(self) -> None:
        with pytest.raises(ValidationError) as exc:
            MediaFile().clean()
        assert "file" in exc.value.message_dict

    def test_clean_rejects_oversized_file(self) -> None:
        file = make_uploaded_file(content=b"x" * (MediaFile.MAX_FILE_SIZE + 1))
        obj = MediaFile(file=file)
        with pytest.raises(ValidationError) as exc:
            obj.clean()
        assert "file" in exc.value.message_dict

    def test_clean_rejects_mismatching_content_signature(self) -> None:
        obj = MediaFile(file=make_uploaded_file(name="poster.png", content=b"%PDF-1.7 fake", content_type="image/png"))
        with pytest.raises(ValidationError) as exc:
            obj.clean()
        assert "file" in exc.value.message_dict

    def test_clean_rejects_extension_mismatch(self) -> None:
        obj = MediaFile(file=make_uploaded_file(name="poster.pdf", content=make_png_bytes(), content_type=None))
        with pytest.raises(ValidationError) as exc:
            obj.clean()
        assert "file" in exc.value.message_dict

    def test_file_has_changed_detects_replacement(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="one.pdf"))
        obj.file = make_uploaded_file(name="two.pdf")
        assert obj._file_has_changed() is True

    def test_metadata_updates_when_file_changes_and_filename_matches_previous(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="one.pdf", content_type="application/pdf"))
        obj.filename = "one.pdf"
        obj.file = make_uploaded_file(name="two.png", content=b"abc", content_type="image/png")
        obj.save()
        obj.refresh_from_db()
        assert obj.filename == "two.png"
        assert obj.mime_type == "image/png"
        assert obj.size_bytes == 3
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_existing_custom_filename_is_preserved_when_file_changes(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="one.pdf"))
        obj.filename = "custom-name.pdf"
        obj.file = make_uploaded_file(name="two.png", content=b"abc", content_type="image/png")
        obj.save()
        obj.refresh_from_db()
        assert obj.filename == "custom-name.pdf"
        assert obj.mime_type == "image/png"
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_existing_filename_is_preserved_when_file_unchanged(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="one.pdf"))
        obj.filename = "custom-name.pdf"
        obj.save()
        obj.refresh_from_db()
        assert obj.filename == "custom-name.pdf"

    def test_clean_populates_fields_on_valid_file(self) -> None:
        obj = MediaFile(file=make_uploaded_file(name="poster.png", content=b"abc", content_type="image/png"))
        obj.clean()
        assert obj.filename == "poster.png"
        assert obj.mime_type == "image/png"
        assert obj.size_bytes == 3
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_save_without_file_still_calls_super(self) -> None:
        obj = MediaFile()
        with patch("apps.media_files.models.BaseModel.save", autospec=True) as mocked_save:
            obj.save()
        mocked_save.assert_called_once()


class TestMediaFileTranslationModel:
    def test_translation_meta_configuration(self) -> None:
        assert MediaFileTranslation._meta.db_table == "media_file_translation"
        assert MediaFileTranslation._meta.verbose_name == "Media file translation"
        assert MediaFileTranslation._meta.verbose_name_plural == "Media file translations"
        assert list(MediaFileTranslation._meta.ordering) == ["language__code"]

    def test_description_max_length_constant_matches_translation_field(self) -> None:
        assert MediaFileTranslation._meta.get_field("description").max_length == DESCRIPTION_MAX_LENGTH

    def test_description_is_optional(self, dutch_language: Language) -> None:
        obj = MediaFileTranslation(
            media_file=MediaFile.objects.create(file=make_uploaded_file()),
            language=dutch_language,
            description="",
        )
        obj.full_clean()

    def test_description_length_is_enforced(self, dutch_language: Language) -> None:
        obj = MediaFileTranslation(
            media_file=MediaFile.objects.create(file=make_uploaded_file()),
            language=dutch_language,
            description="x" * (DESCRIPTION_MAX_LENGTH + 1),
        )
        with pytest.raises(ValidationError) as exc:
            obj.full_clean()
        assert "description" in exc.value.message_dict

    def test_str_returns_language_code_and_filename(self, dutch_language: Language) -> None:
        media_file = MediaFile.objects.create(file=make_uploaded_file(name="poster.pdf"))
        translation = MediaFileTranslation.objects.create(
            media_file=media_file,
            language=dutch_language,
            description="Affiche",
        )
        assert str(translation) == "nl - poster.pdf"

    def test_unique_constraint_rejects_same_language_twice(
        self,
        dutch_language: Language,
    ) -> None:
        media_file = MediaFile.objects.create(file=make_uploaded_file(name="poster.pdf"))
        MediaFileTranslation.objects.create(
            media_file=media_file,
            language=dutch_language,
            description="NL",
        )
        duplicate = MediaFileTranslation(
            media_file=media_file,
            language=dutch_language,
            description="Nog eens NL",
        )
        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_index_and_constraint_names_exist(self) -> None:
        constraint_names = {constraint.name for constraint in MediaFileTranslation._meta.constraints}
        index_names = {index.name for index in MediaFileTranslation._meta.indexes}
        assert "unique_media_file_language" in constraint_names
        assert "idx_media_file_lang" in index_names

    def test_related_name_returns_translations(
        self,
        dutch_language: Language,
        english_language: Language,
    ) -> None:
        media_file = MediaFile.objects.create(file=make_uploaded_file(name="poster.pdf"))
        first = MediaFileTranslation.objects.create(media_file=media_file, language=dutch_language, description="NL")
        second = MediaFileTranslation.objects.create(media_file=media_file, language=english_language, description="EN")
        assert list(media_file.translations.order_by("language__code")) == [second, first]
