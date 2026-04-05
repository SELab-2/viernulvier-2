"""Test settings for the viernulvier_archive project.

Extends base.py with:
- In-memory SQLite so tests run without a Postgres instance
- All throttling disabled so tests never fail due to rate limits
- Password hashing replaced with a trivial hasher for speed
- Media files written to a temp directory

Usage (via pytest.ini):

    [pytest]
    DJANGO_SETTINGS_MODULE = config.settings.test
"""

import tempfile

from .base import *  # noqa: F403
from .base import REST_FRAMEWORK

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

# ---------------------------------------------------------------------------
# Database - in-memory SQLite for fast, isolated test runs
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ---------------------------------------------------------------------------
# REST Framework - all throttling disabled during tests
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "public": None,
        "public_min": None,
        "public_hour": None,
        "anon": None,
        "internal": None,
    },
}

# ---------------------------------------------------------------------------
# Password hashing - use the fastest hasher available in tests
# ---------------------------------------------------------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ---------------------------------------------------------------------------
# Media files - use a temp directory so uploads don't pollute the repo
# ---------------------------------------------------------------------------

MEDIA_ROOT = tempfile.mkdtemp()

# ---------------------------------------------------------------------------
# Logging - silence everything below ERROR in tests to keep output clean
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {"class": "logging.NullHandler"},
    },
    "root": {
        "handlers": ["null"],
        "level": "ERROR",
    },
}

# ---------------------------------------------------------------------------
# Caches - use in-memory cache for tests to avoid external dependencies
# ---------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}
