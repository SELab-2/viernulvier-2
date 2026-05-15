## Overview

The backend follows a modular, domain-based Django structure that promotes maintainability, scalability, and a clear separation of concerns.  
Domain logic is organized into dedicated apps under `apps/`, while project configuration and API routing are centralized.

```text
viernulvier_archive/
│
├── config/                          # Django project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                  # shared settings
│   │   ├── dev.py                   # Dev-specific
│   |   ├── test.py                  # SQLite db for tests
│   │   └── prod.py                  # For production
│   │
│   ├── urls.py                      # Root URL config
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── blogs/                       # BLOG + BLOG_TRANSLATION tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── core/                        # Shared base classes & utilities
│   │   ├── __init__.py
│   │   ├── admin.py                     # BaseAdmin, persistent selections, two-step actions
│   │   ├── admin_filters.py             # Searchable multi-select admin filters
│   │   ├── admin_widgets.py             # Rich-text admin widget and decorator
│   │   ├── authentications.py           # API-key authentication
│   │   ├── exceptions.py                # RFC 7807 exception handler
│   │   ├── filters.py                   # BaseModelFilter
│   │   ├── media_validation.py          # MIME/signature/size validation helpers
│   │   ├── mixins.py                    # Shared ViewSet mixins
│   │   ├── models.py                    # BaseModel
│   │   ├── openapi.py                   # Reusable OpenAPI error responses
│   │   ├── ordering.py                  # Nulls-last ordering filter
│   │   ├── permissions.py               # API-key permission matrix
│   │   ├── serializers.py               # TranslatableSerializerMixin
│   │   ├── spectacular_extensions.py    # OpenAPI API-key auth extension
│   │   ├── throttles.py                 # API-key throttling classes
│   │   ├── views.py                     # Base API ViewSets
│   │   ├── templatetags/
│   │   │   └── admin_dashboard.py       # Custom admin dashboard cards
│   │   └── static/admin/js/
│   │       └── rich_text_admin_widget_*.js
│   │
│   ├── languages/                   # LANGUAGE table
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── productions/                 # PRODUCTION + PRODUCTION_TRANSLATION + production classification tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── genres/                      # GENRE + GENRE_TRANSLATION tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── tags/                        # TAG + TAG_TRANSLATION + PRODUCTION_TAG tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── events/                      # EVENT + EVENT_PRICE tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── locations/                   # LOCATION + SPACE + HALL tables (+ translations)
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── media_library/               # MEDIA_GALLERY + MEDIA_ITEM + CROP tables (+ translations)
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── media_files/                 # Uploaded files (images/PDF) with derived metadata
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── pricing/                     # PRICE + PRICE_RANK + translations 
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── import_log/                     # IMPORT_LOG table
│   |   ├── __init__.py
│   |   ├── admin.py
│   |   ├── filters.py
│   |   ├── models.py
│   |   ├── schemas.py
│   |   ├── serializers.py
│   |   └── views.py
│   |        
│   └── imports/                        # Scraping logic
│       ├── __init__.py
│       ├── csv_importer/
│       │   ├── legacy_csv_constants.py         # CSV paths, headers, and language defaults
│       │   ├── legacy_csv_handlers.py          # Row handlers for productions and events
│       │   ├── legacy_csv_io.py                # CSV reading and dataset detection
│       │   ├── legacy_csv_normalize.py         # Legacy value/date/text normalization
│       │   ├── legacy_csv_relations.py         # Language, genre, hall relation helpers
│       │   └── legacy_csv_sync.py              # CSV import orchestration and ImportLog handling
│       ├── management/
│       |   ├── __init__.py
│       |   └── commands/
│       |       ├── __init__.py
│       |       ├── import_legacy_csv.py        # Imports bundled legacy CSV exports
│       |       └── sync_viernulvier.py         # Syncs configured Viernulvier API endpoints
|       |
│       └── scrapers/
│           ├── __init__.py
│           ├── viernulvier.py                 # Compatibility facade
│           ├── viernulvier_constants.py       # API config, exceptions, dataclasses
│           ├── viernulvier_http.py            # HTTP sessions, retry, pagination, ETag handling
│           ├── viernulvier_import_log.py      # Shared ImportLog finalization helpers
│           ├── viernulvier_normalize.py       # Value normalization and field coercion
│           ├── viernulvier_relations.py       # FK resolution, translations, M2M sync
│           ├── viernulvier_sync.py            # Core sync loop & upsert logic
│           └── viernulvier_media.py           # Media gallery-link and crop sync
│
├── api/    # OpenAPI / DRF router
│   ├── urls.py          # Top-level API routing: versions + schema/docs endpoints
│   ├── versioning.py    # DRF URL path versioning config
│   ├── cache.py         # Shared API caching decorators and cache invalidation helpers
│   ├── pagination.py    # Shared pagination presets
│   └── v1/
|       └── urls.py      # v1 router with all current viewset registrations
│
├── tests/                           # Pytest test suite
│   ├── core/
│   │   ├── test_core_admin.py
│   │   ├── test_core_authentication.py
│   │   ├── test_core_models.py
│   │   ├── test_core_permissions.py
│   │   ├── test_core_serializers.py
│   │   ├── test_core_throttles.py
│   │   └── test_core_views.py
│   ├── events/
│   │   ├── test_event_admin.py
│   │   ├── test_event_models.py
│   │   ├── test_event_serializers.py
│   │   └── test_event_views.py
│   ├── factories/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── event.py
│   │   ├── genre.py
│   │   ├── import_log.py
│   │   ├── language.py
│   │   ├── location.py
│   │   ├── media_library.py
│   │   ├── pricing.py
│   │   ├── production.py
│   │   └── tag.py
│   ├── genres/
│   │   ├── test_genre_admin.py
│   │   ├── test_genre_models.py
│   │   ├── test_genre_serializers.py
│   │   └── test_genre_views.py
│   ├── import_logs/
│   │   ├── test_import_log_admin.py
│   │   ├── test_import_log_models.py
│   │   ├── test_import_log_serializers.py
│   │   └── test_import_log_views.py
│   ├── languages/
│   │   ├── test_language_admin.py
│   │   ├── test_language_models.py
│   │   ├── test_language_serializers.py
│   │   └── test_language_views.py
│   ├── locations/
│   │   ├── test_location_admin.py
│   │   ├── test_location_models.py
│   │   ├── test_location_serializers.py
│   │   └── test_location_views.py
│   ├── media_library/
│   │   ├── test_media_library_admin.py
│   │   ├── test_media_library_models.py
│   │   ├── test_media_library_serializers.py
│   │   └── test_media_library_views.py
│   ├── pricing/
│   │   ├── test_pricing_admin.py
│   │   ├── test_pricing_models.py
│   │   ├── test_pricing_serializers.py
│   │   └── test_pricing_views.py
│   ├── productions/
│   │   ├── test_production_admin.py
│   │   ├── test_production_models.py
│   │   ├── test_production_serializers.py
│   │   └── test_production_views.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── test_sync_configs.py
│   │   └── test_viernulvier.py
│   ├── imports_csv/
│   │   └── test_legacy_csv_importer.py
│   └── tags/
│       ├── test_tag_admin.py
│       ├── test_tag_models.py
│       ├── test_tag_serializers.py
│       └── test_tag_views.py
│
├── .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── manage.py
├── pyproject.toml                   # Dependencies (or requirements/)
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
└── README.md
```

