"""
Models for the Language app.

A Language represents a locale supported by the platform.
Each language has an ISO 639-1 code, a human-readable name, and an
active flag that controls whether the language is surfaced in
consumer-facing interfaces.
"""

from django.db import models

from apps.core.models import BaseModel


class Language(BaseModel):
    """
    A locale supported by the platform.

    Used as a FK target by every translation table in the system
    (GenreTranslation, LocationTranslation, SpaceTranslation, …).
    Deleting a language will cascade to all of those tables.

    Attributes:
        code:      ISO 639-1 two-letter identifier (primary key).
        name:      Human-readable English name of the language.
        is_active: When ``False`` the language is hidden from consumers
                   while translations are still being prepared.
    """

    code = models.CharField(
        primary_key=True,
        max_length=2,
        help_text="ISO 639-1 two-letter code (e.g. `en`, `nl`, `fr`).",
        db_comment="ISO 639-1 code — primary key.",
    )

    name = models.CharField(
        max_length=15,
        null=False,
        blank=False,
        help_text="Human-readable English name of the language (e.g. `English`, `Dutch`).",
        db_comment="Display name of the language.",
    )

    is_active = models.BooleanField(
        default=False,
        help_text=(
            "Controls whether this language is visible in consumer-facing interfaces. "
            "Set to `false` while translations are still being prepared."
        ),
        db_comment="Whether the language is publicly active.",
    )

    class Meta(BaseModel.Meta):
        db_table = "language"
        verbose_name = "Language"
        verbose_name_plural = "Languages"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
