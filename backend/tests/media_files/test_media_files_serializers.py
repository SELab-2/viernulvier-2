"""Tests for apps.media_files.serializers."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
import pytest
from rest_framework import serializers

from apps.media_files.models import DESCRIPTION_MAX_LENGTH, MediaFile
from apps.media_files.serializers import MediaFileSerializer, MediaFileUploadSerializer


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str | None = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


class TestMediaFileSerializerFields(TestCase):
    def setUp(self) -> None:
        self.media_file = MediaFile.objects.create(
            file=make_uploaded_file(name="season-brochure.pdf"),
            description="Seizoensbrochure voor website en drukwerk.",
            external_id="ext-123",
        )

    def test_expected_fields_are_present(self) -> None:
        data = MediaFileSerializer(self.media_file).data
        expected = {
            "id",
            "external_id",
            "file",
            "filename",
            "description",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
        }
        assert set(data.keys()) == expected

    def test_all_fields_are_read_only(self) -> None:
        serializer = MediaFileSerializer()
        assert set(serializer.Meta.read_only_fields) == set(serializer.Meta.fields)

    def test_scalar_values_are_serialized(self) -> None:
        data = MediaFileSerializer(self.media_file).data
        assert data["external_id"] == "ext-123"
        assert data["filename"] == "season-brochure.pdf"
        assert data["description"] == "Seizoensbrochure voor website en drukwerk."
        assert data["mime_type"] == "application/pdf"
        assert data["size_bytes"] == len(b"dummy content")
        assert data["file_type"] == MediaFile.FileType.PDF
        assert data["created_at"] is not None
        assert data["file"].endswith(".pdf")


class TestMediaFileUploadSerializerFields(TestCase):
    def test_expected_fields_are_present(self) -> None:
        serializer = MediaFileUploadSerializer()
        assert set(serializer.fields.keys()) == {
            "id",
            "external_id",
            "file",
            "filename",
            "description",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
        }

    def test_file_field_is_write_only_and_optional_for_updates(self) -> None:
        serializer = MediaFileUploadSerializer()
        assert serializer.fields["file"].write_only is True
        assert serializer.fields["file"].required is False

    def test_description_field_constraints_match_model(self) -> None:
        serializer = MediaFileUploadSerializer()
        assert serializer.fields["description"].required is False
        assert serializer.fields["description"].allow_blank is True
        assert serializer.fields["description"].max_length == DESCRIPTION_MAX_LENGTH

    def test_derived_fields_are_read_only(self) -> None:
        serializer = MediaFileUploadSerializer()
        for field in ("id", "filename", "mime_type", "size_bytes", "file_type", "created_at"):
            assert serializer.fields[field].read_only is True


class TestMediaFileUploadSerializerValidation(TestCase):
    def test_accepts_supported_types(self) -> None:
        for name, content_type in (
            ("brochure.pdf", "application/pdf"),
            ("poster.png", "image/png"),
            ("poster.jpg", "image/jpeg"),
            ("poster.webp", "image/webp"),
        ):
            with self.subTest(content_type=content_type):
                serializer = MediaFileUploadSerializer(
                    data={"file": make_uploaded_file(name=name, content_type=content_type)}
                )
                assert serializer.is_valid(), serializer.errors

    def test_validate_requires_file_on_create(self) -> None:
        serializer = MediaFileUploadSerializer(data={"description": "Alleen metadata"})
        assert not serializer.is_valid()
        assert serializer.errors == {"file": ["This field is required."]}

    def test_rejects_unsupported_file_type(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="notes.txt", content_type="text/plain")}
        )
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_rejects_file_without_content_type(self) -> None:
        serializer = MediaFileUploadSerializer(data={"file": make_uploaded_file(name="notes.txt", content_type=None)})
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_rejects_oversized_file(self) -> None:
        content = b"x" * (MediaFileUploadSerializer.MAX_FILE_SIZE + 1)
        oversized = SimpleUploadedFile("huge.pdf", content, content_type="application/pdf")
        serializer = MediaFileUploadSerializer(data={"file": oversized})
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_rejects_mismatching_content_signature(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="poster.png", content=b"%PDF-1.7 fake", content_type="image/png")}
        )
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_rejects_extension_mismatch(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="poster.pdf", content_type="image/png")}
        )
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_validate_file_returns_value_for_valid_file(self) -> None:
        serializer = MediaFileUploadSerializer()
        uploaded_file = make_uploaded_file(name="ok.pdf", content_type="application/pdf")
        assert serializer.validate_file(uploaded_file) == uploaded_file

    def test_validate_file_raises_for_invalid_file(self) -> None:
        serializer = MediaFileUploadSerializer()
        with pytest.raises(serializers.ValidationError):
            serializer.validate_file(make_uploaded_file(name="bad.txt", content_type="text/plain"))

    def test_description_max_length_is_enforced(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={
                "file": make_uploaded_file(),
                "description": "x" * (DESCRIPTION_MAX_LENGTH + 1),
            }
        )
        assert not serializer.is_valid()
        assert "description" in serializer.errors


class TestMediaFileUploadSerializerMutations(TestCase):
    def test_create_sets_metadata_and_optional_fields(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={
                "file": make_uploaded_file(name="poster.png", content=b"abcdef", content_type="image/png"),
                "description": "Poster voor social.",
                "external_id": "poster-001",
            }
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.filename == "poster.png"
        assert obj.mime_type == "image/png"
        assert obj.size_bytes == 6
        assert obj.file_type == MediaFile.FileType.IMAGE
        assert obj.description == "Poster voor social."
        assert obj.external_id == "poster-001"
        assert MediaFile.objects.filter(pk=obj.pk).exists()

    def test_create_returns_media_file_instance(self) -> None:
        serializer = MediaFileUploadSerializer(data={"file": make_uploaded_file()})
        assert serializer.is_valid(), serializer.errors
        assert isinstance(serializer.save(), MediaFile)

    def test_update_supports_metadata_only_patch(self) -> None:
        instance = MediaFile.objects.create(
            file=make_uploaded_file(name="old.pdf"),
            description="Oud",
            external_id="old-id",
        )
        serializer = MediaFileUploadSerializer(
            instance=instance,
            data={"description": "Nieuw", "external_id": "new-id"},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.description == "Nieuw"
        assert obj.external_id == "new-id"
        assert obj.filename == "old.pdf"

    def test_update_replaces_file_when_supplied(self) -> None:
        instance = MediaFile.objects.create(
            file=make_uploaded_file(name="old.pdf", content_type="application/pdf"),
            description="Oud",
        )
        serializer = MediaFileUploadSerializer(
            instance=instance,
            data={
                "file": make_uploaded_file(name="new.png", content=b"abc", content_type="image/png"),
                "description": "Nieuw",
            },
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        obj.refresh_from_db()
        assert obj.description == "Nieuw"
        assert obj.filename == "new.png"
        assert obj.mime_type == "image/png"
        assert obj.size_bytes == 3
        assert obj.file_type == MediaFile.FileType.IMAGE
