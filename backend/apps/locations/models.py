"""Models for the Locations app.

The location hierarchy is three levels deep:

    Location  ->  Space  ->  Hall

- A **Location** is a physical address (building / venue).
- A **Space** is a distinct area within a location (e.g. a wing or building).
- A **Hall** is a specific room or auditorium within a space.

Every model has a companion ``*Translation`` model that stores localised
display names (and, for halls, an optional localised remark).
"""

from django.db import models

from apps.core.models import BaseModel
from apps.languages.models import Language


class Location(BaseModel):
    """A physical venue or address.

    Attributes:
        street:          Street name.
        number:          Street / house number.
        postal_code:     Postal / ZIP code.
        city:            City name.
        country:         Country name.
        phone_1:         Primary contact phone number (optional).
        phone_2:         Secondary contact phone number (optional).
        is_own_location: ``True`` when this venue is owned by the organisation.
    """

    street = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Street name of the location.",
        db_comment="Street name of the location.",
    )

    number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Street / house number.",
        db_comment="Street number of the location.",
    )

    postal_code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Postal or ZIP code.",
        db_comment="Postal code of the location.",
    )

    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="City in which the location sits.",
        db_comment="City of the location.",
    )

    country = models.CharField(
        max_length=100,
        default="BE",
        help_text="Country in which the location sits.",
        db_comment="Country of the location.",
    )

    phone_1 = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Primary contact phone number (optional).",
        db_comment="Primary phone number.",
    )

    phone_2 = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Secondary contact phone number (optional).",
        db_comment="Secondary phone number.",
    )

    is_own_location = models.BooleanField(
        default=False,
        help_text="``True`` when this venue is owned or operated by the organisation.",
        db_comment="Whether this is an owned/operated location.",
    )

    class Meta(BaseModel.Meta):
        db_table = "location"
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ["id"]

    def __str__(self) -> str:
        """Return a human-readable representation of the location."""
        name = self.get_base_display_name(related_name="translations", fallback=None)

        street_part = " ".join(filter(None, [self.street, self.number]))
        city_part = " ".join(filter(None, [self.postal_code, self.city]))

        parts = [p for p in [street_part, city_part] if p]
        address = ", ".join(parts) if parts else "/"

        return f"{name} - {address}" if name else address


class LocationTranslation(BaseModel):
    """Localised name for a Location.

    Each location can have at most one translation per language.

    Attributes:
        location: The location this translation belongs to.
        language: The language of this translation.
        name:     Localised display name of the location.
    """

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Location this translation belongs to.",
        db_comment="FK to Location.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="location_translations",
        help_text="Language of this translation.",
        db_comment="FK to Language.",
    )

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="Localised display name of the location.",
        db_comment="Translated name of the location.",
    )

    class Meta(BaseModel.Meta):
        db_table = "location_translation"
        verbose_name = "Location Translation"
        verbose_name_plural = "Location Translations"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["location", "language"],
                name="unique_location_language",
            )
        ]

    def __str__(self) -> str:
        """Return a human-readable representation of the location translation."""
        return f"{self.language.code} - {self.name}"


class Space(BaseModel):
    """A distinct physical area within a Location.

    A space groups one or more halls and represents a building, wing,
    or other named section of a venue.

    Attributes:
        location: The parent location this space belongs to.
    """

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="spaces",
        help_text="Parent location this space belongs to.",
        db_comment="FK to Location.",
    )

    class Meta(BaseModel.Meta):
        db_table = "space"
        verbose_name = "Space"
        verbose_name_plural = "Spaces"
        ordering = ["id"]

    def __str__(self) -> str:
        """Return a human-readable representation of the space."""
        name = self.get_base_display_name(related_name="translations", fallback=f"Space {self.id}")
        try:
            city = self.location.city or ""
            return f"{name} ({city})" if city else name
        except Exception:
            return name


class SpaceTranslation(BaseModel):
    """Localised name for a Space.

    Each space can have at most one translation per language.

    Attributes:
        space:    The space this translation belongs to.
        language: The language of this translation.
        name:     Localised display name of the space.
    """

    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Space this translation belongs to.",
        db_comment="FK to Space.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="space_translations",
        help_text="Language of this translation.",
        db_comment="FK to Language.",
    )

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="Localised display name of the space.",
        db_comment="Translated name of the space.",
    )

    class Meta(BaseModel.Meta):
        db_table = "space_translation"
        verbose_name = "Space Translation"
        verbose_name_plural = "Space Translations"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["space", "language"],
                name="unique_space_language",
            )
        ]

    def __str__(self) -> str:
        """Return a human-readable representation of the space translation."""
        return f"{self.language.code} - {self.name}"


class Hall(BaseModel):
    """A specific room or auditorium within a Space.

    Carries seating configuration flags that determine how tickets are
    sold and seats are assigned for events held in this hall.

    Attributes:
        space:          The parent space this hall belongs to.
        seat_selection: ``True`` when visitors can choose a specific seat.
        open_seating:   ``True`` when seating is general-admission (no fixed seat).
    """

    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="halls",
        help_text="Parent space this hall belongs to.",
        db_comment="FK to Space.",
    )

    seat_selection = models.BooleanField(
        default=False,
        help_text="``True`` when visitors can choose a specific seat during purchase.",
        db_comment="Whether seat selection is available.",
    )

    open_seating = models.BooleanField(
        default=False,
        help_text="``True`` when seating is general-admission (no fixed seat assignment).",
        db_comment="Whether seating is open / general admission.",
    )

    class Meta(BaseModel.Meta):
        db_table = "hall"
        verbose_name = "Hall"
        verbose_name_plural = "Halls"
        ordering = ["id"]

    def __str__(self) -> str:
        """Return a human-readable representation of the hall."""
        name = self.get_base_display_name(related_name="translations", fallback=f"Hall {self.id}")
        try:
            city = self.space.location.city or ""
            return f"{name} ({city})" if city else name
        except Exception:
            return name


class HallTranslation(BaseModel):
    """Localised name and optional remark for a Hall.

    Each hall can have at most one translation per language.

    Attributes:
        hall:     The hall this translation belongs to.
        language: The language of this translation.
        name:     Localised display name of the hall.
        remark:   Optional localised note about the hall (e.g. accessibility info).
    """

    hall = models.ForeignKey(
        Hall,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Hall this translation belongs to.",
        db_comment="FK to Hall.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="hall_translations",
        help_text="Language of this translation.",
        db_comment="FK to Language.",
    )

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="Localised display name of the hall.",
        db_comment="Translated name of the hall.",
    )

    remark = models.TextField(
        blank=True,
        null=True,
        help_text="Optional localised note about the hall (e.g. accessibility information).",
        db_comment="Optional translated remark about the hall.",
    )

    class Meta(BaseModel.Meta):
        db_table = "hall_translation"
        verbose_name = "Hall Translation"
        verbose_name_plural = "Hall Translations"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["hall", "language"],
                name="unique_hall_language",
            )
        ]

    def __str__(self) -> str:
        """Return a human-readable representation of the hall translation."""
        return f"{self.language.code} - {self.name}"
