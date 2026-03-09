# Import Pipeline & Import Log

This page documents the import pipeline monitoring infrastructure for the VIERNULVIER archive project.

## Overview

The import pipeline ingests data from external sources (e.g. the Viernulvier/Peppered API) and stores it in the Django database. Each pipeline run is tracked via an `ImportLog` record, which provides a lightweight audit trail of every import job.

The `import_log` app exposes a **read-only API endpoint** at `/api/import-logs/` for monitoring pipeline activity. Import logs are created and updated exclusively by the import pipeline itself — they cannot be created or modified via the API or Django admin.

---

## ImportLog Model

Defined in `apps/import_log/models.py`.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Auto-generated primary key |
| `source` | string (max 255) | Identifier for the data source (e.g. a URL or file name) |
| `status` | string | Current state of the import run (see [Status Values](#status-values)) |
| `records_total` | positive integer | Total number of records encountered |
| `records_imported` | positive integer | Number of records successfully imported |
| `records_failed` | positive integer | Number of records that could not be imported |
| `started_at` | datetime (ISO 8601) | Timestamp at which the import run began (`null` if not started) |
| `finished_at` | datetime (ISO 8601) | Timestamp at which the import run ended (`null` while in progress) |
| `error_message` | text | Human-readable error detail when the run fails (`null` on success) |

### Status Values

| Status | Description |
|--------|-------------|
| `PENDING` | Import run is queued but has not started yet |
| `IN_PROGRESS` | Import run is currently executing |
| `PARTIAL_SUCCESS` | Import run completed, but some records failed |
| `SUCCESS` | Import run completed successfully with no failures |
| `FAILED` | Import run encountered a fatal error and was aborted |

### Constraints

- `finished_at` must not be earlier than `started_at` (enforced via a database-level check constraint).
- Records are ordered by `started_at` descending (most recent first) by default.

---

## API Endpoint

The `ImportLogViewSet` exposes the import log data as a read-only REST endpoint.

### Base URL

```
/api/import-logs/
```

### Supported Actions

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/import-logs/` | List all import logs (paginated, most recent first) |
| `GET` | `/api/import-logs/{id}/` | Retrieve a single import log by ID |

Write operations (`POST`, `PUT`, `PATCH`, `DELETE`) are not supported.

### Authentication

Both `PUBLIC_API_KEY` (read-only) and `INTERNAL_API_KEY` (full CRUD) grant read access to this endpoint. See the [API Overview](API%20Overview.md) for authentication details.

### Example Response

```json
{
  "id": 1,
  "source": "https://www.viernulvier.gent/api/v1/events",
  "status": "SUCCESS",
  "records_total": 200,
  "records_imported": 200,
  "records_failed": 0,
  "started_at": "2025-09-01T02:00:00Z",
  "finished_at": "2025-09-01T02:01:43Z",
  "duration": "0:01:43",
  "error_message": null
}
```

> **Note:** The `duration` field is computed by the serializer as `finished_at - started_at`, formatted as `HH:MM:SS`. It returns `null` when either timestamp is absent.

---

## Django Admin

Import logs are accessible in the Django admin at `/admin/import_log/importlog/` as a **read-only** view. The admin allows filtering by `status` and searching by `source` or `error_message`. Manual creation and editing of import logs via the admin is disabled to preserve audit integrity.

---

## Contributing

When implementing or extending the import pipeline:

1. Create an `ImportLog` record at the start of each pipeline run and update it as records are processed.
2. Use the `status` field to reflect the current state of the run.
3. Populate `error_message` on failure for debuggability.
4. Do not expose write operations for `ImportLog` via the API or admin — it is an append-only audit trail.

