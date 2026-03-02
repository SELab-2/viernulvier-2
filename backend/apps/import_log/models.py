"""
Models for the Imports app.

The imports app provides a lightweight audit trail for the data ingestion
pipeline:

    ImportLog

- An **ImportLog** is created by the import pipeline at the start of each
  run and updated as records are processed. It is never created or mutated
  via the API or the Django admin — both surfaces are intentionally
  read-only.

A database-level check constraint guarantees that ``finished_at`` is never
earlier than ``started_at``.
"""

from django.db import models
from django.db.models import F, Q

from apps.core.models import BaseModel


# ===========================================================================
# ImportLog
# ===========================================================================

class ImportLog(BaseModel):
    """
    Audit record for a single run of the data import pipeline.

    An ``ImportLog`` is created automatically when an import job starts and
    updated as the job progresses. The ``status`` field reflects the current
    state of the run; ``records_total``, ``records_imported``, and
    ``records_failed`` provide a progress summary.

    This model is intentionally append-only from the perspective of external
    consumers. The admin and API both expose it as read-only.

    Attributes:
        source:            Identifier for the data source
                           (e.g. a URL or a file name).
        status:            Current state of the import run.
        records_total:     Total number of records encountered.
        records_imported:  Number of records successfully imported.
        records_failed:    Number of records that could not be imported.
        started_at:        Timestamp at which the import run began.
        finished_at:       Timestamp at which the import run ended.
                           ``null`` while the run is still in progress.
                           Must not be earlier than ``started_at``.
        error_message:     Human-readable error detail when the run fails.
                           ``null`` when the run completed without error.
    """

    class Status(models.TextChoices):
        """Lifecycle states of an import run."""

        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        PARTIAL_SUCCESS = "PARTIAL_SUCCESS", "Partial Success"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    source = models.CharField(
        max_length=255,
        help_text="Identifier for the data source (e.g. a URL or a file name).",
        db_comment="The source of the import, e.g. file name or URL.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=(
            "Current state of the import run. "
            "Accepted values: `PENDING`, `IN_PROGRESS`, `PARTIAL_SUCCESS`, "
            "`SUCCESS`, `FAILED`."
        ),
        db_comment="Current status of the import process.",
    )

    records_total = models.PositiveIntegerField(
        default=0,
        help_text="Total number of records encountered during the import run.",
        db_comment="Total number of records processed.",
    )

    records_imported = models.PositiveIntegerField(
        default=0,
        help_text="Number of records successfully imported.",
        db_comment="Number of successfully imported records.",
    )

    records_failed = models.PositiveIntegerField(
        default=0,
        help_text="Number of records that could not be imported.",
        db_comment="Number of failed records.",
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="ISO 8601 UTC timestamp at which the import run began.",
        db_comment="Timestamp when the import started.",
    )

    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "ISO 8601 UTC timestamp at which the import run ended. "
            "`null` while the run is still in progress. "
            "Must not be earlier than `started_at`."
        ),
        db_comment="Timestamp when the import finished.",
    )

    error_message = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "Human-readable error detail populated when the run fails or "
            "encounters problems. `null` when the run completed without error."
        ),
        db_comment="Error message if the import failed.",
    )

    class Meta(BaseModel.Meta):
        db_table = "import_log"
        verbose_name = "Import Log"
        verbose_name_plural = "Import Logs"
        ordering = ["-started_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(started_at__isnull=True)
                    | Q(finished_at__isnull=True)
                    | Q(finished_at__gte=F("started_at"))
                ),
                name="importlog_finished_after_or_equal_started",
            )
        ]

    def __str__(self) -> str:
        return f"{self.source} - {self.status}"