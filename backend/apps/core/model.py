import django.db.models as models


class BaseModel(models.Model):
    """Base class for all models in the project.

    Let all models inherit from this class and implement model validation
    in `clean()`. On `save()`, `full_clean()` is executed automatically.
    """
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Always run validation before saving."""
        self.full_clean()
        super().save(*args, **kwargs)