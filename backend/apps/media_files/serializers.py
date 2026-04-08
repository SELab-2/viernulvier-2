"""Serializers for the Media Files app."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import MediaFile


class MediaFileSerializer(serializers.ModelSerializer):
    """Read serializer for media files."""

    class Meta:
        model = MediaFile
        fields = [
            "id",
            "external_id",
            "file",
            "original_name",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "external_id",
            "file",
            "original_name",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        ]
        extra_kwargs = {
            "file": {
                "help_text": "Stored file location/URL.",
            },
            "original_name": {
                "help_text": "Original filename as uploaded by the user.",
            },
            "mime_type": {
                "help_text": "Detected MIME type of the uploaded file.",
            },
            "size_bytes": {
                "help_text": "File size in bytes.",
            },
            "file_type": {
                "help_text": "Normalized internal file category (e.g. image, pdf, other).",
            },
            "uploaded_by": {
                "help_text": "User who uploaded the file.",
            },
            "created_at": {
                "help_text": "Timestamp when the file was uploaded.",
            },
        }


class MediaFileUploadSerializer(serializers.ModelSerializer):
    """Write serializer for uploading a new media file."""

    file = serializers.FileField(
        write_only=True,
        help_text="Binary file upload. Supported types: JPEG, PNG, WEBP, PDF.",
    )

    class Meta:
        model = MediaFile
        fields = [
            "id",
            "external_id",
            "file",
            "original_name",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "external_id",
            "original_name",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        ]

    ALLOWED_MIME_TYPES = {
        "image/jpeg": MediaFile.FileType.IMAGE,
        "image/png": MediaFile.FileType.IMAGE,
        "image/webp": MediaFile.FileType.IMAGE,
        "application/pdf": MediaFile.FileType.PDF,
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def validate_file(self, value):
        """Validate uploaded file type and size."""
        if not value:
            raise serializers.ValidationError("No file was uploaded.")

        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(f"File is too large (max {self.MAX_FILE_SIZE // (1024 * 1024)} MB).")

        content_type = getattr(value, "content_type", None)
        if content_type not in self.ALLOWED_MIME_TYPES:
            raise serializers.ValidationError("Unsupported file type. Allowed types are JPEG, PNG, WEBP, and PDF.")

        return value

    def create(self, validated_data):
        """Populate derived metadata fields from the uploaded file."""
        uploaded_file = validated_data["file"]
        mime_type = getattr(uploaded_file, "content_type", None)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        User = get_user_model()

        uploaded_by = user if isinstance(user, User) else None

        instance = MediaFile(
            file=uploaded_file,
            original_name=uploaded_file.name,
            mime_type=mime_type or "",
            size_bytes=uploaded_file.size,
            file_type=self.ALLOWED_MIME_TYPES.get(mime_type, MediaFile.FileType.OTHER),
            uploaded_by=uploaded_by,
        )

        instance.save()
        return instance
