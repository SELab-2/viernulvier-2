from django.db import models
from apps.core.model import BaseModel

class UitDatabaseTheme(BaseModel):
    """Model representing a theme in the UIT database."""
    name = models.CharField(
        max_length=200,
        db_comment="The name of the theme."
    )

    class Meta(BaseModel.Meta):
        db_table = "uit_database_theme"
        verbose_name = "UIT Database Theme"
        verbose_name_plural = "UIT Database Themes"

    def __str__(self):
        return self.name

class UitDatabaseType(BaseModel):
    """Model representing a type in the UIT database."""
    name = models.CharField(
        max_length=200,
        db_comment="The name of the type."
    )

    class Meta(BaseModel.Meta):
        db_table = "uit_database_type"
        verbose_name = "UIT Database Type"
        verbose_name_plural = "UIT Database Types"

    def __str__(self):
        return self.name

class Production(BaseModel):
    """Model representing a production."""

    # TODO: add more choices for attendance model if needed (look at the api responses)
    class AttendanceMode(models.TextChoices):
        """Enum representing the attendance model of a production."""
        OFFLINE = "offline", "Offline"
        ONLINE = "online", "Online"

    # TODO: add more choices for performance model if needed (look at the api responses)
    class PerformanceType(models.TextChoices):
        """Enum representing the performance model of a production."""
        GROUP = "group", "Group"
        SOLO = "solo", "Solo"

    uit_database_theme = models.ForeignKey(
        UitDatabaseTheme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_comment="The theme of the production as defined in the UIT database.",
        related_name="productions",
    )

    uit_database_type = models.ForeignKey(
        UitDatabaseType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_comment="The type of the production as defined in the UIT database.",
        related_name="productions",
    )

    attendance_mode = models.CharField(
        max_length=20,
        choices=AttendanceMode.choices,
        blank=True,
        db_comment="The attendance mode of the production."
    )

    performance_type = models.CharField(
        max_length=20,
        choices=PerformanceType.choices,
        blank=True,
        db_comment="The performance type of the production."
    )

    genres = models.ManyToManyField(
        Genre, # TODO: implement Genre model
        blank=True,
        db_comment="The genres of the production.",
        related_name="productionGenres",
    )

    tags = models.ManyToManyField(
        Tag, # TODO: implement Tag model
        blank=True,
        db_comment="The tags associated with the production.",
        related_name="productionTags",
    )

    class Meta(BaseModel.Meta):
        db_table = "production"
        verbose_name = "Production"
        verbose_name_plural = "Productions"

    def __str__(self):
        return f"Production {self.id}" # TODO: change if we know how to do translations
