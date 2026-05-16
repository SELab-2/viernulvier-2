## Overview

The backend follows a modular, domain-based Django structure that promotes maintainability, scalability, and a clear separation of concerns.  
Domain logic is organized into dedicated apps under `apps/`, while project configuration, API routing, shared static assets, templates, requirements, and tests are centralized at backend level.

```text
viernulvier_archive/
│
├── config/                                             # Django project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                                     # Shared settings
│   │   ├── dev.py                                      # Local development settings
│   │   ├── test.py                                     # Test settings
│   │   ├── staging.py                                  # Local/pre-production staging settings
│   │   └── prod.py                                     # Production settings
│   ├── health.py                                       # Health check endpoint
│   ├── urls.py                                         # Root URL config
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                                               # Domain Django apps
│   ├── blogs/                                          # BLOG + BLOG_TRANSLATION tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── core/                                           # Shared base classes and utilities
│   │   ├── __init__.py
│   │   ├── admin.py                                    # BaseAdmin, persistent selections, two-step actions
│   │   ├── admin_filters.py                            # Searchable multi-select admin filters
│   │   ├── admin_widgets.py                            # Rich-text admin widget and decorator
│   │   ├── authentications.py                          # API-key authentication
│   │   ├── exceptions.py                               # RFC 7807 exception handler
│   │   ├── filters.py                                  # BaseModelFilter
│   │   ├── media_validation.py                         # MIME/signature/size validation helpers
│   │   ├── mixins.py                                   # Shared ViewSet mixins
│   │   ├── models.py                                   # BaseModel
│   │   ├── openapi.py                                  # Reusable OpenAPI error responses
│   │   ├── ordering.py                                 # Nulls-last ordering filter
│   │   ├── permissions.py                              # API-key permission matrix
│   │   ├── serializers.py                              # TranslatableSerializerMixin
│   │   ├── spectacular_extensions.py                   # OpenAPI API-key auth extension
│   │   ├── throttles.py                                # API-key throttling classes
│   │   ├── views.py                                    # Base API ViewSets
│   │   ├── templatetags/
│   │   │   └── admin_dashboard.py                      # Custom admin dashboard cards
│   │   └── static/admin/js/
│   │       └── rich_text_admin_widget_*.js             # Rich-text admin widget modules
│   │
│   ├── languages/                                      # LANGUAGE table
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── productions/                                    # PRODUCTION + translations + classifications
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── admin_filters.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── genres/                                         # GENRE + GENRE_TRANSLATION tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── tags/                                           # TAG + TAG_TRANSLATION tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── events/                                         # EVENT + EVENT_PRICE tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── locations/                                      # LOCATION + SPACE + HALL tables (+ translations)
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── media_library/                                  # MEDIA_GALLERY + MEDIA_ITEM + CROP tables
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── media_files/                                    # Uploaded files with derived metadata
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── pricing/                                        # PRICE + PRICE_RANK + translations
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── filters.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py
│   │   └── views.py
│   │
│   ├── import_log/                                     # IMPORT_LOG table
│   │   ├── __init__.py
│   │   ├── admin.py                                    # Read-only admin for import audit logs
│   │   ├── filters.py                                  # API filters for status/source/timestamps/errors
│   │   ├── models.py                                   # ImportLog audit model
│   │   ├── schemas.py                                  # OpenAPI docs for read-only endpoints
│   │   ├── serializers.py                              # Read-only serializer with duration/warnings
│   │   └── views.py                                    # Read-only ImportLog API ViewSet
│   │
│   └── imports/                                        # Import and sync pipelines
│       ├── __init__.py
│       ├── csv_importer/                               # Legacy CSV import pipeline
│       │   ├── __init__.py
│       │   ├── legacy_csv_constants.py                 # CSV paths, headers, defaults
│       │   ├── legacy_csv_handlers.py                  # Row handlers for productions/events
│       │   ├── legacy_csv_io.py                        # CSV reading and dataset detection
│       │   ├── legacy_csv_normalize.py                 # Legacy value/date/text normalization
│       │   ├── legacy_csv_relations.py                 # Language, genre, hall helpers
│       │   └── legacy_csv_sync.py                      # Import orchestration and ImportLog handling
│       ├── management/
│       │   ├── __init__.py
│       │   └── commands/
│       │       ├── __init__.py
│       │       ├── import_legacy_csv.py                # Imports bundled legacy CSV exports
│       │       └── sync_viernulvier.py                 # Syncs Viernulvier API endpoints
│       └── scrapers/
│           ├── __init__.py
│           ├── viernulvier.py                          # Compatibility facade
│           ├── viernulvier_constants.py                # API config, exceptions, dataclasses
│           ├── viernulvier_http.py                     # HTTP sessions, retry, pagination, ETags
│           ├── viernulvier_import_log.py               # Shared ImportLog finalization helpers
│           ├── viernulvier_media.py                    # Media gallery-link and crop sync
│           ├── viernulvier_normalize.py                # Value normalization and field coercion
│           ├── viernulvier_relations.py                # FK resolution, translations, M2M sync
│           └── viernulvier_sync.py                     # Core sync loop and upsert logic
│
├── api/                                                # API routing, versioning, docs, caching, pagination
│   ├── __init__.py
│   ├── urls.py                                         # Top-level API routing
│   ├── versioning.py                                   # DRF URL path versioning config
│   ├── cache.py                                        # Shared API caching helpers
│   ├── pagination.py                                   # Shared pagination presets
│   └── v1/
│       └── urls.py                                     # v1 router with current ViewSet registrations
│
├── static/                                             # Shared static assets
│   └── admin/
│       └── js/
│           └── media_file_upload.js                    # Shared admin upload validation
│
├── templates/                                          # Shared Django/admin templates
│   ├── admin/
│   │   ├── index.html                                  # Custom admin dashboard
│   │   ├── login.html                                  # Custom admin login page
│   │   ├── persistent_change_list.html                 # Persistent cross-page selections
│   │   └── two_step_action.html                        # Confirmation form for two-step actions
│   └── multiselect_search.html                         # Searchable multi-select admin filter template
│
├── tests/                                              # Pytest test suite
│   ├── __init__.py
│   ├── api/                                            # Shared API helper tests
│   ├── blogs/                                          # Blog app tests
│   ├── config/                                         # Project configuration tests
│   ├── core/                                           # Shared core utility tests
│   ├── events/                                         # Event app tests
│   ├── factories/                                      # Test data factories
│   ├── genres/                                         # Genre app tests
│   ├── helpers/                                        # Shared test helpers
│   ├── import_logs/                                    # ImportLog app tests
│   ├── imports_csv/                                    # Legacy CSV importer tests
│   ├── languages/                                      # Language app tests
│   ├── locations/                                      # Location app tests
│   ├── media_files/                                    # Media files app tests
│   ├── media_library/                                  # Media library app tests
│   ├── pricing/                                        # Pricing app tests
│   ├── productions/                                    # Production app tests
│   ├── scrapers/                                       # Viernulvier scraper tests
│   └── tags/                                           # Tag app tests
│
├── requirements/                                       # Environment-specific dependency sets
│   ├── base.txt                                        # Shared runtime dependencies
│   ├── development.txt                                 # Development and test dependencies
│   └── production.txt                                  # Production-only dependencies
│
├── media/                                              # Local uploaded media files (ignored in git)
├── .gitignore
├── .dockerignore
├── Dockerfile
├── manage.py
├── pyproject.toml                                      # Tooling configuration
├── pytest.ini                                          # Pytest/pytest-django configuration
└── viernulvier_dev                                     # Local helper/virtual environment artifact (not committed)
```

