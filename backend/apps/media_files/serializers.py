"""Serializers for Media Files."""

from typing import Any

from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers

from apps.core.media_validation import (
    ALLOWED_MEDIA_MIME_TYPES,
    MAX_MEDIA_FILE_SIZE_BYTES,
    validate_media_file,
)
from apps.core.serializers import TranslatableSerializerMixin

from .models import MediaFile


class MediaFileSerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
    """Read serializer for media files.

    The ``description`` field returns all available translations as a
    language-code dictionary.
    """

    description = serializers.SerializerMethodField(
        help_text=(
            "Dictionary of all available description translations for the media file "
            '(e.g. {"nl": "Nederlandse brochure", "en": "English brochure"}). '
            "Read-only - use the translation endpoints or admin to manage translations."
        ),
    )

    display_description = serializers.SerializerMethodField(
        help_text=(
            "Description in the project's base language (derived from settings.LANGUAGE_CODE). "
            "Falls back to the first available translation when missing."
        ),
    )

    class Meta:
        model = MediaFile
        fields = [
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
        ]
        read_only_fields = fields

    def get_description(self, obj: MediaFile) -> dict[str, str]:
        """Return all available translations as a language-code dictionary."""
        return self.get_translated_field(obj, "description")

    def get_display_description(self, obj: MediaFile) -> str | None:
        """Return the base-language description (with fallback)."""
        return self.get_base_translated_value(obj, field_name="description")


class MediaFileUploadSerializer(serializers.ModelSerializer):
    """Write serializer for uploading or updating a media file."""

    ALLOWED_MIME_TYPES = ALLOWED_MEDIA_MIME_TYPES
    MAX_FILE_SIZE = MAX_MEDIA_FILE_SIZE_BYTES

    file = serializers.FileField(
        write_only=True,
        required=False,
        help_text=(
            "Binary file upload. Supported types: JPEG, PNG, WebP, PDF. "
            "Validation: max 10 MB, binary signature verification (PDF %25PDF- header, image Pillow verify), "
            "content-type vs declared MIME mismatch detection, extension-MIME consistency check."
        ),
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
        extra_kwargs = {
            "external_id": {
                "help_text": "Optional external identifier for linking this media file to another system.",
                "required": False,
                "allow_null": True,
            },
        }

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
        )
        instance.full_clean()
        instance.save()
        return instance

    def update(self, instance: MediaFile, validated_data: dict[str, Any]) -> MediaFile:
        """Update file and editable metadata on an existing media file."""
        if "external_id" in validated_data:
            instance.external_id = validated_data["external_id"]

        if "file" in validated_data:
            instance.file = validated_data["file"]

        instance.full_clean()
        instance.save()
        return instance
