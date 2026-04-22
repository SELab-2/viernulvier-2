## Overview

The backend uses a structured requirements setup to clearly separate dependencies for different environments:

```text
backend/
├── requirements/
│   ├── base.txt          
│   ├── development.txt   
│   └── production.txt   
```

This improves maintainability, onboarding, and environment consistency.

---

## Files

### base.txt

Shared dependencies required in all environments (e.g. Django, DRF, database drivers).

### development.txt

Extends base: -r base.txt

Adds development-only tools such as:

- pytest
- pytest-django
- factory-boy
- Faker
- django-debug-toolbar
- ruff

### production.txt

Extends base: -r base.txt

Adds production-only packages such as:

- gunicorn

---

## Installation

### Development

```bash
pip install -r backend/requirements/development.txt
```

### Production

```bash
pip install -r backend/requirements/production.txt
```

## Adding a New Package

1. Install locally:

```bash
pip install <package>
```

1. Add it to the correct file:

- `base.txt` -> needed everywhere

- `development.txt` -> testing/debugging only
- `production.txt` -> deployment only

1. Commit the updated file.
