"""
Tests for apps/media_files/serializers.py

Covers:
- MediaFileSerializer field presence and completeness
- MediaFileSerializer serialization of scalar fields
- MediaFileUploadSerializer field presence and read/write behaviour
- file validation for supported MIME types
- file validation for unsupported MIME types
- file validation for missing file
- file validation for oversized files
- create() deriving metadata from the uploaded file
- create() assigning uploaded_by from request.user
- create() leaving uploaded_by as None for anonymous users
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.media_files.models import MediaFile
from apps.media_files.serializers import MediaFileSerializer, MediaFileUploadSerializer

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str = "application/pdf",
) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)


def make_request(user=None, url: str = "/api/v1/media/") -> Request:
    factory = RequestFactory()
    django_request = factory.post(url)

    request = Request(django_request)

    request.user = user

    return request


# ---------------------------------------------------------------------------
# MediaFileSerializer - field presence
# ---------------------------------------------------------------------------


class TestMediaFileSerializerFields(TestCase):
    """Verify field presence and completeness of MediaFileSerializer."""

    def setUp(self) -> None:
        self.media_file = MediaFile.objects.create(
            file=make_uploaded_file(name="season-brochure.pdf", content_type="application/pdf"),
            original_name="season-brochure.pdf",
            mime_type="application/pdf",
            size_bytes=123,
        )

    def test_expected_fields_are_present(self) -> None:
        data = MediaFileSerializer(self.media_file).data
        expected = {
            "id",
            "external_id",
            "file",
            "original_name",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        }
        for field in expected:
            with self.subTest(field=field):
                assert field in data

    def test_no_extra_fields_are_exposed(self) -> None:
        data = MediaFileSerializer(self.media_file).data
        assert set(data.keys()) == {
            "id",
            "external_id",
            "file",
            "original_name",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        }


# ---------------------------------------------------------------------------
# MediaFileSerializer - scalar values
# ---------------------------------------------------------------------------


class TestMediaFileSerializerValues(TestCase):
    """Verify scalar field serialization of MediaFileSerializer."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="serializer-user",
            email="serializer@example.com",
            password="password",
        )
        self.media_file = MediaFile.objects.create(
            file=make_uploaded_file(name="poster.png", content_type="image/png"),
            original_name="poster.png",
            mime_type="image/png",
            size_bytes=456,
            uploaded_by=self.user,
            external_id="ext-123",
        )
        self.data = MediaFileSerializer(self.media_file).data

    def test_id_is_present(self) -> None:
        assert self.data["id"] is not None

    def test_external_id_is_correct(self) -> None:
        assert self.data["external_id"] == "ext-123"

    def test_file_is_serialized(self) -> None:
        assert isinstance(self.data["file"], str)
        assert self.data["file"].endswith(".png")

    def test_original_name_is_correct(self) -> None:
        assert self.data["original_name"] == "poster.png"

    def test_mime_type_is_correct(self) -> None:
        assert self.data["mime_type"] == "image/png"

    def test_size_bytes_is_correct(self) -> None:
        assert self.data["size_bytes"] == 456

    def test_file_type_is_correct(self) -> None:
        assert self.data["file_type"] == MediaFile.FileType.IMAGE

    def test_uploaded_by_is_serialized_as_pk(self) -> None:
        assert self.data["uploaded_by"] == self.user.pk

    def test_created_at_is_present(self) -> None:
        assert self.data["created_at"] is not None


# ---------------------------------------------------------------------------
# MediaFileUploadSerializer - field presence / mode
# ---------------------------------------------------------------------------


