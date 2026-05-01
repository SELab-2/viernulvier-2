This guide explains how to use the `sync_viernulvier` Django management command to synchronize data from the Viernulvier/Peppered API to your local database.

## Architecture

The scraper implementation has been refactored into focused, single-responsibility modules within `backend/apps/imports/scrapers/`:

- **`viernulvier_constants.py`** - Shared constants, exceptions, and configuration dataclasses
- **`viernulvier_http.py`** - HTTP session management, retry logic, and pagination
- **`viernulvier_normalize.py`** - Value normalization and field coercion helpers
- **`viernulvier_relations.py`** - Foreign key resolution, translations, and many-to-many sync
- **`viernulvier_sync.py`** - Core model synchronization loop
- **`viernulvier_media.py`** - Media gallery and crop synchronization
- **`viernulvier.py`** - Compatibility facade maintaining legacy API

For pre-API historical data, a dedicated CSV importer is available in `backend/apps/imports/csv_importer/`:

- **`legacy_csv.py`** - Imports the bundled legacy production/event CSV exports into current models
- **`management/commands/import_legacy_csv.py`** - CLI entrypoint for running the legacy CSV import

This modular design improves maintainability, testability, and separation of concerns.

**Benefits of the refactoring**:

- Each module has a clear, single responsibility
- Lower cyclomatic complexity enables all modules to comply with ruff linting rules
- Easier to test individual components in isolation
- Simpler to locate and modify specific functionality

## Overview

The `sync_viernulvier` command fetches data from the Viernulvier/Peppered API (`https://www.viernulvier.gent/api/v1`) and synchronizes it with your local Django database. It supports:

- **Full synchronization** of all data models
- **Selective synchronization** of specific model types
- **Filtering** by creation date, update date, event start/end times
- **Inclusive and exclusive** date range filters

---

## Basic Usage

### Sync Everything

To synchronize all data from the API:

```bash
python manage.py sync_viernulvier
```

This will process all sync steps in the correct order (respecting foreign key dependencies).

### Import Historical CSV Data

To import the older pre-API archive data from the bundled CSV files:

```bash
python manage.py import_legacy_csv
```

Dry-run mode is available:

```bash
python manage.py import_legacy_csv --dry-run
```

To import only one legacy dataset, use `--only`:

```bash
python manage.py import_legacy_csv --only productions
python manage.py import_legacy_csv --only events
```

### Sync a Specific Step

To synchronize only a specific model type:

```bash
python manage.py sync_viernulvier --only <step_name>
```

For example, to sync only events:

```bash
python manage.py sync_viernulvier --only events
```

---

## Available Sync Steps

The following sync steps are available (listed in dependency order):

| Step Name           | Model           | API Endpoint         | Description                           |
| ------------------- | --------------- | -------------------- | ------------------------------------- |
| `uitdatabank_types` | UitDatabaseType | `/uitdatabank/types` | UiTdatabank types                     |
| `genres`            | Genre           | `/genres`            | Production genres                     |
| `tags`              | Tag             | `/tags`              | Tags for categorization               |
| `locations`         | Location        | `/locations`         | Physical locations/venues             |
| `spaces`            | Space           | `/spaces`            | Spaces within locations               |
| `halls`             | Hall            | `/halls`             | Halls within spaces                   |
| `media_galleries`   | MediaGallery    | `/media/galleries`   | Media galleries                       |
| `media_items`       | MediaItem       | `/media/items`       | Individual media items (images, etc.) |
| `prices`            | Price           | `/prices`            | Base price definitions                |
| `price_ranks`       | PriceRank       | `/prices/ranks`      | Price rank categories                 |
| `productions`       | Production      | `/productions`       | Productions/shows                     |
| `events`            | Event           | `/events`            | Specific event instances              |
| `event_prices`      | EventPrice      | `/events/prices`     | Pricing for specific events           |

**Note:** Steps are executed in dependency order. For example, `events` depends on `productions` and `halls`, so those must be synced first.

---

## Filtering Options

The command supports filtering by four different time-based criteria:

### Filter Prefixes

- **`created`** - Filters by record creation timestamp (`created_at` in API)
- **`updated`** - Filters by record update timestamp (`updated_at` in API)
- **`starts`** - Filters by event start time (`starts_at` in API)
- **`ends`** - Filters by event end time (`ends_at` in API)

### Filter Boundaries

Each prefix supports two types of boundaries:

1. **Inclusive boundaries** (`--{prefix}-after`, `--{prefix}-before`)
   - Includes records at the exact timestamp

2. **Exclusive boundaries** (`--{prefix}-after-x`, `--{prefix}-before-x`)
   - Excludes records at the exact timestamp

### Filter Format

All timestamp filters accept ISO 8601 formatted datetime strings:

