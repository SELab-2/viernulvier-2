"""Serializers for Media Files."""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers

from apps.core.media_validation import (
    ALLOWED_MEDIA_MIME_TYPES,
    MAX_MEDIA_FILE_SIZE_BYTES,
    validate_media_file,
)

from .models import MediaFile


class MediaFileSerializer(serializers.ModelSerializer):
    """Read serializer for media files."""

    uploaded_by = serializers.CharField(source="uploaded_by.username", read_only=True, allow_null=True)

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

    ALLOWED_MIME_TYPES = ALLOWED_MEDIA_MIME_TYPES
    MAX_FILE_SIZE = MAX_MEDIA_FILE_SIZE_BYTES

    file = serializers.FileField(
        write_only=True,
        help_text=(
            "Binary file upload. Supported types: JPEG, PNG, WEBP, PDF. "
            "Validation: max 10 MB, binary signature verification (PDF %25PDF- header, image Pillow verify), "
            "content-type vs declared MIME mismatch detection, extension-MIME consistency check."
        ),
    )
    uploaded_by = serializers.CharField(source="uploaded_by.username", read_only=True, allow_null=True)

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
        try:
            validate_media_file(
                value,
                allowed_mime_types=self.ALLOWED_MIME_TYPES,
                max_file_size=self.MAX_FILE_SIZE,
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

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
