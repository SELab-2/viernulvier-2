"""
Covers:
- __str__ output
- UUID primary key creation
- nullable uploaded_by
- inherited external_id field
- upload path format
- file_type inference in clean()
- BaseModel save() calling full_clean()
- manual file_type override being normalized on save
- delete behavior with SET_NULL uploader relation
"""

import os
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.media_files.models import MediaFile, upload_to_media

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
# upload_to_media
# =====================================================


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
        uuid.UUID(stem)  # must not raise


# =====================================================
# MediaFile
# =====================================================


class TestMediaFile:
    def test_id_is_uuid(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(),
            original_name="test.pdf",
            mime_type="application/pdf",
            size_bytes=123,
        )
        assert isinstance(obj.id, uuid.UUID)

    def test_external_id_is_optional(self) -> None:
        obj = MediaFile(
            file=make_uploaded_file(),
            original_name="test.pdf",
            mime_type="application/pdf",
            size_bytes=123,
            external_id=None,
        )
        obj.full_clean()  # should not raise

    def test_uploaded_by_is_optional(self) -> None:
        obj = MediaFile(
            file=make_uploaded_file(),
            original_name="test.pdf",
            mime_type="application/pdf",
            size_bytes=123,
            uploaded_by=None,
        )
        obj.full_clean()  # should not raise

    def test_str_returns_original_name(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(),
            original_name="season-brochure.pdf",
            mime_type="application/pdf",
            size_bytes=123,
        )
        assert str(obj) == "season-brochure.pdf"

    def test_file_is_stored_under_upload_prefix(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(name="season-brochure.pdf"),
            original_name="season-brochure.pdf",
            mime_type="application/pdf",
            size_bytes=123,
        )
        assert obj.file.name.startswith("media/uploads/")
        assert obj.file.name.endswith(".pdf")

    def test_pdf_mime_type_sets_pdf_file_type(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(name="brochure.pdf", content_type="application/pdf"),
            original_name="brochure.pdf",
            mime_type="application/pdf",
            size_bytes=123,
        )
        assert obj.file_type == MediaFile.FileType.PDF

    def test_png_mime_type_sets_image_file_type(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(name="poster.png", content_type="image/png"),
            original_name="poster.png",
            mime_type="image/png",
            size_bytes=123,
        )
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_jpeg_mime_type_sets_image_file_type(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(name="poster.jpg", content_type="image/jpeg"),
            original_name="poster.jpg",
            mime_type="image/jpeg",
            size_bytes=123,
        )
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_webp_mime_type_sets_image_file_type(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(name="poster.webp", content_type="image/webp"),
            original_name="poster.webp",
            mime_type="image/webp",
            size_bytes=123,
        )
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_unknown_mime_type_sets_other_file_type(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(name="notes.txt", content_type="text/plain"),
            original_name="notes.txt",
            mime_type="text/plain",
            size_bytes=123,
        )
        assert obj.file_type == MediaFile.FileType.OTHER

    def test_manual_file_type_override_is_normalized_by_clean(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(name="brochure.pdf", content_type="application/pdf"),
            original_name="brochure.pdf",
            mime_type="application/pdf",
            size_bytes=123,
            file_type=MediaFile.FileType.OTHER,
        )
        assert obj.file_type == MediaFile.FileType.PDF

    def test_clean_is_called_automatically_via_basemodel_save(self) -> None:
        obj = MediaFile(
            file=make_uploaded_file(name="image.jpg", content_type="image/jpeg"),
            original_name="image.jpg",
            mime_type="image/jpeg",
            size_bytes=123,
            file_type=MediaFile.FileType.OTHER,
        )
        obj.save()
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_deleting_uploader_sets_uploaded_by_to_null(self) -> None:
        user = User.objects.create_user(
            username="media-owner",
            email="owner@example.com",
            password="password",
        )
        obj = MediaFile.objects.create(
            file=make_uploaded_file(),
            original_name="test.pdf",
            mime_type="application/pdf",
            size_bytes=123,
            uploaded_by=user,
        )

        user.delete()
        obj.refresh_from_db()

        assert obj.uploaded_by is None

    def test_user_reverse_relation_uploaded_media(self) -> None:
        user = User.objects.create_user(
            username="reverse-user",
            email="reverse@example.com",
            password="password",
        )
        MediaFile.objects.create(
            file=make_uploaded_file(name="one.pdf"),
            original_name="one.pdf",
            mime_type="application/pdf",
            size_bytes=100,
            uploaded_by=user,
        )
        MediaFile.objects.create(
            file=make_uploaded_file(name="two.pdf"),
            original_name="two.pdf",
            mime_type="application/pdf",
            size_bytes=200,
            uploaded_by=user,
        )

        assert user.uploaded_media.count() == 2

    def test_created_at_is_set_on_create(self) -> None:
        obj = MediaFile.objects.create(
            file=make_uploaded_file(),
            original_name="test.pdf",
            mime_type="application/pdf",
            size_bytes=123,
        )
        assert obj.created_at is not None
        