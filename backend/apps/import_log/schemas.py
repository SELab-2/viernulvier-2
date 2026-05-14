"""OpenAPI schema decorators and examples for the read-only Imports app."""

from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view

from apps.core.openapi import ITEM_ERRORS, READ_ERRORS

from .serializers import ImportLogSerializer

# ===========================================================================
# ImportLog - examples
# ===========================================================================

_IMPORT_LOG_SUCCESS_RESPONSE = OpenApiExample(
    "ImportLog - successful run",
    summary="A completed import run with no failures",
    value={
        "id": 1,
        "source": "https://api.uitdatabank.be/events?limit=50&start=0",
        "status": "SUCCESS",
        "records_total": 200,
        "records_imported": 200,
        "records_failed": 0,
        "started_at": "2025-09-01T02:00:00Z",
        "finished_at": "2025-09-01T02:01:43Z",
        "duration": "0:01:43",
        "error_message": None,
    },
    response_only=True,
)

_IMPORT_LOG_PARTIAL_RESPONSE = OpenApiExample(
    "ImportLog - partial success",
    summary="A run that completed but with some failed records",
    value={
        "id": 2,
        "source": "https://api.uitdatabank.be/events?limit=50&start=50",
        "status": "PARTIAL_SUCCESS",
        "records_total": 150,
        "records_imported": 143,
        "records_failed": 7,
        "started_at": "2025-09-02T02:00:00Z",
        "finished_at": "2025-09-02T02:02:11Z",
        "duration": "0:02:11",
        "error_message": "7 records skipped due to missing required fields.",
    },
    response_only=True,
)

_IMPORT_LOG_FAILED_RESPONSE = OpenApiExample(
    "ImportLog - failed run",
    summary="A run that failed before completing",
    value={
        "id": 3,
        "source": "https://api.uitdatabank.be/events?limit=50&start=100",
        "status": "FAILED",
        "records_total": 0,
        "records_imported": 0,
        "records_failed": 0,
        "started_at": "2025-09-03T02:00:00Z",
        "finished_at": "2025-09-03T02:00:04Z",
        "duration": "0:00:04",
        "error_message": "Connection timeout after 3 retries.",
    },
    response_only=True,
)

_IMPORT_LOG_IN_PROGRESS_RESPONSE = OpenApiExample(
    "ImportLog - in progress",
    summary="A run that is currently executing",
    value={
        "id": 4,
        "source": "https://api.uitdatabank.be/events?limit=50&start=150",
        "status": "IN_PROGRESS",
        "records_total": 50,
        "records_imported": 23,
        "records_failed": 0,
        "started_at": "2025-09-04T02:00:00Z",
        "finished_at": None,
        "duration": None,
        "error_message": None,
    },
    response_only=True,
)


# ===========================================================================
# ImportLog - per-action schemas
# ===========================================================================

_IMPORT_LOG_LIST = extend_schema(
    summary="List all import logs",
    description=(
        "Returns a paginated list of all **ImportLog** records ordered from "
        "most recent to oldest by `started_at`.\n\n"
        "Use the `status` filter on the response to isolate failed or "
        "in-progress runs. The computed `duration` field provides the total "
        "wall-clock time of each run as `HH:MM:SS` - `null` while a run has "
        "not yet finished.\n\n"
        "> **Read-only.** Import logs are managed exclusively by the import "
        "pipeline and cannot be created or modified via this endpoint."
    ),
    responses={200: ImportLogSerializer, **READ_ERRORS},
    examples=[
        _IMPORT_LOG_SUCCESS_RESPONSE,
        _IMPORT_LOG_PARTIAL_RESPONSE,
        _IMPORT_LOG_FAILED_RESPONSE,
        _IMPORT_LOG_IN_PROGRESS_RESPONSE,
    ],
)

_IMPORT_LOG_RETRIEVE = extend_schema(
    summary="Retrieve an import log",
    description=(
        "Returns the full record of a single **ImportLog** identified by its "
        "primary key.\n\n"
        "The `error_message` field contains human-readable detail when a run "
        "has `status: FAILED` or `status: PARTIAL_SUCCESS`.\n\n"
        "> **Read-only.** Import logs are managed exclusively by the import "
        "pipeline and cannot be modified via this endpoint."
    ),
    responses={200: ImportLogSerializer, **ITEM_ERRORS},
    examples=[_IMPORT_LOG_SUCCESS_RESPONSE, _IMPORT_LOG_FAILED_RESPONSE],
)


# ===========================================================================
# Assembled decorator - imported and applied in views.py
# ===========================================================================

import_log_schema = extend_schema_view(
    list=_IMPORT_LOG_LIST,
    retrieve=_IMPORT_LOG_RETRIEVE,
)