class TestMediaFileUploadSerializerFields(TestCase):
    """Verify field presence and read/write behaviour of MediaFileUploadSerializer."""

    def test_expected_fields_are_present(self) -> None:
        serializer = MediaFileUploadSerializer()
        fields = set(serializer.fields.keys())

        assert fields == {
            "id",
            "external_id",
            "file",
            "original_name",
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

        assert serializer.fields["id"].read_only is True
        assert serializer.fields["external_id"].read_only is True
        assert serializer.fields["original_name"].read_only is True
        assert serializer.fields["mime_type"].read_only is True
        assert serializer.fields["size_bytes"].read_only is True
        assert serializer.fields["file_type"].read_only is True
        assert serializer.fields["uploaded_by"].read_only is True
        assert serializer.fields["created_at"].read_only is True


# ---------------------------------------------------------------------------
# MediaFileUploadSerializer - validate_file
# ---------------------------------------------------------------------------


class TestMediaFileUploadSerializerValidation(TestCase):
    """Verify file validation behaviour."""

    def test_accepts_pdf_file(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="brochure.pdf", content_type="application/pdf")}
        )
        assert serializer.is_valid(), serializer.errors

    def test_accepts_png_file(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="poster.png", content_type="image/png")}
        )
        assert serializer.is_valid(), serializer.errors

    def test_accepts_jpeg_file(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="poster.jpg", content_type="image/jpeg")}
        )
        assert serializer.is_valid(), serializer.errors

    def test_accepts_webp_file(self) -> None:
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="poster.webp", content_type="image/webp")}
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
        assert "Unsupported file type" in str(serializer.errors["file"][0])

    def test_rejects_oversized_file(self) -> None:
        content = b"x" * (MediaFileUploadSerializer.MAX_FILE_SIZE + 1)
        oversized = SimpleUploadedFile(
            "huge.pdf",
            content,
            content_type="application/pdf",
        )

        serializer = MediaFileUploadSerializer(data={"file": oversized})

        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_validate_file_returns_value_for_valid_file(self) -> None:
        serializer = MediaFileUploadSerializer()
        uploaded_file = make_uploaded_file(name="ok.pdf", content_type="application/pdf")

        result = serializer.validate_file(uploaded_file)

        assert result == uploaded_file


# ---------------------------------------------------------------------------
# Upload serializer creation tests
# ---------------------------------------------------------------------------


class TestMediaFileUploadSerializerCreate(TestCase):
    """Verify object creation and derived metadata."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="upload-user",
            email="upload@example.com",
            password="password",
        )

    def test_create_sets_original_name(self) -> None:
        request = make_request(user=self.user)
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="poster.png", content_type="image/png")},
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert obj.original_name == "poster.png"

    def test_create_sets_mime_type(self) -> None:
        request = make_request(user=self.user)
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="brochure.pdf", content_type="application/pdf")},
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert obj.mime_type == "application/pdf"

    def test_create_sets_size_bytes(self) -> None:
        request = make_request(user=self.user)
        uploaded = make_uploaded_file(
            name="poster.png",
            content=b"abcdef",
            content_type="image/png",
        )
        serializer = MediaFileUploadSerializer(
            data={"file": uploaded},
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert obj.size_bytes == 6

    def test_create_sets_file_type_for_image(self) -> None:
        request = make_request(user=self.user)
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="poster.png", content_type="image/png")},
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_create_sets_file_type_for_pdf(self) -> None:
        request = make_request(user=self.user)
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file(name="brochure.pdf", content_type="application/pdf")},
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert obj.file_type == MediaFile.FileType.PDF

    def test_create_assigns_uploaded_by_for_authenticated_user(self) -> None:
        request = make_request(user=self.user)
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file()},
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert obj.uploaded_by == self.user

    def test_create_leaves_uploaded_by_none_for_anonymous_user(self) -> None:
        class AnonymousUser:
            is_authenticated = False

        request = make_request(user=AnonymousUser())
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file()},
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert obj.uploaded_by is None

    def test_create_persists_object(self) -> None:
        request = make_request(user=self.user)
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file()},
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert MediaFile.objects.filter(pk=obj.pk).exists()

    def test_create_returns_media_file_instance(self) -> None:
        request = make_request(user=self.user)
        serializer = MediaFileUploadSerializer(
            data={"file": make_uploaded_file()},
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert isinstance(obj, MediaFile)