---

## Core Files

### `manage.py`

**Purpose**: Django management entry point.

- Runs the development server.
- Executes migrations.
- Runs tests and management commands.

**Example**:

```bash
python manage.py runserver
python manage.py migrate
pytest
```

---

### `config/settings/base.py`

**Purpose**: Shared settings used across environments.

- Installed apps and middleware.
- Database defaults.
- Internationalization and time zone.
- Shared DRF/OpenAPI settings.
- Shared cache, logging, static, and media configuration.

---

### `config/settings/dev.py`

**Purpose**: Local development overrides.

- Debug enabled.
- Browsable API renderer enabled.
- Debug toolbar and CORS enabled for local frontend development.
- Throttling disabled.
- Local-only security relaxations.

---

### `config/settings/test.py`

**Purpose**: Test-specific overrides.

- In-memory SQLite database.
- Dummy cache for API caching.
- Throttling disabled.
- Faster password hashing.
- Temporary media root.

---

### `config/settings/staging.py`

**Purpose**: Local/pre-production staging settings.

- Approximates production behaviour for manual testing.
- Keeps selected security settings relaxed where plain HTTP/local access is required.
- Uses the configured API throttle classes.

---

### `config/settings/prod.py`

**Purpose**: Production settings.

- Debug disabled.
- Strict security headers and secure cookies.
- HTTPS/proxy configuration.
- Production throttle policy.

---

### `config/health.py`

**Purpose**: Health check endpoint.

- Exposes `/health/`.
- Verifies that the application is running and the default database connection is reachable.
- Returns `200` for healthy and `503` when the database is unavailable.

---

### `config/urls.py`

**Purpose**: Root URL configuration.

- Exposes `/health/`.
- Exposes Django admin at `/admin/`.
- Delegates API routes to `api.urls` under `/api/`.
- Adds debug toolbar and local media serving only when `DEBUG=True`.

---

### `api/urls.py`

**Purpose**: Top-level API routing.

- Exposes API version prefixes, such as `/api/v1/`.
- Exposes OpenAPI schema and documentation endpoints.
- Delegates version-specific viewset registration to files such as `api/v1/urls.py`.

---

### `api/v1/urls.py`

**Purpose**: Version-specific API router.

- Registers current v1 ViewSets.
- Keeps endpoint naming and grouping consistent across apps.
- Allows future API versions to be added without changing v1 routes.

---

## Directories

### `apps/`

