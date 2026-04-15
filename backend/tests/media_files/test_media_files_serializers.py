"""Tests for apps.media_files.serializers."""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
import pytest
from rest_framework import serializers
from rest_framework.request import Request

from apps.media_files.models import MediaFile
from apps.media_files.serializers import MediaFileSerializer, MediaFileUploadSerializer

User = get_user_model()


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str | None = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


def make_request(user=None, url: str = "/api/v1/media/") -> Request:
    factory = RequestFactory()
    django_request = factory.post(url)
    request = Request(django_request)
    request.user = user
    return request


class TestMediaFileSerializerFields(TestCase):
    def setUp(self) -> None:
        self.media_file = MediaFile.objects.create(file=make_uploaded_file(name="season-brochure.pdf"))

    def test_expected_fields_are_present(self) -> None:
        data = MediaFileSerializer(self.media_file).data
        expected = {
            "id",
            "external_id",
            "file",
            "filename",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        }
        assert set(data.keys()) == expected

    def test_all_fields_are_read_only(self) -> None:
        serializer = MediaFileSerializer()
        assert set(serializer.Meta.read_only_fields) == set(serializer.Meta.fields)


class TestMediaFileSerializerValues(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="serializer-user",
            email="serializer@example.com",
            password="password",
        )
        self.media_file = MediaFile.objects.create(
            file=make_uploaded_file(name="poster.png", content_type="image/png"),
            uploaded_by=self.user,
            external_id="ext-123",
        )
        self.data = MediaFileSerializer(self.media_file).data

    def test_scalar_values_are_serialized(self) -> None:
        assert self.data["external_id"] == "ext-123"
        assert self.data["filename"] == "poster.png"
        assert self.data["mime_type"] == "image/png"
        assert self.data["size_bytes"] == len(b"dummy content")
        assert self.data["file_type"] == MediaFile.FileType.IMAGE
        assert self.data["uploaded_by"] == self.user.username
        assert self.data["created_at"] is not None
        assert self.data["file"].endswith(".png")


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
            "uploaded_by",
            "created_at",
        }

    def test_file_field_is_write_only(self) -> None:
        serializer = MediaFileUploadSerializer()
        assert serializer.fields["file"].write_only is True

    def test_derived_fields_are_read_only(self) -> None:
        serializer = MediaFileUploadSerializer()
        for field in ("id", "external_id", "filename", "mime_type", "size_bytes", "file_type", "uploaded_by", "created_at"):
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

    def test_rejects_missing_file(self) -> None:
        serializer = MediaFileUploadSerializer(data={})
        assert not serializer.is_valid()
        assert "file" in serializer.errors

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


class TestMediaFileUploadSerializerCreate(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="upload-user",
            email="upload@example.com",
            password="password",
        )

    def test_create_sets_metadata_for_authenticated_user(self) -> None:
        request = make_request(user=self.user)
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="poster.png", content=b"abcdef", content_type="image/png")},
            context={"request": request},
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.filename == "poster.png"
        assert obj.mime_type == "image/png"
        assert obj.size_bytes == 6
        assert obj.file_type == MediaFile.FileType.IMAGE
        assert obj.uploaded_by == self.user
        assert MediaFile.objects.filter(pk=obj.pk).exists()

    def test_create_leaves_uploaded_by_none_for_anonymous_user(self) -> None:
        class AnonymousUser:
            is_authenticated = False

        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file()},
            context={"request": make_request(user=AnonymousUser())},
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.uploaded_by is None

    def test_create_returns_media_file_instance(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file()},
            context={"request": make_request(user=self.user)},
        )
        assert serializer.is_valid(), serializer.errors
        assert isinstance(serializer.save(), MediaFile)

    def test_validate_file_raises_for_falsy_value(self) -> None:
        """Covers serializers.py line 74: validate_file called with falsy value."""
        serializer = MediaFileUploadSerializer()
        with pytest.raises(serializers.ValidationError, match="No file was uploaded"):
            serializer.validate_file(None)
