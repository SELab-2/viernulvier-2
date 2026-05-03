"""Models for the Tags app.

Tags are classification labels that can be attached to productions:

    Tag  ->  TagTranslation

- A **Tag** defines a label with optional source metadata (useful for tags
  imported from external systems such as UiTdatabank).
- A **TagTranslation** carries the localised name, excerpt, short description,
  and URL title for a specific language.
"""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import models

from apps.core.media_validation import (
    ALLOWED_IMAGE_MIME_TYPES,
    MAX_MEDIA_FILE_SIZE_BYTES,
    validate_media_file,
)
from apps.core.models import BaseModel
from apps.languages.models import Language


class Tag(BaseModel):
    """A classification label that can be attached to one or more productions.

    Tags support both internally created labels and labels imported from
    external systems (e.g. UiTdatabank). The ``source`` field records
    the origin of the tag.

    Attributes:
        url:         Public URL of the tag in the originating system.
        source:      Identifier of the system that created this tag
                     (e.g. ``uitdatabank``, ``system``).
        is_enabled:  ``False`` to soft-disable the tag without removing it.
        type:        Internal category used for grouping
                     (e.g. ``theme``, ``audience``).
    """

    url = models.URLField(
        blank=True,
        help_text="Public URL of the tag in the originating system. Empty string when not applicable.",
        db_comment="The URL of the tag, if it exists.",
    )

    source = models.CharField(
        max_length=255,
        blank=True,
        help_text="Identifier of the system that created this tag (e.g. `uitdatabank`, `system`).",
        db_comment="Source of the tag (e.g. system, external API).",
    )

    is_enabled = models.BooleanField(
        default=True,
        help_text="`false` to soft-disable the tag without deleting it.",
        db_comment="Whether the tag is enabled.",
    )

    type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Internal category of the tag used for grouping (e.g. `theme`, `audience`).",
        db_comment="Type/category of the tag.",
    )

    image = models.ImageField(
        upload_to="tag_images/",
        null=True,
        blank=True,
        help_text="Upload an image for this tag.",
        db_comment="Optional image for the tag.",
    )

    def clean(self) -> None:
        """Validate uploaded image files."""
        super().clean()
        uploaded_image = getattr(self.image, "_file", None)
        if isinstance(uploaded_image, UploadedFile):
            try:
                validate_media_file(
                    uploaded_image,
                    allowed_mime_types=ALLOWED_IMAGE_MIME_TYPES,
                    max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
                )
            except ValueError as exc:
                raise ValidationError({"image": str(exc)}) from exc

    class Meta(BaseModel.Meta):
        db_table = "tag"
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["id"]

    def __str__(self) -> str:
        """String representation of a Tag is its name in the default language, or a fallback."""
        name = self.get_base_display_name(
            related_name="translations",
            name_field="name",
            fallback=None,
        )

        return name or f"Tag {self.id}"


class TagTranslation(BaseModel):
    """Localised text fields for a Tag.

    Each tag can have at most one translation per language. The ``name``
    field is the primary display label; ``excerpt``, ``short_description``
    and ``url_title`` are optional supplementary fields.

    Attributes:
        tag:               The tag this translation belongs to.
        language:          The language of this translation.
        name:              Localised display name of the tag.
        excerpt:          Optional excerpt or summary of the tag.
        short_description: Optional short description of the tag.
        url_title:         URL-safe title used in slugs or links.
    """

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Tag this translation belongs to.",
        db_comment="The tag that this translation belongs to.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="tag_translations",
        help_text="Language of this translation.",
        db_comment="The language of the translation.",
    )

    name = models.CharField(
        max_length=255,
        help_text="Localised display name of the tag (e.g. `Contemporary`, `Family friendly`).",
        db_comment="The name of the tag in the specified language.",
    )


    excerpt = models.TextField(
        blank=True,
        null=True,
        help_text="Optional short excerpt or summary of the tag in this language.",
        db_comment="Translated excerpt.",
    )

    short_description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional short description of the tag in this language.",
        db_comment="Short description of the tag.",
    )

    url_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="URL-safe title of the tag in this language (e.g. `contemporary`, `family-friendly`).",
        db_comment="URL title in the specified language.",
    )

    class Meta(BaseModel.Meta):
        db_table = "tag_translation"
        verbose_name = "Tag Translation"
        verbose_name_plural = "Tag Translations"
        ordering = ["language__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["tag", "language"],
                name="unique_tag_language",
            )
        ]
        indexes = [
            models.Index(fields=["tag", "language"], name="idx_tag_lang"),
        ]

    def __str__(self) -> str:
        """String representation of a TagTranslation includes the language code and name."""
        return f"{self.language.code} - {self.name}"