**Purpose**: Domain modules (Django apps).

**Guidelines**:

- One domain = one app, for example `events`, `pricing`, or `locations`.
- Keep API concerns inside the app: `filters.py`, `serializers.py`, `views.py`, and `schemas.py`.
- Use explicit boundaries: shared logic belongs in `apps/core/`.

**Typical app layout**:

```text
apps/<domain>/
├── admin.py
├── filters.py
├── models.py
├── schemas.py
├── serializers.py
└── views.py
```

---

### `apps/core/`

**Purpose**: Shared base classes and reusable utilities.

**Use cases**:

- Base models.
- Shared admin mixins and widgets.
- API-key authentication, permissions, throttles, and OpenAPI extensions.
- Serializer/viewset mixins.
- Shared validation, filtering, ordering, and exception handling.

**Guidelines**:

- Keep `core/` generic and avoid domain-specific business logic.
- Prefer composition/mixins over copy-paste.

---

### `apps/imports/` and `apps/imports/scrapers/`

**Purpose**: Import, sync, and ingestion logic.

**Guidelines**:

- Keep external API specifics inside the scraper modules.
- Keep import audit data in `apps/import_log/`.
- Split complex pipelines into focused modules for HTTP, normalization, relation sync, media sync, and final persistence.

---

### `api/`

**Purpose**: Central API configuration for routing, versioning, docs, caching, and pagination.

- `api/urls.py` exposes version prefixes and documentation endpoints.
- `api/v1/urls.py` registers the current v1 viewsets.
- `api/versioning.py` defines supported API versions.
- `api/cache.py` contains reusable API cache helpers.
- `api/pagination.py` defines shared pagination presets.

---

### `static/`

**Purpose**: Shared static files that are not owned by a single app.

Current shared asset:

- `static/admin/js/media_file_upload.js` validates admin file inputs based on their `accept` attribute and prevents unsupported files from being submitted.

---

### `templates/`

**Purpose**: Shared Django/admin templates.

Current admin customizations:

- Custom admin dashboard.
- Custom admin login page.
- Persistent cross-page changelist selections.
- Two-step admin action confirmation view.
- Searchable multi-select admin filter template.

---

### `tests/`

**Purpose**: Pytest test suite.

**Guidelines**:

- Mirror domain apps where possible.
- Keep shared factories in `tests/factories/`.
- Keep shared helper utilities in `tests/helpers/`.
- Keep cross-cutting API/config tests in their own folders, such as `tests/api/` and `tests/config/`.
- Prefer consistent patterns across apps: model, serializer, view, and admin tests.

**Example structure**:

```text
tests/
├── api/
│   └── test_cache.py
├── core/
├── events/
├── factories/
├── helpers/
├── media_files/
├── productions/
└── tags/
```

---

## Configuration Files

### `.env`

- Local environment variables.
- Never commit secrets.

### `pyproject.toml`

- Tooling configuration, such as linting/formatting settings.

### `pytest.ini`

- Pytest and pytest-django configuration.

### `requirements/`

- `base.txt` — shared runtime dependencies.
- `development.txt` — development and test dependencies.
- `production.txt` — production-only dependencies.

### `Dockerfile`

- Container setup for running the backend locally or in deployment.

---

## Best Practices

### App Organization

1. **One domain per app**: avoid mega-apps.
2. **Keep boundaries clear**: shared logic belongs in `apps/core/`, not duplicated across apps.
3. **Consistent naming**: use `models.py`, `filters.py`, `serializers.py`, `views.py`, and `schemas.py` for app API code.
4. **Thin views**: move reusable or complex business logic into focused helpers/services when it grows.
5. **Document complex paths**: add concise docstrings/comments for import/sync logic, caching, validation, serializers, filters, and view/queryset logic.

---

### Naming Conventions

- **Apps**: snake_case, e.g. `media_library`, `media_files`, `import_log`.
- **Models**: PascalCase, e.g. `Event`, `MediaItem`, `ImportLog`.
- **Serializers**: `XSerializer`.
- **ViewSets**: `XViewSet`.
- **Tests**: `test_<subject>.py`, with test functions starting with `test_`.

---

### Import Order

1. Standard library.
2. Third-party imports, such as Django/DRF.
3. Local app imports, such as `apps.*`.
4. Relative imports.

---

## Quick Reference

| Path | Purpose | Example |
| --- | --- | --- |
| `config/` | Project configuration | `config/urls.py` |
| `config/settings/` | Settings per environment | `dev.py`, `test.py`, `staging.py`, `prod.py` |
| `apps/` | Domain apps | `apps/events/` |
| `apps/core/` | Shared utilities | `permissions.py`, `serializers.py` |
| `api/` | API routing, versioning, docs, caching, and pagination | `api/urls.py`, `api/v1/urls.py` |
| `static/` | Shared static assets | `static/admin/js/media_file_upload.js` |
| `templates/` | Shared Django/admin templates | `templates/admin/index.html` |
| `tests/` | Pytest tests | `tests/api/test_cache.py` |
| `requirements/` | Dependency sets | `development.txt` |
```
