"""Staging settings for the viernulvier_archive project.

Mirrors production as closely as possible so that staging catches
configuration drift before it reaches prod. The main differences are:
- HSTS is intentionally shorter (5 minutes) so the domain can be
  reassigned without browsers being locked out for a year.
- Throttle rates are lower to simplify manual and automated testing.

Usage:

    DJANGO_SETTINGS_MODULE=config.settings.staging gunicorn config.wsgi
"""

import os

from .base import *  # noqa: F403
from .base import REST_FRAMEWORK

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = False

ALLOWED_HOSTS = [host.strip() for host in os.environ["ALLOWED_HOSTS"].split(",") if host.strip()]

# ---------------------------------------------------------------------------
# Security - same as prod, except a short HSTS duration
# ---------------------------------------------------------------------------

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 300  # 5 minutes - safe to iterate on staging domains
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "SAMEORIGIN"

CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host]

# ---------------------------------------------------------------------------
# REST Framework - throttle rates lower than prod for easier manual testing
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.core.throttles.PublicKeyMinuteThrottle",
        "apps.core.throttles.PublicKeyHourThrottle",
        # fallback for unauthenticated requests, should be blocked by permissions but just in case
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "public_min": "40/minute",
        "public_hour": "800/hour",
        # fallback for unauthenticated requests, should be blocked by permissions but just in case
        "anon": "5/minute",
    },
}
