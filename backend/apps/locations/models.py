from django.db import models

from apps.core.model import BaseModel
from apps.languages.models import Language

# ==============================
# LOCATION
# ==============================


class Location(BaseModel):
    street = models.CharField(max_length=255, db_comment="The street of the location.")

    number = models.CharField(
        max_length=20, db_comment="The street number of the location."
    )

    postal_code = models.CharField(
        max_length=20, db_comment="The postal code of the location."
    )

    city = models.CharField(max_length=100, db_comment="City")

    country = models.CharField(max_length=100, db_comment="Country")

    phone_1 = models.CharField(
        max_length=50, blank=True, null=True, db_comment="Primary phone number"
    )

    phone_2 = models.CharField(
        max_length=50, blank=True, null=True, db_comment="Secondary phone number"
    )

    is_own_location = models.BooleanField(
        default=False, db_comment="Whether this is an owned location or not"
    )

    class Meta(BaseModel.Meta):
        db_table = "location"
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return f"{self.city} - {self.street} {self.number}"


class LocationTranslation(BaseModel):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="translations",
        db_comment="Reference to the location",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="location_translations",
        db_comment="Language of the translation",
    )

    name = models.CharField(
        max_length=255, db_comment="Translated name of the location"
    )

    class Meta(BaseModel.Meta):
        db_table = "location_translation"
        verbose_name = "Location Translation"
        verbose_name_plural = "Location Translations"
        constraints = [
            models.UniqueConstraint(
                fields=["location", "language"], name="unique_location_language"
            )
        ]

    def __str__(self):
        return f"{self.language.code} - {self.name}"


# ==============================
# SPACE
# ==============================


class Space(BaseModel):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="spaces",
        db_comment="Reference to the location of the space",
    )

    class Meta(BaseModel.Meta):
        db_table = "space"
        verbose_name = "Space"
        verbose_name_plural = "Spaces"

    def __str__(self):
        return f"Space {self.id} - {self.location}"


class SpaceTranslation(BaseModel):
    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="translations",
        db_comment="Reference to the space",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="space_translations",
        db_comment="Language of the translation",
    )

    name = models.CharField(max_length=255, db_comment="Translated name of the space")

    class Meta(BaseModel.Meta):
        db_table = "space_translation"
        verbose_name = "Space Translation"
        verbose_name_plural = "Space Translations"
        constraints = [
            models.UniqueConstraint(
                fields=["space", "language"], name="unique_space_language"
            )
        ]

    def __str__(self):
        return f"Space - {self.language.code} - {self.name}"


# ==============================
# HALL
# ==============================


class Hall(BaseModel):
    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="halls",
        db_comment="Reference to the space where the hall is located",
    )

    seat_selection = models.BooleanField(
        default=False, db_comment="Whether seat selection is available"
    )

    open_seating = models.BooleanField(
        default=False, db_comment="Whether seating is open/general admission"
    )

    class Meta(BaseModel.Meta):
        db_table = "hall"
        verbose_name = "Hall"
        verbose_name_plural = "Halls"

    def __str__(self):
        return f"Hall {self.id} @ {self.space}"


class HallTranslation(BaseModel):
    hall = models.ForeignKey(
        Hall,
        on_delete=models.CASCADE,
        related_name="translations",
        db_comment="Reference to the hall",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="hall_translations",
        db_comment="Language of the translation",
    )

    name = models.CharField(max_length=255, db_comment="Translated name of the hall")

    remark = models.TextField(
        blank=True, null=True, db_comment="Optional remark about the hall"
    )

    class Meta(BaseModel.Meta):
        db_table = "hall_translation"
        verbose_name = "Hall Translation"
        verbose_name_plural = "Hall Translations"
        constraints = [
            models.UniqueConstraint(
                fields=["hall", "language"], name="unique_hall_language"
            )
        ]

    def __str__(self):
        return f"{self.language.code} - {self.name}"