---

## Core Files

### `manage.py`

**Purpose**: Django management entry point

- Runs the development server
- Executes migrations
- Runs tests and management commands

**Example**:

```bash
python manage.py runserver
python manage.py migrate
python manage.py test
```

---

### `config/settings/base.py`

**Purpose**: Shared settings used across environments

- Installed apps and middleware
- Database defaults
- Internationalization and time zone
- Shared DRF/OpenAPI settings (if configured here)

---

### `config/settings/dev.py`

**Purpose**: Development overrides

- Debug enabled
- Local database settings
- Dev-only integrations (if any)

---

### `config/settings/test.py`

**Purpose**: Test-specific overrides

- Fast test database config (commonly SQLite)
- Settings that make tests deterministic

---

### `config/settings/prod.py`

**Purpose**: Production settings

- Debug disabled
- Secure settings (allowed hosts, SSL headers, etc.)
- Production database and logging

---

### `api/urls.py`

**Purpose**: Top-level API routing

- Exposes API version prefixes, such as `/api/v1/`
- Exposes OpenAPI schema and documentation endpoints
- Delegates version-specific viewset registration to files such as `api/v1/urls.py`

---

## Directories

### `apps/`

**Purpose**: Domain modules (Django apps)

**Guidelines**:

- One domain = one app (e.g. `events`, `pricing`, `locations`)
- Keep API concerns inside the app (`serializers.py`, `views.py`, `schemas.py`)
- Use explicit boundaries: shared logic goes to `apps/core/`

