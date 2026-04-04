## Overview

The backend follows a modular, domain-based Django structure that promotes maintainability, scalability, and a clear separation of concerns.  
Domain logic is organized into dedicated apps under `apps/`, while project configuration and API routing are centralized.

```
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
│   ├── urls.py                      # Root URL config
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── core/                        # Shared base classes & utilities
│   │   ├── __init__.py
│   │   ├── admin.py                 # Base admin mixins
│   │   ├── authentications.py       # Authentication validation
│   │   ├── permissions.py           # Internal/public Api-Key validation
│   │   ├── serializers.py           # TranslatableSerializerMixin
│   │   ├── openapi.py               # Reusable responses
│   │   ├── views.py                 # ApiModelViewSet and ApiReadOnlyViewSet
│   │   ├── models.py                # BaseModel base
│   │   ├── spectacular_extensions.py # Defines OpenAPI schema extension for API-key authentication
│   │   └── throttles.py             # Implements DRF rate-limiting classes for public and internal API keys
│   │
│   ├── languages/                   # LANGUAGE table
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── productions/                 # PRODUCTION + PRODUCTION_TRANSLATION + UITDATABANK tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── genres/                      # GENRE + GENRE_USE_AS + GENRE_TRANSLATION tables
│   │   ├── __init__.py
│   │   ├── admin.py
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
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── locations/                   # LOCATION + SPACE + HALL tables (+ translations)
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── media_library/               # MEDIA_GALLERY + MEDIA_ITEM + CROP tables (+ translations)
│   │   ├── __init__.py
│   │   ├── admin.py
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
│   |   ├── models.py
│   |   ├── schemas.py
│   |   ├── serializers.py
│   |   └── views.py
│   |        
│   └── imports/                        # Scraping logic
│       ├── __init__.py
│       ├── management/
│       |   ├── __init__.py
│       |   └── commands/
│       |       ├── __init__.py
│       |       └── sync_viernulvier.py
|       |
│       └── scrapers/
│           ├── __init__.py
│           ├── viernulvier.py                 # Compatibility facade
│           ├── viernulvier_constants.py       # API config, exceptions, dataclasses
│           ├── viernulvier_http.py            # HTTP, retry, pagination
│           ├── viernulvier_normalize.py       # Value normalization & coercion
│           ├── viernulvier_relations.py       # FK resolution, translations, M2M
│           ├── viernulvier_sync.py            # Core sync loop & upsert logic
│           └── viernulvier_media.py           # Media gallery & crop sync
│
├── api/                             # OpenAPI / DRF router
│   ├── __init__.py
│   ├── urls.py                      # Central API router
│   └── pagination.py                # Custom pagination
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
**Purpose**: Central API router

- Registers app viewsets
- Defines API prefixes (e.g. `/api/`)
- Keeps routing consistent across apps

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
**Purpose**: Central DRF/OpenAPI routing and shared API configuration

**Guidelines**:
- Keep app-specific routes/viewsets inside apps
- Use `api/urls.py` only to aggregate and version/prefix endpoints
- Put cross-cutting API concerns here (pagination, versioning)

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
|------|---------|---------|
| `config/` | Project configuration | `config/urls.py` |
| `config/settings/` | Settings per environment | `dev.py`, `test.py` |
| `apps/` | Domain apps | `apps/events/` |
| `apps/core/` | Shared utilities | `permissions.py` |
| `api/` | Central API routing | `api/urls.py` |
| `tests/` | Pytest tests | `tests/pricing/test_views.py` |
| `requirements/` | Dependency sets | `development.txt` |
