"""Tests for apps.media_files.models."""

import os
from unittest.mock import MagicMock
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.media_files.models import MediaFile, upload_to_media

pytestmark = pytest.mark.django_db

User = get_user_model()


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str | None = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


class TestUploadToMedia:
    def test_upload_path_uses_media_uploads_prefix(self) -> None:
        path = upload_to_media(instance=None, filename="poster.png")
        assert path.startswith("media/uploads/")

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

    def test_derive_file_type_recognizes_image(self) -> None:
        assert MediaFile()._derive_file_type("image/webp") == MediaFile.FileType.IMAGE

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


class TestMediaFileModel:
    def test_id_is_uuid(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file())
        assert isinstance(obj.id, uuid.UUID)

    def test_external_id_is_optional(self) -> None:
        obj = MediaFile(file=make_uploaded_file(), external_id=None)
        obj.full_clean()

    def test_uploaded_by_is_optional(self) -> None:
        obj = MediaFile(file=make_uploaded_file(), uploaded_by=None)
        obj.full_clean()

    def test_str_returns_filename(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="season-brochure.pdf"))
        assert str(obj) == "season-brochure.pdf"

    def test_file_is_stored_under_upload_prefix(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="season-brochure.pdf"))
        assert obj.file.name.startswith("media/uploads/")
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

    def test_webp_mime_type_sets_other_file_type(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="poster.webp", content_type="image/webp"))
        assert obj.file_type == MediaFile.FileType.OTHER

    def test_unknown_mime_type_sets_other_file_type(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="archive.bin", content_type=None))
        assert obj.file_type == MediaFile.FileType.OTHER

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

    def test_file_has_changed_detects_replacement(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="one.pdf"))
        obj.file = make_uploaded_file(name="two.pdf")
        assert obj._file_has_changed() is True

    def test_metadata_updates_when_file_changes(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="one.pdf", content_type="application/pdf"))
        obj.file = make_uploaded_file(name="two.png", content=b"abc", content_type="image/png")
        obj.filename = ""
        obj.save()
        obj.refresh_from_db()
        assert obj.filename == "two.png"
        assert obj.mime_type == "image/png"
        assert obj.size_bytes == 3
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_existing_filename_is_preserved_when_file_unchanged(self) -> None:
        obj = MediaFile.objects.create(file=make_uploaded_file(name="one.pdf"))
        obj.filename = "custom-name.pdf"
        obj.save()
        obj.refresh_from_db()
        assert obj.filename == "custom-name.pdf"

    def test_uploaded_by_set_null_when_user_deleted(self) -> None:
        user = User.objects.create_user(username="uploader", email="uploader@example.com", password="password")
        obj = MediaFile.objects.create(file=make_uploaded_file(), uploaded_by=user)
        user.delete()
        obj.refresh_from_db()
        assert obj.uploaded_by is None

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
