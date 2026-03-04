"""
Definition of the models related to tags.
"""

from django.db import models

from apps.core.model import BaseModel
from apps.languages.models import Language


class Tag(BaseModel):
    """
    Model for defining tags, which can be used to group productions together.
    """

    url = models.URLField(
        blank=True,
        db_comment="The URL of the tag, if it exists."
    )

    source = models.CharField(
        max_length=255,
        blank=True,
        db_comment="Source of the tag (e.g. system, external API)"
    )

    source_type = models.CharField(
        max_length=100,
        blank=True,
        db_comment="Type of the source"
    )

    is_external = models.BooleanField(
        default=False,
        db_comment="Whether this tag originates from an external system"
    )

    is_enabled = models.BooleanField(
        default=True,
        db_comment="Whether the tag is enabled"
    )

    type = models.CharField(
        max_length=100,
        blank=True,
        db_comment="Type/category of the tag"
    )

    class Meta(BaseModel.Meta):
        db_table = "tag"
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return f"Tag of type ({self.type})"

class TagTranslation(BaseModel):
    """
    Model for defining translations for tags.
    """

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="translations",
        db_comment="The tag that this translation belongs to."
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="tag_translations",
        db_comment="The language of the translation."
    )

    name = models.CharField(
        max_length=255,
        db_comment="The name of the tag in the specified language."
    )

    short_description = models.TextField(
        blank=True,
        null=True,
        db_comment="Short description of the tag"
    )
    
    url_title = models.CharField(
        max_length=255,
        blank=True,
        db_comment="URL title in the specified language"
    )

    class Meta(BaseModel.Meta):
        db_table = "tag_translation"
        verbose_name = "Tag Translation"
        verbose_name_plural = "Tag Translations"
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'language'], name='unique_tag_language'
            )
        ]
    
    def __str__(self):
        return f"{self.language.code} - {self.name}"
