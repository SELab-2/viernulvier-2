"""Model for Media Files."""

import mimetypes
import os
from pathlib import Path
from typing import Any
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel


def upload_to_media(instance: Any, filename: str) -> str:  # noqa: ARG001
    """Return a unique upload path for a media file."""
    ext = os.path.splitext(filename)[1]
    return f"media/uploads/{uuid.uuid4()}{ext}"


class MediaFile(BaseModel):
    """Stored uploaded media asset such as a poster, brochure, or PDF."""

    class FileType(models.TextChoices):
        IMAGE = "image", "Image"
        PDF = "pdf", "PDF"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=upload_to_media)

    original_name = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=100, blank=True, editable=False)
    size_bytes = models.PositiveBigIntegerField(blank=True, null=True, editable=False)

    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
        editable=False,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_media",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def _derive_original_name(self) -> str:
        """Prefer the client filename over the generated storage path."""
        if not self.file:
            return ""
        uploaded_name = getattr(self.file, "name", "") or ""
        return Path(uploaded_name).name

    def _derive_mime_type(self) -> str:
        """Determine MIME type from uploaded file metadata or filename."""
        if not self.file:
            return ""

        content_type = getattr(self.file, "content_type", None)
        if content_type:
            return content_type

        guessed_type, _ = mimetypes.guess_type(getattr(self.file, "name", ""))
        return guessed_type or "application/octet-stream"

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
        """Fill metadata fields derived from the uploaded file."""
        if not self.file:
            return

        file_changed = self._file_has_changed()

        if not self.original_name:
            self.original_name = self._derive_original_name()

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

        self._populate_derived_fields()

        if (self.size_bytes or 0) > self.MAX_FILE_SIZE:
            raise ValidationError({"file": f"File is too large (max {self.MAX_FILE_SIZE // (1024 * 1024)} MB)."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Populate derived fields as a defensive fallback.

        This helps when some code path skips full_clean().
        """
        if self.file:
            self._populate_derived_fields()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return the original uploaded filename."""
        return self.original_name
