"""
Models for the Media app.

The media hierarchy is two levels deep:

    MediaGallery  ->  MediaItem  ->  MediaItemTranslation
                                ->  MediaItemCrop

- A **MediaGallery** is a named collection of media items.
- A **MediaItem** is a single image, video, or audio file within a gallery.
- A **MediaItemTranslation** stores localised metadata (title, description,
  credits, link) for a media item.
- A **MediaItemCrop** stores a named, pre-rendered crop (e.g. thumbnail,
  banner) of a media item together with its URL.
"""

from django.db import models

from apps.core.models import BaseModel
from apps.languages.models import Language


class MediaGallery(BaseModel):
    """
    A named collection of media items.

    Galleries group related MediaItem objects and are typically attached
    to a production, location, or other entity in the archive.

    Attributes:
        name: Human-readable name of the gallery.
    """

    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Human-readable name of the gallery.",
        db_comment="Name of the media gallery.",
    )

    items = models.ManyToManyField(
        "MediaItem",
        through="MediaGalleryItem",
        related_name="galleries",
        blank=True,
        help_text="Media items linked to this gallery through MediaGalleryItem.",
    )

    class Meta(BaseModel.Meta):
        db_table = "media_gallery"
        verbose_name = "Media Gallery"
        verbose_name_plural = "Media Galleries"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name if self.name else "Unnamed Gallery"


class MediaItem(BaseModel):
    """
    A single media asset within a MediaGallery.

    Supports images, videos, and audio files. Dimensional metadata
    (``width``, ``height``) applies to visual media only.

    Attributes:
        gallery:           The parent gallery this item belongs to.
        type:              Media type - one of ``foto``, ``video``, ``audio``, ``other``.
        format:            File format / extension (e.g. ``jpg``, ``mp4``).
        original_filename: Original filename as uploaded.
        position:          Display order within the gallery (ascending).
        width:             Width in pixels (images and videos only).
        height:            Height in pixels (images and videos only).
    """

    class MediaItemType(models.TextChoices):
        IMAGE = "foto", "Foto"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        OTHER = "other", "Other"

    gallery = models.ForeignKey(
        MediaGallery,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="media_items",
        help_text="Parent gallery this item belongs to.",
        db_comment="FK to MediaGallery.",
    )

    type = models.CharField(
        max_length=20,
        choices=MediaItemType.choices,
        null=False,
        blank=False,
        help_text="Media type: `foto`, `video`, `audio`, or `other`.",
        db_comment="Type of media item.",
    )

    format = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="File format / extension (e.g. `jpg`, `mp4`, `mp3`).",
        db_comment="Format / extension of the media item.",
    )

    original_filename = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Original filename as uploaded.",
        db_comment="Original filename of the media item.",
    )

    position = models.PositiveIntegerField(
        default=0,
        help_text="Display order within the gallery. Lower values appear first.",
        db_comment="Position of the media item within the gallery.",
    )

    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Width in pixels. Applies to images and videos only.",
        db_comment="Width of the media item in pixels.",
    )

    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Height in pixels. Applies to images and videos only.",
        db_comment="Height of the media item in pixels.",
    )

    class Meta(BaseModel.Meta):
        db_table = "media_item"
        verbose_name = "Media Item"
        verbose_name_plural = "Media Items"
        ordering = ["position"]

    def __str__(self) -> str:
        return f"{self.type} - {self.original_filename or 'Unnamed'}"


class MediaGalleryItem(models.Model):
    """Explicit gallery-item link table with stable ordering within a gallery."""

    gallery = models.ForeignKey(
        MediaGallery,
        on_delete=models.CASCADE,
        related_name="media_gallery_items",
        help_text="Gallery this media item is linked to.",
        db_comment="FK to MediaGallery.",
    )

    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="media_gallery_links",
        help_text="Media item linked to the gallery.",
        db_comment="FK to MediaItem.",
    )

    position = models.PositiveIntegerField(
        default=0,
        help_text="Display order of the media item within the gallery.",
        db_comment="Position of the media item within the gallery.",
    )

    class Meta:
        db_table = "media_gallery_item"
        verbose_name = "Media Gallery Item"
        verbose_name_plural = "Media Gallery Items"
        ordering = ["gallery_id", "position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["gallery", "media_item"],
                name="unique_media_item_per_gallery",
            )
        ]

    def __str__(self) -> str:
        return f"{self.gallery_id}:{self.media_item_id}@{self.position}"


class MediaItemTranslation(BaseModel):
    """
    Localised metadata for a MediaItem.

    Each media item can have at most one translation per language.
    All translated fields are optional.

    Attributes:
        media_item:  The media item this translation belongs to.
        language:    The language of this translation.
        title:       Localised display title.
        description: Localised extended description.
        credits:     Localised attribution / credits string.
        link:        Localised external URL related to the item.
    """

    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Media item this translation belongs to.",
        db_comment="FK to MediaItem.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="media_item_translations",
        help_text="Language of this translation.",
        db_comment="FK to Language.",
    )

    title = models.CharField(
        max_length=2000,
        blank=True,
        default="",
        help_text="Localised display title of the media item.",
        db_comment="Translated title of the media item.",
    )

    description = models.TextField(
        blank=True,
        default="",
        help_text="Localised extended description of the media item.",
        db_comment="Translated description of the media item.",
    )

    credits = models.CharField(
        max_length=300,
        blank=True,
        default="",
        help_text="Localised attribution or credits for the media item.",
        db_comment="Translated credits for the media item.",
    )

    link = models.CharField(
        max_length=255,
        blank=True,
        help_text="Localised external URL related to the media item.",
        db_comment="Translated external link for the media item.",
    )

    class Meta(BaseModel.Meta):
        db_table = "media_item_translation"
        verbose_name = "Media Item Translation"
        verbose_name_plural = "Media Item Translations"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["media_item", "language"],
                name="unique_media_language",
            )
        ]

    def __str__(self) -> str:
        return f"{self.media_item} - {self.language}"


class MediaItemCrop(BaseModel):
    """
    A named, pre-rendered crop of a MediaItem, stored as a local image file.

    Crops are downloaded from the Viernulvier CDN and saved locally via
    Django's ImageField. Only a curated set of crop variants is stored
    (currently ``hd_ready`` and ``FE3_header``).

    Each media item can have at most one crop per name.

    Attributes:
        media_item: The media item this crop belongs to.
        name:       Identifier for the crop variant (e.g. ``hd_ready``).
        image:      Locally stored image file downloaded from the CDN.
    """

    # Crop variants that are fetched and stored during sync.
    SYNCED_CROP_NAMES = {"hd_ready", "FE3_header"}

    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="crops",
        help_text="Media item this crop belongs to.",
        db_comment="FK to MediaItem.",
    )

    name = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="Crop variant identifier (e.g. `hd_ready`, `FE3_header`).",
        db_comment="Name / variant of the crop.",
    )

    image = models.ImageField(
        upload_to="media_crops/",
        null=False,
        blank=False,
        help_text="Downloaded crop image stored locally.",
        db_comment="Local path to the downloaded crop image.",
    )

    class Meta(BaseModel.Meta):
        db_table = "media_item_crop"
        verbose_name = "Media Item Crop"
        verbose_name_plural = "Media Item Crops"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["media_item", "name"],
                name="unique_crop_name_per_media_item",
            )
        ]

    def __str__(self) -> str:
        return f"{self.media_item} - {self.name}"