```text
YYYY-MM-DDTHH:MM:SSZ
YYYY-MM-DDTHH:MM:SS+HH:MM
```

Example: `2024-01-01T00:00:00Z` or `2024-01-01T00:00:00+00:00`

---

## Examples

### 1. Sync Events Created After a Date (Inclusive)

Get all events created on or after June 1, 2024:

```bash
python manage.py sync_viernulvier --only events --created-after 2024-06-01T00:00:00Z
```

**API Parameter:** `created_at[after]=2024-06-01T00:00:00Z`

---

### 2. Sync Events Updated Before a Date (Inclusive)

Get all events updated on or before June 1, 2024:

```bash
python manage.py sync_viernulvier --only events --updated-before 2024-06-01T00:00:00Z
```

**API Parameter:** `updated_at[before]=2024-06-01T00:00:00Z`

---

### 3. Sync Events Starting After a Date (Exclusive)

Get all events starting strictly after June 1, 2024 (excluding events starting exactly at that time):

```bash
python manage.py sync_viernulvier --only events --starts-after-x 2024-06-01T00:00:00Z
```

**API Parameter:** `starts_at[strictly_after]=2024-06-01T00:00:00Z`

---

### 4. Sync Events Ending Before a Date (Exclusive)

Get all events ending strictly before June 1, 2024 (excluding events ending exactly at that time):

```bash
python manage.py sync_viernulvier --only events --ends-before-x 2024-06-01T00:00:00Z
```

**API Parameter:** `ends_at[strictly_before]=2024-06-01T00:00:00Z`

---

### 5. Combine Multiple Filters

Get events created after January 1, 2024, that start between June 1 and July 1, 2024:

```bash
python manage.py sync_viernulvier --only events \
  --created-after 2024-01-01T00:00:00Z \
  --starts-after 2024-06-01T00:00:00Z \
  --starts-before 2024-07-01T00:00:00Z
```

---

### 6. Sync Recent Productions

Get all productions updated in the last month:

```bash
python manage.py sync_viernulvier --only productions \
  --updated-after 2024-02-01T00:00:00Z
```

---

### 7. Sync Everything with Time Filter

Sync all models, but only fetch records updated after a specific date:

```bash
python manage.py sync_viernulvier --updated-after 2024-01-01T00:00:00Z
```

---

### 8. Full Incremental Sync

To do a daily incremental sync of all new/updated data from the previous day:

```bash
python manage.py sync_viernulvier --updated-after 2024-06-01T00:00:00Z
```

---

### 9. Incremental Sync Since the Last Successful Run

To sync everything that has changed since the last successful run,
without needing to know or pass a specific timestamp:

```bash
python manage.py sync_viernulvier --since-last-success
```

This reads the most recent non-failed `ImportLog` row for Viernulvier,
subtracts a 1-hour safety buffer from its `started_at`, and uses the
result as `--updated-after`. It is the same mechanism the scheduled
GitHub Actions workflow uses, so running it manually on the server
produces identical behaviour. Fails with a clear error if no prior
successful import exists (e.g. on a fresh database).

---

## Scheduled Runs

In production the scraper runs automatically via the
`.github/workflows/sync-viernulvier.yml` workflow on the self-hosted
runner. It calls `docker exec backend python manage.py sync_viernulvier`
against the already-running `backend` container, so it reuses the
container's environment and needs no extra configuration.

- **Schedule:** daily at `01:30 UTC`. GitHub Actions cron is always UTC.
- **Overlap protection:** a `concurrency` group prevents a new run from
  starting while the previous one is still in progress.
- **Preflight:** the workflow fails fast if the `backend` container is
  not running.

### Incremental by default

Scheduled runs only fetch new and changed records, not the full catalog.
Under the hood they pass `--since-last-success` to the command, which
reads the most recent non-failed `ImportLog` row (sources prefixed with
`viernulvier:`), subtracts a 1-hour safety buffer from its `started_at`,
and uses the result as `--updated-after` for every sync step. The API
exposes this as `updated_at[after]`, so every record touched since the
last good run comes back.

Why this is resilient: if the workflow is skipped or fails for several
days, `--updated-after` is automatically set further back to cover the
gap, because it is derived from the last successful run, not from a
fixed time window. You will never miss records as long as one
successful (or partial-success) import exists somewhere in the log.
Re-processing overlapping records is free because every row upserts by
`external_id`.

`--updated-after` (via `updated_at`) is preferred over `--created-after`
because it also catches edits to existing productions and events, not
only newly created ones.

**First run on a fresh database:** `--since-last-success` fails fast
with a clear error if no prior successful Viernulvier import exists.
Do a one-time full sync first on the server with
`docker exec -it backend python manage.py sync_viernulvier`. After that
the daily incremental run is enough.

### Changing the schedule

