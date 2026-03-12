"""
Serializers for the Imports app.

``ImportLogSerializer`` is a read-only serializer that adds a computed
``duration`` field to the standard model fields. Write operations are
explicitly blocked at the serializer level to match the read-only intent
of the API endpoint.

The ``duration`` field is computed from ``finished_at - started_at`` and
returned as an ``HH:MM:SS`` string, making it easy to compare run times
at a glance without client-side datetime arithmetic.
"""

from rest_framework import serializers

from .models import ImportLog


class ImportLogSerializer(serializers.ModelSerializer):
    """
    Read-only representation of an ImportLog.

    Exposes the full audit trail of an import run, including record counts,
    status, timestamps, and a computed ``duration`` field. All fields are
    explicitly marked read-only.

    Write operations (:meth:`create` and :meth:`update`) raise a
    ``ValidationError`` as an additional guard - import logs must only be
    created and mutated by the import pipeline itself.

    Computed fields
    ---------------
    ``duration``
        Total wall-clock time of the import run, formatted as ``HH:MM:SS``.
        ``null`` when either ``started_at`` or ``finished_at`` is not yet set
        (i.e. the run has not started or has not finished).
    """

    duration = serializers.SerializerMethodField(
        help_text=(
            "Total wall-clock time of the import run, formatted as `HH:MM:SS`. "
            "`null` when the run has not started or has not finished yet."
        ),
    )

    class Meta:
        model = ImportLog
        fields = [
            "id",
            "source",
            "status",
            "records_total",
            "records_imported",
            "records_failed",
            "started_at",
            "finished_at",
            "duration",
            "error_message",
        ]
        read_only_fields = fields
        extra_kwargs = {
            "source": {
                "help_text": "Identifier for the data source (e.g. a URL or a file name).",
            },
            "status": {
                "help_text": (
                    "Current state of the import run. "
                    "One of: `PENDING`, `IN_PROGRESS`, `PARTIAL_SUCCESS`, `SUCCESS`, `FAILED`."
                ),
            },
            "records_total": {
                "help_text": "Total number of records encountered during the import run.",
            },
            "records_imported": {
                "help_text": "Number of records successfully imported.",
            },
            "records_failed": {
                "help_text": "Number of records that could not be imported.",
            },
            "started_at": {
                "help_text": "ISO 8601 UTC timestamp at which the import run began.",
            },
            "finished_at": {
                "help_text": (
                    "ISO 8601 UTC timestamp at which the import run ended. `null` while the run is still in progress."
                ),
            },
            "error_message": {
                "help_text": (
                    "Human-readable error detail populated when the run fails. `null` when the run completed without error."
                ),
            },
        }

    # ---------------------------------------------------------------------------
    # Computed field
    # ---------------------------------------------------------------------------

    def get_duration(self, obj: ImportLog) -> str | None:
        """
        Return the total processing time as an ``HH:MM:SS`` string.

        Microseconds are stripped by splitting on ``.`` so the value is
        human-readable at a glance. Returns ``None`` when either timestamp
        is absent.
        """
        if obj.started_at and obj.finished_at:
            delta = obj.finished_at - obj.started_at
            return str(delta).split(".")[0]  # Strip microseconds -> HH:MM:SS
        return None

    # ---------------------------------------------------------------------------
    # Explicit write guards
    # ---------------------------------------------------------------------------

    def create(self, validated_data: dict) -> None:
        """Prevent creation of import logs via the API."""
        raise serializers.ValidationError("Import logs cannot be created via the API.")

    def update(self, instance: ImportLog, validated_data: dict) -> None:
        """Prevent modification of import logs via the API."""
        raise serializers.ValidationError("Import logs cannot be updated via the API.")