**Typical app layout**:

```text
apps/<domain>/
├── admin.py
├── models.py
├── schemas.py
├── serializers.py
└── views.py
```

---

### `apps/core/`

**Purpose**: Shared base classes and reusable utilities

**Use cases**:

- Base models (timestamps, soft-delete patterns, common fields)
- Reusable serializer mixins (e.g. translation helpers)
- Shared viewsets (e.g. read-only base viewsets)
- Common permissions/authentication helpers

**Guidelines**:

- Keep `core/` generic (no domain-specific logic)
- Prefer composition/mixins over copy-paste

---

### `imports/` and `imports/scrapers/`

**Purpose**: Import logging and scraping/ingestion logic

**Guidelines**:

- Scrapers implement a shared interface (`AbstractScraper`)
- ImportLog models store import metadata (status, timestamps, etc.)
- Keep external API specifics inside the scraper module

---

### `api/`

**Purpose**: Central API configuration for routing, versioning, docs, caching, and pagination.

- `api/urls.py` exposes version prefixes and documentation endpoints.
- `api/v1/urls.py` registers the current v1 viewsets.
- `api/versioning.py` defines supported API versions.
- `api/cache.py` contains reusable API cache helpers.
- `api/pagination.py` defines shared pagination presets.

---

### `tests/`

**Purpose**: Pytest test suite

**Guidelines**:

- Mirror domain apps (tests grouped per app)
- Keep shared fixtures in `tests/conftest.py`
- Prefer consistent patterns across apps (models/serializers/views/admin)

**Example structure**:

```text
tests/
├── pricing/
│   ├── test_pricing_models.py
│   ├── test_pricing_serializers.py
│   ├── test_pricing_views.py
│   └── test_pricing_admin.py
└── events/
    ├── test_event_models.py
    ├── test_event_serializers.py
    ├── test_event_views.py
    └── test_event_admin.py
```

---

## Configuration Files

### `.env`

- Local environment variables
- Never commit secrets

### `pyproject.toml`

- Tooling configuration (formatters, linters, etc.)
- Dependencies (if not using only `requirements/`)

### `requirements/`

- `base.txt` — shared dependencies
- `development.txt` — dev-only dependencies
- `production.txt` — production dependencies

### `Dockerfile` / `docker-compose.yml`

- Container setup for running the backend locally or in CI

---

## Best Practices

### App Organization

1. **One domain per app**: avoid “mega-apps”
2. **Keep boundaries clear**: shared logic in `apps/core/`, not duplicated
3. **Consistent naming**: `models.py`, `serializers.py`, `views.py`, `schemas.py`
4. **Thin views**: business logic belongs in services/managers if it grows

---

### Naming Conventions

- **Apps**: snake_case (e.g. `media_library`, `imports`)
- **Models**: PascalCase (e.g. `Event`, `MediaItem`)
- **Serializers**: `XSerializer`
- **ViewSets**: `XViewSet`
- **Tests**: `test_<subject>.py`, test functions start with `test_`

---

### Import Order

1. Standard library
2. Third-party (Django/DRF)
3. Local apps imports (`apps.*`)
4. Relative imports

---

## Quick Reference

| Path | Purpose | Example |
| ------ | --------- | --------- |
| `config/` | Project configuration | `config/urls.py` |
| `config/settings/` | Settings per environment | `dev.py`, `test.py` |
| `apps/` | Domain apps | `apps/events/` |
| `apps/core/` | Shared utilities | `permissions.py` |
| `api/` | API routing, versioning, docs, caching, and pagination | `api/urls.py`, `api/v1/urls.py` |
| `tests/` | Pytest tests | `tests/pricing/test_views.py` |
| `requirements/` | Dependency sets | `development.txt` |
