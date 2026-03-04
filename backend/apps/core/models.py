"""
Base model for the core app.

``BaseModel`` is the single abstract parent for every concrete model in
the project. Inheriting from it guarantees that model-level validation
(defined in each model's ``clean()`` method) is always executed before
a record is written to the database.
"""

from django.db import models
from django.conf import settings


class BaseModel(models.Model):
    """
    Project-wide abstract base class for all models.

    Every app-level model should inherit from ``BaseModel`` instead of
    ``django.db.models.Model`` directly. This ensures ``full_clean()``
    is always called before ``save()``, so any ``ValidationError`` raised
    in a model's ``clean()`` method is surfaced consistently — whether the
    save originates from the Django admin, the API, a management command,
    or a test.

    Validation order (``full_clean``)
    ----------------------------------
    Django's ``full_clean()`` runs three steps in order:

    1. ``validate_unique()``  — checks ``unique`` and ``unique_together``
       constraints at the application level.
    2. ``clean_fields()``     — validates individual field constraints
       (e.g. ``max_length``, ``blank=False``).
    3. ``clean()``            — custom cross-field validation defined on the
       model itself.

    Subclasses should override ``clean()`` for cross-field business rules
    and rely on field-level validators for single-field constraints.

    Notes
    -----
    - ``full_clean()`` is **not** called automatically by Django's ORM on
      ``save()`` by default — this base class adds that behaviour explicitly.
    - ``CheckConstraint`` rules are enforced at the database level and are
      **not** caught by ``full_clean()``. Mirror critical constraints in
      ``clean()`` so they surface as friendly ``ValidationError`` messages
      in the admin and API (see :class:`~apps.events.models.Event` for an
      example).
    - ``update()`` on a queryset bypasses ``save()`` entirely and therefore
      also bypasses this validation. Use with care.

    Usage
    -----
    ::

        from apps.core.models import BaseModel

        class MyModel(BaseModel):
            name = models.CharField(max_length=100)

            def clean(self):
                super().clean()
                if self.name == "forbidden":
                    raise ValidationError("This name is not allowed.")
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        """
        Run full model validation before persisting to the database.

        Calls ``self.full_clean()`` prior to delegating to the standard
        ``Model.save()``. Any ``ValidationError`` raised during validation
        will propagate to the caller.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def base_language_code(cls) -> str:
        """
        Returns the project's base language code.
        """
        code = getattr(settings, "LANGUAGE_CODE", "en")
        return code.split("-")[0].lower()

    def get_base_translation(self, related_name="translations"):
        """
        Returns the translation object for the base language,
        falling back to the first available translation.
        """
        manager = getattr(self, related_name, None)
        if not manager:
            return None

        base_code = self.base_language_code()
        qs = manager.all()
        return qs.filter(language__code=base_code).first() or qs.first()

    def get_base_display_name(
        self,
        related_name="translations",
        name_field="name",
        fallback=None,
    ):
        tr = self.get_base_translation(related_name=related_name)
        if not tr:
            return fallback
        return getattr(tr, name_field, None) or fallback