This guide explains how to use the `sync_viernulvier` Django management command to synchronize data from the Viernulvier/Peppered API to your local database.

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

| Step Name              | Model              | API Endpoint            | Description                           |
|------------------------|--------------------|-------------------------|---------------------------------------|
| `uitdatabank_themes`   | UitDatabaseTheme   | `/uitdatabank/themes`   | UiTdatabank themes                    |
| `uitdatabank_types`    | UitDatabaseType    | `/uitdatabank/types`    | UiTdatabank types                     |
| `genres`               | Genre              | `/genres`               | Production genres                     |
| `tags`                 | Tag                | `/tags`                 | Tags for categorization               |
| `locations`            | Location           | `/locations`            | Physical locations/venues             |
| `spaces`               | Space              | `/spaces`               | Spaces within locations               |
| `halls`                | Hall               | `/halls`                | Halls within spaces                   |
| `media_galleries`      | MediaGallery       | `/media/galleries`      | Media galleries                       |
| `media_items`          | MediaItem          | `/media/items`          | Individual media items (images, etc.) |
| `prices`               | Price              | `/prices`               | Base price definitions                |
| `price_ranks`          | PriceRank          | `/prices/ranks`         | Price rank categories                 |
| `productions`          | Production         | `/productions`          | Productions/shows                     |
| `events`               | Event              | `/events`               | Specific event instances              |
| `event_prices`         | EventPrice         | `/events/prices`        | Pricing for specific events           |

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

```
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

## How It Works

### Sync Process

1. **API Request**: The command makes paginated GET requests to the Viernulvier API endpoints
2. **Data Mapping**: Each API field is mapped to the corresponding Django model field using configuration
3. **Upsert Logic**: Records are created or updated based on the `external_id` field
4. **Translations**: Multi-language fields are synced to separate translation models
5. **Relationships**: Foreign keys and many-to-many relationships are resolved and linked
6. **Transaction Safety**: Each record is saved within a database transaction for data integrity

### Field Mapping

The scraper uses a `ModelSyncConfig` for each model that defines:

- **field_map**: Maps API field names to Django model field names
- **translations**: Configuration for translatable fields (title, description, etc.)
- **m2m**: Configuration for many-to-many relationships
- **value_transforms**: Custom transformation functions for specific fields

### External IDs

All synchronized models must have an `external_id` field that stores the API's `@id` value. This is used as the unique identifier for update-or-create operations.

---

## Troubleshooting

### Unknown Step Error

If you get an error like:

```
Unknown step 'event'. Choices: uitdatabank_themes, uitdatabank_types, ...
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

| Option                   | Description                                          |
|--------------------------|------------------------------------------------------|
| `--created-after`        | Records created on or after this timestamp           |
| `--created-before`       | Records created on or before this timestamp          |
| `--created-after-x`      | Records created strictly after this timestamp        |
| `--created-before-x`     | Records created strictly before this timestamp       |
| `--updated-after`        | Records updated on or after this timestamp           |
| `--updated-before`       | Records updated on or before this timestamp          |
| `--updated-after-x`      | Records updated strictly after this timestamp        |
| `--updated-before-x`     | Records updated strictly before this timestamp       |
| `--starts-after`         | Events starting on or after this timestamp           |
| `--starts-before`        | Events starting on or before this timestamp          |
| `--starts-after-x`       | Events starting strictly after this timestamp        |
| `--starts-before-x`      | Events starting strictly before this timestamp       |
| `--ends-after`           | Events ending on or after this timestamp             |
| `--ends-before`          | Events ending on or before this timestamp            |
| `--ends-after-x`         | Events ending strictly after this timestamp          |
| `--ends-before-x`        | Events ending strictly before this timestamp         |

---

## Contributing

If you need to add support for additional API endpoints or models:

1. Add the model configuration in `apps/imports/management/commands/sync_viernulvier.py`
2. Add the sync step to the `SYNC_STEPS` list (in dependency order)
3. Test with `--only` flag first
4. Update this documentation

Make sure there exists a model for Django, and it is present in the database.

