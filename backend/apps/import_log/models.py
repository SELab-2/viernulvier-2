from django.db import models
from apps.core.model import BaseModel
from django.db.models import Q, F

# Create your models here.
class ImportLog(BaseModel):
    """
    Model for logging import operations. This is useful for debugging if something goes wrong.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending', 'pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress', 'in progress'
        PARTIAL_SUCCESS = 'PARTIAL_SUCCESS', 'Partial Success', 'partial success'
        SUCCESS = 'SUCCESS', 'Success', 'success'
        FAILED = 'FAILED', 'Failed', 'failed'
    
    source = models.CharField(
        max_length=255,
        help_text="The source of the import, e.g., file name or URL."
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_comment="Current status of the import process"
    )

    records_total = models.PositiveIntegerField(
        default=0,
        db_comment="Total number of records processed"
    )

    records_imported = models.PositiveIntegerField(
        default=0,
        db_comment="Number of successfully imported records"
    )

    records_failed = models.PositiveIntegerField(
        default=0,
        db_comment="Number of failed records"
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment="Timestamp when the import started"
    )

    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment="Timestamp when the import finished"
    )

    error_message = models.TextField(
        null=True,
        blank=True,
        db_comment="Error message if the import failed"
    )

    class Meta(BaseModel.Meta):
        db_table = "import_log"
        verbose_name = "Import Log"
        verbose_name_plural = "Import Logs"
        ordering = ["-started_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(started_at__isnull=True) |
                    Q(finished_at__isnull=True) |
                    Q(finished_at__gt=F("started_at")) # If both timestamps are set, finished_at must be after started_at
                ),
                name="importlog_finished_after_started",
            )
        ]

    def __str__(self):
        return f"{self.source} - {self.status}"