Edit the `cron` line in `.github/workflows/sync-viernulvier.yml`. Times
are UTC, and scheduled workflows may be delayed slightly by GitHub under
load. No other constants need tuning when changing the interval —
`--since-last-success` adapts automatically.

### Running manually

From the GitHub UI: **Actions → Sync Viernulvier data → Run workflow**.
The manual trigger accepts two optional inputs:

| Workflow input | Passed as              | Purpose                                           |
| -------------- | ---------------------- | ------------------------------------------------- |
| `only`         | `--only <value>`       | Limit to a single sync step (e.g. `events`).      |
| `full_sync`    | `--since-last-success` is omitted | Re-fetch everything regardless of time. |

Leaving both empty/unticked is the same as a scheduled run: an
incremental sync via `--since-last-success`. `full_sync` and `only` can
be combined (e.g. re-fetch every event unconditionally).

For anything else — a dry run, an explicit `--updated-after`, a
specific date range — run the command directly on the server:

```bash
docker exec -it backend python manage.py sync_viernulvier [flags...]
```

All flags documented elsewhere in this page work there.

### Partial manual runs and `--since-last-success`

`--since-last-success` looks at the latest non-failed viernulvier
`ImportLog` row **regardless of which step produced it**. That means if
you run `--only events --updated-after <some_old_ts>` by hand and it
succeeds, the next nightly incremental will use that run's `started_at`
as the starting point for every endpoint — including ones that were not
part of your `--only` run. If you need strict consistency after a
partial manual sync, follow it up with a full re-sync (tick `full_sync`
in the workflow UI, or run without `--since-last-success` on the
server) before relying on the nightly incremental again.

### Logs

Each run's full output is captured under **Actions → Sync Viernulvier
data**. For deeper inspection, `docker logs backend` on the server shows
the Django-side logs.

---

## How It Works

### Sync Process

1. **HTTP Layer** (`viernulvier_http.py`): Establishes a persistent `requests.Session` with retry logic (exponential backoff + jitter) for 429/5xx/network errors. Manages pagination and concurrent page fetching via `ThreadPoolExecutor`.
2. **Data Fetching**: The command makes paginated GET requests to the Viernulvier API endpoints with ETag support for efficient incremental syncs.
3. **Data Normalization** (`viernulvier_normalize.py`): Each API field is normalized using value transformers (URL validation, date parsing, decimal conversion, etc.)
4. **Relationship Resolution** (`viernulvier_relations.py`): Foreign keys are resolved using an in-memory cache (warm-loaded per model) to avoid N+1 queries. Many-to-many relationships are synced after the primary record.
5. **Core Sync** (`viernulvier_sync.py`): Records are created or updated based on the `external_id` field. Translations are batched per language to minimize database queries. Each record is saved within a savepoint for safe error handling.
6. **Media Sync** (`viernulvier_media.py`): Media galleries, items, and crops are fetched and synchronized separately. Crop variants (hd_ready, FE3_header) are downloaded and stored locally.
7. **Transaction Safety**: Dry-run mode is supported for inspection before writing. All changes are wrapped in database transactions.

### Key Design Decisions

- **Session pooling**: One `requests.Session` per sync run for connection reuse and auth header consistency
- **Batch translation updates**: All translated fields for one parent + one language are merged into a single DB call
- **In-memory FK cache**: One bulk query per model to populate cache, eliminating N+1 problems
- **Concurrent page fetching**: Up to 4 concurrent HTTP requests with thread pool, preserving page order
- **Per-item savepoints**: One bad record never aborts the whole batch

### Field Mapping

The scraper uses a `ModelSyncConfig` for each model that defines:

- **field_map**: Maps API field names to Django model field names
- **translations**: Configuration for translatable fields (title, description, etc.)
- **m2m**: Configuration for many-to-many relationships
- **value_transforms**: Custom transformation functions for specific fields (via `viernulvier_normalize.py`)

### External IDs

All synchronized models must have an `external_id` field that stores the API's `@id` value. This is used as the unique identifier for update-or-create operations.

---

## Module Guide for Developers

This section explains where to make changes for different types of modifications:

### Adding or Modifying API Constants

**File**: `viernulvier_constants.py`

- Base URL, endpoints, timeouts
- Retry configuration (backoff strategy, max retries, status codes)
- Error context paths
- Exception class definitions
- Configuration dataclasses (`ModelSyncConfig`, `TranslationConfig`, `M2MConfig`)

### HTTP Issues or Retry Logic

**File**: `viernulvier_http.py`

- Retry mechanism with exponential backoff and jitter
- Session management and user-agent rotation
- Pagination helpers
- Concurrent page fetching via `ThreadPoolExecutor`
- Request error handling (429, 5xx, network errors)
- ETag/304 response handling

### Value Transformation or Normalization

**File**: `viernulvier_normalize.py`

