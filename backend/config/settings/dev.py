"""Development settings for the viernulvier_archive project.

Extends base.py with:
- DEBUG mode and relaxed security
- BrowsableAPIRenderer for the DRF UI
- Throttling fully disabled
- django-debug-toolbar for query inspection
- django-cors-headers for local frontend dev (e.g. Vite on :5173)

Usage:

    DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py runserver
"""

import os

from corsheaders.defaults import default_headers

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, MIDDLEWARE, REST_FRAMEWORK

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ---------------------------------------------------------------------------
# REST Framework - add BrowsableAPIRenderer and disable all throttling
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}

# ---------------------------------------------------------------------------
# django-debug-toolbar
# ---------------------------------------------------------------------------

INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
INTERNAL_IPS = ["127.0.0.1"]

# ---------------------------------------------------------------------------
# django-cors-headers
# ---------------------------------------------------------------------------

INSTALLED_APPS = [*INSTALLED_APPS, "corsheaders"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", *MIDDLEWARE]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
CORS_ALLOW_HEADERS = [*default_headers, "x-api-key"]

# ---------------------------------------------------------------------------
# Security - relaxed for local development
# ---------------------------------------------------------------------------

# Django's SecurityMiddleware sets X-Content-Type-Options: nosniff by default.
# In development this causes browsers to download WebP files instead of
# displaying them inline when served cross-origin (Django :8000 → Vite :5173).
# Safe to disable locally: in production media is served via S3/Nginx, not Django.
SECURE_CONTENT_TYPE_NOSNIFF = False
