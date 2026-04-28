"""Tests for apps.media_files.serializers."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
import pytest
from rest_framework import serializers

from apps.languages.models import Language
from apps.media_files.models import MediaFile, MediaFileTranslation
from apps.media_files.serializers import MediaFileSerializer, MediaFileUploadSerializer


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str | None = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


@override_settings(LANGUAGE_CODE="nl")
class TestMediaFileSerializerFields(TestCase):
    def setUp(self) -> None:
        self.nl = Language.objects.create(code="nl", name="Dutch", is_active=True)
        self.en = Language.objects.create(code="en", name="English", is_active=True)
        self.media_file = MediaFile.objects.create(
            file=make_uploaded_file(name="season-brochure.pdf"),
            external_id="ext-123",
        )
        MediaFileTranslation.objects.create(
            media_file=self.media_file,
            language=self.nl,
            description="Seizoensbrochure voor website en drukwerk.",
        )
        MediaFileTranslation.objects.create(
            media_file=self.media_file,
            language=self.en,
            description="Season brochure for website and print.",
        )

    def test_expected_fields_are_present(self) -> None:
        data = MediaFileSerializer(self.media_file).data
        expected = {
            "id",
            "external_id",
            "file",
            "filename",
            "display_description",
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

    def test_translated_values_are_serialized(self) -> None:
        data = MediaFileSerializer(self.media_file).data
        assert data["external_id"] == "ext-123"
        assert data["filename"] == "season-brochure.pdf"
        assert data["display_description"] == "Seizoensbrochure voor website en drukwerk."
        assert data["description"] == {
            "nl": "Seizoensbrochure voor website en drukwerk.",
            "en": "Season brochure for website and print.",
        }
        assert data["mime_type"] == "application/pdf"
        assert data["size_bytes"] == len(b"dummy content")
        assert data["file_type"] == MediaFile.FileType.PDF
        assert data["created_at"] is not None
        assert data["file"].endswith(".pdf")

    def test_display_description_falls_back_to_first_available_translation_when_base_missing(self) -> None:
        fr = Language.objects.create(code="fr", name="French", is_active=True)
        media_file = MediaFile.objects.create(file=make_uploaded_file(name="poster.pdf"))
        MediaFileTranslation.objects.create(
            media_file=media_file,
            language=fr,
            description="Description française.",
        )
        data = MediaFileSerializer(media_file).data
        assert data["display_description"] == "Description française."
        assert data["description"] == {"fr": "Description française."}

    def test_description_is_empty_dict_when_no_translations_exist(self) -> None:
        media_file = MediaFile.objects.create(file=make_uploaded_file(name="empty.pdf"))
        data = MediaFileSerializer(media_file).data
        assert data["description"] == {}
        assert data["display_description"] is None


class TestMediaFileUploadSerializerFields(TestCase):
    def test_expected_fields_are_present(self) -> None:
        serializer = MediaFileUploadSerializer()
        assert set(serializer.fields.keys()) == {
            "id",
            "external_id",
            "file",
            "filename",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
        }

    def test_file_field_is_write_only_and_optional_for_updates(self) -> None:
        serializer = MediaFileUploadSerializer()
        assert serializer.fields["file"].write_only is True
        assert serializer.fields["file"].required is False

    def test_description_field_is_removed_from_write_serializer(self) -> None:
        serializer = MediaFileUploadSerializer()
        assert "description" not in serializer.fields

    def test_derived_fields_are_read_only(self) -> None:
        serializer = MediaFileUploadSerializer()
        for field in ("id", "filename", "mime_type", "size_bytes", "file_type", "created_at"):
            assert serializer.fields[field].read_only is True

    def test_external_id_help_text_and_nullability_are_configured(self) -> None:
        serializer = MediaFileUploadSerializer()
        assert serializer.fields["external_id"].required is False
        assert serializer.fields["external_id"].allow_null is True
        assert "external identifier" in serializer.fields["external_id"].help_text.lower()


class TestMediaFileUploadSerializerValidation(TestCase):
    def test_accepts_supported_types(self) -> None:
        for name, content_type in (
            ("brochure.pdf", "application/pdf"),
            ("poster.png", "image/png"),
            ("poster.jpg", "image/jpeg"),
        ):
            with self.subTest(content_type=content_type):
                serializer = MediaFileUploadSerializer(
                    data={"file": make_uploaded_file(name=name, content_type=content_type)}
                )
                assert serializer.is_valid(), serializer.errors

    def test_validate_requires_file_on_create(self) -> None:
        serializer = MediaFileUploadSerializer(data={"external_id": "Alleen metadata"})
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


class TestMediaFileUploadSerializerMutations(TestCase):
    def test_create_sets_metadata_and_optional_fields(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={
                "file": make_uploaded_file(name="poster.png", content=b"abcdef", content_type="image/png"),
                "external_id": "poster-001",
            }
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.filename == "poster.png"
        assert obj.mime_type == "image/png"
        assert obj.size_bytes == 6
        assert obj.file_type == MediaFile.FileType.IMAGE
        assert obj.external_id == "poster-001"
        assert MediaFile.objects.filter(pk=obj.pk).exists()

    def test_create_returns_media_file_instance(self) -> None:
        serializer = MediaFileUploadSerializer(data={"file": make_uploaded_file()})
        assert serializer.is_valid(), serializer.errors
        assert isinstance(serializer.save(), MediaFile)

    def test_update_supports_metadata_only_patch(self) -> None:
        instance = MediaFile.objects.create(
            file=make_uploaded_file(name="old.pdf"),
            external_id="old-id",
        )
        serializer = MediaFileUploadSerializer(
            instance=instance,
            data={"external_id": "new-id"},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.external_id == "new-id"
        assert obj.filename == "old.pdf"

    def test_update_replaces_file_when_supplied(self) -> None:
        instance = MediaFile.objects.create(
            file=make_uploaded_file(name="old.pdf", content_type="application/pdf"),
        )
        serializer = MediaFileUploadSerializer(
            instance=instance,
            data={
                "file": make_uploaded_file(name="new.png", content=b"abc", content_type="image/png"),
                "external_id": "ext-2",
            },
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        obj.refresh_from_db()
        assert obj.external_id == "ext-2"
        assert obj.filename == "new.png"
        assert obj.mime_type == "image/png"
        assert obj.size_bytes == 3
        assert obj.file_type == MediaFile.FileType.IMAGE