- URL validation and normalization
- Date/datetime parsing
- Decimal/number conversion
- String transformations (camelCase to snake_case)
- Field value parsing and coercion

### Foreign Keys, Translations, or M2M Relations

**File**: `viernulvier_relations.py`

- `FKCache` class for in-memory FK resolution
- Translation building and batching
- Many-to-many relationship sync
- Default value population
- Bulk loading of related objects

### Core Sync Logic and Error Handling

**File**: `viernulvier_sync.py`

- Main synchronization loop (`sync_viernulvier_impl`)
- Transaction and savepoint handling
- Upsert logic (create/update based on external_id)
- Error accumulation and reporting
- Dry-run mode
- Import logging

### Media, Galleries, and Crops

**File**: `viernulvier_media.py`

- Media gallery linking
- Crop downloading and storage
- Image variant handling (hd_ready, FE3_header)
- Media item crop synchronization
- Local file storage via Django's ImageField backend

---

## Troubleshooting

### Unknown Step Error

If you get an error like:

```text
Unknown step 'event'. Choices: uitdatabank_types, genres, ...
```

Make sure you're using the exact step name from the [Available Sync Steps](#available-sync-steps) table. The names are case-sensitive and use underscores.

### Foreign Key Errors

If you get foreign key constraint errors, you may need to sync dependency models first:

```bash
# Sync in order
python manage.py sync_viernulvier --only locations
python manage.py sync_viernulvier --only halls
python manage.py sync_viernulvier --only productions
python manage.py sync_viernulvier --only events
```

Or just run without `--only` to sync everything in the correct order.

### API Connection Issues

If the API is unreachable, check:

1. Your internet connection
2. The API base URL in `apps/imports/scrapers/viernulvier.py` (`BASE_URL`)
3. Whether the API is currently available at `https://www.viernulvier.gent/api/v1`

### Date Format Errors

Ensure your datetime strings follow the [ISO 8601 format](https://www.iso8601.com/).

---

## Additional Options

### Help Command

To see all available options:

```bash
python manage.py sync_viernulvier --help
```

### Logging

The scraper uses Python's logging module. To see detailed logs, configure Django logging in your settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.imports.scrapers.viernulvier': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Quick Reference

### All Filter Options

| Option                 | Description                                                                                                                                                              |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--created-after`      | Records created on or after this timestamp                                                                                                                               |
| `--created-before`     | Records created on or before this timestamp                                                                                                                              |
| `--created-after-x`    | Records created strictly after this timestamp                                                                                                                            |
| `--created-before-x`   | Records created strictly before this timestamp                                                                                                                           |
| `--updated-after`      | Records updated on or after this timestamp                                                                                                                               |
| `--updated-before`     | Records updated on or before this timestamp                                                                                                                              |
| `--updated-after-x`    | Records updated strictly after this timestamp                                                                                                                            |
| `--updated-before-x`   | Records updated strictly before this timestamp                                                                                                                           |
| `--since-last-success` | Set `--updated-after` from the last non-failed `ImportLog` minus 1h, so missed runs are caught up automatically. Cannot combine with an explicit `--updated-after`/`-x`. |
| `--starts-after`       | Events starting on or after this timestamp                                                                                                                               |
| `--starts-before`      | Events starting on or before this timestamp                                                                                                                              |
| `--starts-after-x`     | Events starting strictly after this timestamp                                                                                                                            |
| `--starts-before-x`    | Events starting strictly before this timestamp                                                                                                                           |
| `--ends-after`         | Events ending on or after this timestamp                                                                                                                                 |
| `--ends-before`        | Events ending on or before this timestamp                                                                                                                                |
| `--ends-after-x`       | Events ending strictly after this timestamp                                                                                                                              |
| `--ends-before-x`      | Events ending strictly before this timestamp                                                                                                                             |

---

## Contributing

### Adding a New Sync Step

If you need to add support for additional API endpoints or models:

1. **Create the Django model** in the appropriate `apps/*/models.py` file with an `external_id` field
2. **Add model configuration** in `apps/imports/management/commands/sync_viernulvier.py`:
   - Create a `ModelSyncConfig` instance with field mappings, translations, and M2M relationships
   - Register it in `SYNC_STEPS` list (in dependency order)
3. **Test thoroughly**:
   - Test with `--only <step_name>` flag first
   - Test with `--dry-run` mode to verify without writing
   - Test with various date filters
4. **Update this documentation** with the new step in the Available Sync Steps table

### Modifying Scraper Behavior

Refer to the [Module Guide for Developers](#module-guide-for-developers) section to understand which module to modify for your use case.

### Testing

Run the scraper tests from the backend directory:

```bash
cd backend
pytest apps/imports/tests/ -v
```

Or test a single step interactively:

```bash
python manage.py sync_viernulvier --only <step_name> --dry-run
```
