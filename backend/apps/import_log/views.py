"""
ViewSets for the Imports app.

Schema annotations are kept in schemas.py so this file stays focused
on routing logic only.

The imports app exposes a read-only endpoint for monitoring the data
ingestion pipeline. Write operations are intentionally not supported —
import logs are created and updated exclusively by the import pipeline.
"""

from drf_spectacular.utils import extend_schema

from apps.core.views import ApiReadOnlyViewSet

from .models import ImportLog
from .schemas import import_log_schema
from .serializers import ImportLogSerializer

_TAG = "Imports"  # Reusable tag for all import-related endpoints in the OpenAPI docs


@extend_schema(tags=[_TAG])
@import_log_schema
class ImportLogViewSet(ApiReadOnlyViewSet):
    """
    Read-only endpoint for monitoring ImportLog records.

    Import logs are created and updated exclusively by the import pipeline.
    This endpoint provides visibility into the pipeline's activity and is
    useful for debugging failed or partial runs.

    Both public and internal API keys have read access. Write operations
    (POST, PUT, PATCH, DELETE) are not supported — ``ApiReadOnlyViewSet``
    only registers the ``list`` and ``retrieve`` routes.

    Results are ordered from most recent to oldest via the model's default
    ``ordering = ["-started_at"]``.

    Queryset strategy
    -----------------
    No ``select_related`` or ``prefetch_related`` is needed — ``ImportLog``
    has no FK or M2M relations that are rendered by the serializer.
    """

    serializer_class = ImportLogSerializer
    queryset = ImportLog.objects.all()