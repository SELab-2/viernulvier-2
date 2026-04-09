"""Serializers for Media Files."""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
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
            "filename",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        ]
        read_only_fields = fields


class MediaFileUploadSerializer(serializers.ModelSerializer):
    """Write serializer for uploading a new media file."""

    ALLOWED_MIME_TYPES = {
        "image/jpeg": MediaFile.FileType.IMAGE,
        "image/png": MediaFile.FileType.IMAGE,
        "image/webp": MediaFile.FileType.IMAGE,
        "application/pdf": MediaFile.FileType.PDF,
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

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
            "filename",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "external_id",
            "filename",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        ]

    def validate_file(self, value: UploadedFile) -> UploadedFile:
        """Validate that the uploaded file is present, supported, and not too large."""
        if not value:
            raise serializers.ValidationError("No file was uploaded.")

        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(f"File is too large (max {self.MAX_FILE_SIZE // (1024 * 1024)} MB).")

        content_type = getattr(value, "content_type", None)
        if content_type not in self.ALLOWED_MIME_TYPES:
            raise serializers.ValidationError("Unsupported file type. Allowed types are JPEG, PNG, WEBP, and PDF.")

        return value

    def create(self, validated_data: dict[str, Any]) -> MediaFile:
        """Create a media file instance and let the model derive metadata."""
        request = self.context.get("request")
        user = getattr(request, "user", None)

        user_model = get_user_model()
        uploaded_by = user if isinstance(user, user_model) else None

        instance = MediaFile(
            file=validated_data["file"],
            uploaded_by=uploaded_by,
        )
        instance.full_clean()
        instance.save()
        return instance
