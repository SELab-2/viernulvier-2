from django.db import models
from apps.core.model import BaseModel

# Create your models here.
class Language(BaseModel):

    code = models.CharField(
        primary_key=True, 
        max_length=2, 
        db_comment="The ISO 639-1 code of the language ex. en, nl, etc."
    )
    
    name = models.CharField(
        max_length=15, 
        null=False, 
        blank=False, 
        db_comment="The name of the language ex. English, Dutch, etc."
    )
    
    is_active = models.BooleanField(
        default=False,
        db_comment="Wether the language should be shown in the frontend or not. Useful for when a language is still being implemented."
    )

    class Meta(BaseModel.Meta):
        db_table = "language"
        verbose_name = "Language"
        verbose_name_plural = "Languages"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"
