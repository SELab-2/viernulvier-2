from django.db import models
from apps.core.model import BaseModel
from apps.languages.models import Language

class MediaGallery(BaseModel):
    """Model representing a media gallery."""
    name = models.CharField(
        max_length=255,
        db_comment="Name of the media gallery.",
    )

    class Meta(BaseModel.Meta):
        db_table = "media_gallery"
        verbose_name = "Media Gallery"
        verbose_name_plural = "Media Galleries"
    
    def __str__(self):
        return self.name
    
class MediaItem(BaseModel):
    """Model representing a media item."""
    gallery = models.ForeignKey(
        MediaGallery,
        on_delete=models.CASCADE,
        related_name="media_items",
        db_comment="The media gallery this item belongs to.",
    )

    type = models.CharField(
        max_length=50,
        db_comment="Type of media item (e.g., image, video).",
    )

    format = models.CharField(
        max_length=50,
        blank=True,
        db_comment="Format of the media item (e.g., jpg, mp4).",
    )

    original_filename = models.CharField(
        max_length=255,
        blank=True,
        db_comment="Original filename of the media item.",
    )

    position = models.PositiveIntegerField(
        default=0,
        db_comment="Position of the media item within the gallery.",
    )

    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_comment="Width of the media item in pixels.",
    )

    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_comment="Height of the media item in pixels.",
    )

    class Meta(BaseModel.Meta):
        db_table = "media_item"
        verbose_name = "Media Item"
        verbose_name_plural = "Media Items"
        ordering = ['position']

    def __str__(self):
        return f"{self.type} - {self.original_filename or 'Unnamed'}"
    
class MediaItemTranslation(BaseModel):
    """Model representing a translation for a media item."""
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="translations",
        db_comment="The media item this translation belongs to.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="media_item_translations",
        db_comment="Language of the translation.",
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        db_comment="Title of the media item in the specified language.",
    )

    description = models.TextField(
        blank=True,
        db_comment="Description of the media item in the specified language.",
    )

    credits = models.CharField(
        max_length=255,
        blank=True,
        db_comment="Credits for the media item in the specified language.",
    )

    link = models.URLField(
        blank=True,
        db_comment="External link related to the media item in the specified language.",
    )

    class Meta(BaseModel.Meta):
        db_table = "media_item_translation"
        unique_together = (("media_item", "language"),)
        verbose_name = "Media Item Translation"
        verbose_name_plural = "Media Item Translations"
    
    def __str__(self):
        return f"{self.media_item} - {self.language}"
    
class MediaItemCrop(BaseModel):
    """Model representing a crop for a media item."""
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="crops",
        db_comment="The media item this crop belongs to.",
    )

    name = models.CharField(
        max_length=100,
        db_comment="Name of the crop (e.g., thumbnail, banner).",
    )

    url = models.URLField(
        db_comment="URL of the cropped media item.",
    )

    class Meta(BaseModel.Meta):
        db_table = "media_item_crop"
        unique_together = (("media_item", "name"),)
        verbose_name = "Media Item Crop"
        verbose_name_plural = "Media Item Crops"
    
    def __str__(self):
        return f"{self.media_item} - {self.name}"