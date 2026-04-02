"""Base settings for the viernulvier_archive project.

Environment-specific settings files (dev, prod, test) import everything
from here and override only what differs. Never run the application with
this file directly - always use one of the environment-specific modules.

Environment variables
---------------------
All secrets and deployment-specific values are read from the environment
(or from a ``.env`` file via python-dotenv). No secret may have a
hard-coded fallback in this file.
"""

import os
from pathlib import Path
import textwrap

from dotenv import load_dotenv

from api.versioning import VERSIONING_SETTINGS

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Security - no defaults for secrets
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ["SECRET_KEY"]

# API keys used by apps.core.authentications.ApiKeyAuthentication.
# The public key grants read-only access; the internal key grants full CRUD.
PUBLIC_API_KEY: str = os.environ["PUBLIC_API_KEY"]
INTERNAL_API_KEY: str = os.environ["INTERNAL_API_KEY"]

DEBUG = False
ALLOWED_HOSTS: list[str] = []

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "drf_spectacular",
    "django_filters",
]

LOCAL_APPS = [
    "apps.core",
    "apps.languages",
    "apps.productions",
    "apps.events",
    "apps.genres",
    "apps.import_log",
    "apps.imports",
    "apps.tags",
    "apps.pricing",
    "apps.locations",
    "apps.media_library",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ---------------------------------------------------------------------------
# URLs / WSGI
# ---------------------------------------------------------------------------

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "viernulvier_archief"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,  # Persistent connections for better performance
        "OPTIONS": {
            "connect_timeout": 10,  # Short timeout for faster failure in case of DB issues
        },
    }
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static and media files
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Primary key
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    **VERSIONING_SETTINGS,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "api.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.core.authentications.ApiKeyAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "apps.core.permissions.ApiKeyPermission",
    ],
    # Throttle classes and rates are intentionally NOT set in base.py.
    # Each environment configures its own throttle policy so that tests and
    # local development are never accidentally rate-limited.
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

# ---------------------------------------------------------------------------
# drf-spectacular (OpenAPI)
# ---------------------------------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "Viernulvier Archive API",
    "DESCRIPTION": textwrap.dedent("""
        This API provides structured access to the digital archive, including
        productions, events, media, and locations.

        ### Authentication
        Access is determined by your API key:
        * **Public API key**: Read-only.
        * **Internal API key**: Full rights (CRUD).

        ### Alternative Views
        * [**ReDoc**](/api/redoc/) - Documentation-focused interface.
    """).strip(),
    "VERSION": "1.0.0",
    "CONTACT": {
        "name": "Support Team",
        "url": "https://www.viernulvier.gent/",
        "email": "info@viernulvier.gent",
    },
    "LICENSE": {
        "name": "MIT License",
    },
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+/",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [{"ApiKey": []}],
    "ERRORS_USE_REASON_PHRASES": True,
    "ERROR_SCHEMA_SYMBOLIC_NAME": "ProblemDetails",
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "ApiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Use the `X-API-Key` header to authenticate.",
            }
        },
        "schemas": {
            "ProblemDetails": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "format": "uri",
                        "default": "about:blank",
                    },
                    "title": {"type": "string"},
                    "status": {"type": "integer"},
                    "detail": {"type": "string"},
                    "instance": {"type": "string"},
                    "errors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "pointer": {"type": "string"},
                                "detail": {"type": "string"},
                                "code": {"type": "string"},
                            },
                        },
                    },
                },
            }
        },
    },
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayOperationId": False,
        "filter": False,
        "showRequestDuration": True,
        "persistAuthorization": True,
        "tagsSorter": "alpha",
        "operationsSorter": "method",
        "tryItOutEnabled": True,
        "docExpansion": "none",
        "defaultModelsExpandDepth": 0,
    },
    "TAGS": [
        {"name": "Productions", "description": "Production management and translations."},
        {"name": "Events", "description": "Event instances and pricing information."},
        {"name": "Media", "description": "Media galleries, items and crops."},
        {"name": "Locations", "description": "Locations, halls and spaces."},
        {"name": "Genres", "description": "Genre taxonomy and usage types."},
        {"name": "Tags", "description": "Tag management and production tagging."},
        {"name": "Pricing", "description": "Price ranks and price structures."},
        {"name": "Languages", "description": "Supported languages."},
        {"name": "Imports", "description": "Import pipeline audit logs."},
    ],
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "WARNING"),
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": os.environ.get("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
