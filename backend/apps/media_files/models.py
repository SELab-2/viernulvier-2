"""Models for the Media Files app."""

import os
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


def upload_to_media(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f"media/uploads/{uuid.uuid4()}{ext}"


class MediaFile(BaseModel):
    class FileType(models.TextChoices):
        IMAGE = "image", "Image"
        PDF = "pdf", "PDF"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    file = models.FileField(upload_to=upload_to_media)

    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.PositiveBigIntegerField()

    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_media",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()

        if self.mime_type.startswith("image/"):
            self.file_type = self.FileType.IMAGE
        elif self.mime_type == "application/pdf":
            self.file_type = self.FileType.PDF
        else:
            self.file_type = self.FileType.OTHER

    def __str__(self):
        return self.original_name
