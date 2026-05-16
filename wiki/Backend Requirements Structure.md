## Overview

The backend uses a structured requirements setup to separate shared runtime dependencies from development/test-only and production-only packages.

```text
backend/
└── requirements/
    ├── base.txt         # Shared runtime dependencies
    ├── development.txt  # Development and test dependencies
    └── production.txt   # Production-only dependencies
```

This improves maintainability, onboarding, and environment consistency.

---

## Files

### `base.txt`

Shared dependencies required in all environments, such as Django, Django REST Framework, database drivers, API documentation tools, caching support, and media/image handling.

### `development.txt`

Extends `base.txt` via:

```txt
-r base.txt
```

Adds development and test tools such as:

- pytest
- pytest-django
- pytest-cov
- factory-boy
- Faker
- django-debug-toolbar
- ruff

### `production.txt`

Extends `base.txt` via:

```txt
-r base.txt
```

Adds production-only packages such as:

- gunicorn

---

## Installation

Commands below assume you are in the repository root.

### Development

```bash
pip install -r backend/requirements/development.txt
```

### Production

```bash
pip install -r backend/requirements/production.txt
```

---

## Adding a New Package

1. Install the package locally:

```bash
pip install <package>
```

2. Add it to the correct requirements file:

- `base.txt` — needed in every environment.
- `development.txt` — needed only for testing, debugging, linting, or local development.
- `production.txt` — needed only at runtime in production.

3. Pin the version explicitly.
4. Run the relevant tests/lint checks.
5. Commit the updated requirements file.

---

## Notes

- Lines starting with `#` are comments and are ignored by `pip`.
- Prefer short comments above dependency groups when that improves readability.
- Keep environment-specific packages out of `base.txt` unless every environment needs them.
