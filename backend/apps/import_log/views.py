"""
ViewSets for the Imports app.

Schema annotations are kept in schemas.py so this file stays focused
on routing logic only.

The imports app exposes a read-only endpoint for monitoring the data
ingestion pipeline. Write operations are intentionally not supported -
import logs are created and updated exclusively by the import pipeline.
"""

from drf_spectacular.utils import extend_schema

from apps.core.views import ApiReadOnlyViewSet

from .filters import ImportLogFilter
from .models import ImportLog
from .schemas import import_log_schema
from .serializers import ImportLogSerializer

_TAG = "Imports"


@extend_schema(tags=[_TAG])
@import_log_schema
class ImportLogViewSet(ApiReadOnlyViewSet):
    """
    Read-only endpoint for monitoring ImportLog records.

    Import logs are created and updated exclusively by the import pipeline.
    This endpoint provides visibility into the pipeline's activity and is
    useful for debugging failed or partial runs.

    Both public and internal API keys have read access. Write operations
    (POST, PUT, PATCH, DELETE) are not supported.

    Filtering
    ---------
    ``?status=FAILED``
        Filter by pipeline run status. Accepted values: ``PENDING``,
        ``IN_PROGRESS``, ``PARTIAL_SUCCESS``, ``SUCCESS``, ``FAILED``.
    ``?source=viernulvier``
        Substring match on the source identifier.
    ``?started_at_after=2024-01-01T00:00:00Z``
        Runs started on or after the given datetime (ISO 8601).
    ``?started_at_before=2024-12-31T23:59:59Z``
        Runs started on or before the given datetime (ISO 8601).
    ``?finished_at_after=2024-01-01T00:00:00Z``
        Runs finished on or after the given datetime (ISO 8601).
    ``?finished_at_before=2024-12-31T23:59:59Z``
        Runs finished on or before the given datetime (ISO 8601).
    ``?has_error=true``
        Only runs that have (``true``) or lack (``false``) an error message.

    Ordering
    --------
    ``?ordering=-started_at``
        Most recent runs first (default).
    ``?ordering=status``
        Group by pipeline status.
    ``?ordering=source``
        Alphabetical by source identifier.

    Search
    ------
    ``?search=viernulvier``
        Full-text search across ``source`` and ``status``.

    Queryset strategy
    -----------------
    No ``select_related`` or ``prefetch_related`` is needed - ``ImportLog``
    has no FK or M2M relations rendered by the serializer.
    """

    serializer_class = ImportLogSerializer
    queryset = ImportLog.objects.order_by("-started_at")

    filterset_class = ImportLogFilter
    ordering_fields = ["started_at", "finished_at", "status", "source"]
    ordering = ["-started_at"]
    search_fields = ["source", "status"]