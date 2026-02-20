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