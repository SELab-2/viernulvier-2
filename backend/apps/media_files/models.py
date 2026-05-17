"""Models for uploaded media files.

The Media Files app stores user-uploaded images and PDFs, derives metadata
such as MIME type, size, filename and normalized file type, and keeps
localised descriptions in MediaFileTranslation.
"""

import os
from typing import Any
import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.media_validation import (
    ALLOWED_MEDIA_MIME_TYPES,
    MAX_MEDIA_FILE_SIZE_BYTES,
    detect_best_mime_type,
    extract_safe_filename,
    validate_media_file,
)
from apps.core.models import BaseModel
from apps.languages.models import Language

DESCRIPTION_MAX_LENGTH = 200


def upload_to_media(instance: Any, filename: str) -> str:  # noqa: ARG001
    """Return a unique upload path for a media file."""
    ext = os.path.splitext(filename)[1]
    return f"uploads/{uuid.uuid4()}{ext}"


class MediaFile(BaseModel):
    """Stored uploaded media asset such as a poster, brochure, or PDF.

    Localised descriptions are stored in :class:`MediaFileTranslation`.
    """

    class FileType(models.TextChoices):
        IMAGE = "image", "Image"
        PDF = "pdf", "PDF"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=upload_to_media)

    filename = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=100, blank=True, editable=False)
    size_bytes = models.PositiveBigIntegerField(blank=True, null=True, editable=False)

    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
        editable=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    MAX_FILE_SIZE = MAX_MEDIA_FILE_SIZE_BYTES

    class Meta(BaseModel.Meta):
        db_table = "media_file"
        verbose_name = "Media File"
        verbose_name_plural = "Media Files"
        ordering = ["-created_at"]

    def _derive_filename(self) -> str:
        """Prefer the client filename over the generated storage path."""
        if not self.file:
            return ""
        uploaded_name = getattr(self.file, "name", "") or ""
        return extract_safe_filename(uploaded_name)

    def _derive_mime_type(self) -> str:
        """Determine MIME type from uploaded file metadata or filename."""
        if not self.file:
            return ""

        return detect_best_mime_type(self.file)

    def _derive_size_bytes(self) -> int:
        """Read size from uploaded file object."""
        if not self.file:
            return 0

        size = getattr(self.file, "size", None)
        return int(size or 0)

    def _derive_file_type(self, mime_type: str) -> str:
        """Normalize internal file type from MIME type."""
        if mime_type.startswith("image/"):
            return self.FileType.IMAGE
        if mime_type == "application/pdf":
            return self.FileType.PDF
        return self.FileType.OTHER

    def _file_has_changed(self) -> bool:
        """Return whether the stored file was replaced on an existing object."""
        if self._state.adding or not self.pk:
            return False

        try:
            previous = type(self).objects.only("file").get(pk=self.pk)
        except type(self).DoesNotExist:
            return False

        previous_name = getattr(previous.file, "name", "") or ""
        current_name = getattr(self.file, "name", "") or ""
        return previous_name != current_name

    def _populate_derived_fields(self) -> None:
        """Fill metadata fields derived from the uploaded file.

        The filename is only replaced automatically when it was empty, or when the
        binary file changed and the current filename still matches the previous
        stored filename. This preserves manually edited filenames across metadata
        updates.
        """
        if not self.file:
            return

        file_changed = self._file_has_changed()

        previous_filename = None
        if not self._state.adding and self.pk:
            try:
                previous = type(self).objects.only("filename").get(pk=self.pk)
                previous_filename = previous.filename
            except type(self).DoesNotExist:
                previous_filename = None

        derived_filename = self._derive_filename()

        if not self.filename or (file_changed and self.filename == (previous_filename or "")):
            self.filename = derived_filename

        if file_changed or not self.mime_type:
            self.mime_type = self._derive_mime_type()

        if file_changed or self.size_bytes is None:
            self.size_bytes = self._derive_size_bytes()

        self.file_type = self._derive_file_type(self.mime_type or "")

    def clean(self) -> None:
        """Populate derived fields before validation.

        This makes admin, serializers, and any other save path behave the same.
        """
        super().clean()

        if not self.file:
            raise ValidationError({"file": "This field is required."})

        try:
            # Validation performs binary signature/MIME/size checks and returns trusted metadata.
            validation = validate_media_file(
                self.file,
                allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
                max_file_size=self.MAX_FILE_SIZE,
            )
            self.mime_type = validation.mime_type
            self.size_bytes = validation.size_bytes
        except ValueError as exc:
            raise ValidationError({"file": str(exc)}) from exc

        self._populate_derived_fields()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Ensure derived fields are populated before saving."""
        if self.file:
            self._populate_derived_fields()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return the original uploaded filename."""
        return self.filename


class MediaFileTranslation(BaseModel):
    """Localised description for a MediaFile.

    Each media file can have at most one description per language.
    """

    media_file = models.ForeignKey(
        MediaFile,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Media file this translation belongs to.",
        db_comment="The media file that this translation belongs to.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="media_file_translations",
        help_text="Language of this translation.",
        db_comment="The language of the translation.",
    )

    description = models.CharField(
        max_length=DESCRIPTION_MAX_LENGTH,
        blank=True,
        help_text="Localised description of the media file.",
        db_comment="Description of the media file in the specified language.",
    )

    class Meta(BaseModel.Meta):
        db_table = "media_file_translation"
        verbose_name = "Media File Translation"
        verbose_name_plural = "Media File Translations"
        ordering = ["language__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["media_file", "language"],
                name="unique_media_file_language",
            )
        ]
        indexes = [
            models.Index(fields=["media_file", "language"], name="idx_media_file_lang"),
        ]

    def __str__(self) -> str:
        """String representation includes the language code and file name."""
        return f"{self.language.code} - {self.media_file.filename}"
