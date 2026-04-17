"""Serializers for Media Files."""

from typing import Any

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

    class Meta:
        model = MediaFile
        fields = [
            "id",
            "external_id",
            "file",
            "filename",
            "description",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
        ]
        read_only_fields = fields


class MediaFileUploadSerializer(serializers.ModelSerializer):
    """Write serializer for uploading or updating a media file."""

    ALLOWED_MIME_TYPES = ALLOWED_MEDIA_MIME_TYPES
    MAX_FILE_SIZE = MAX_MEDIA_FILE_SIZE_BYTES

    file = serializers.FileField(
        write_only=True,
        required=False,
        help_text=(
            "Binary file upload. Supported types: JPEG, PNG, WEBP, PDF. "
            "Validation: max 10 MB, binary signature verification (PDF %25PDF- header, image Pillow verify), "
            "content-type vs declared MIME mismatch detection, extension-MIME consistency check."
        ),
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=MediaFile._meta.get_field("description").max_length,
        help_text="Optional contextual note about the content of the media file.",
    )

    class Meta:
        model = MediaFile
        fields = [
            "id",
            "external_id",
            "file",
            "filename",
            "description",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "filename",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Require a file on create, but allow metadata-only updates."""
        if self.instance is None and "file" not in attrs:
            raise serializers.ValidationError({"file": "This field is required."})
        return attrs

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
        instance = MediaFile(
            file=validated_data["file"],
            external_id=validated_data.get("external_id"),
            description=validated_data.get("description", ""),
        )
        instance.full_clean()
        instance.save()
        return instance

    def update(self, instance: MediaFile, validated_data: dict[str, Any]) -> MediaFile:
        """Update file and editable metadata on an existing media file."""
        for field in ("external_id", "description"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        if "file" in validated_data:
            instance.file = validated_data["file"]

        instance.full_clean()
        instance.save()
        return instance
