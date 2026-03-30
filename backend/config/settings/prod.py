"""Production settings for the viernulvier_archive project.

Extends base.py with:
- Strict security headers (HSTS, secure cookies, SSL redirect)
- Full throttle policy (burst + sustained limits for public keys)
- No BrowsableAPIRenderer

All values that differ per deployment must come from environment variables.
No secrets or host names may be hard-coded here.

Usage:

    DJANGO_SETTINGS_MODULE=config.settings.prod gunicorn config.wsgi
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
# Security
# ---------------------------------------------------------------------------

# Trust the X-Forwarded-Proto header set by the reverse proxy (nginx / ALB).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Redirect all HTTP requests to HTTPS at the Django level.
SECURE_SSL_REDIRECT = True

# HSTS: tell browsers to only connect over HTTPS for one year.
# includeSubDomains and preload are intentionally omitted until the full
# domain inventory is confirmed.
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Cookies are only sent over HTTPS.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Prevent the browser from sniffing the content type.
SECURE_CONTENT_TYPE_NOSNIFF = True

# Only allow the site to be embedded in frames from the same origin.
X_FRAME_OPTIONS = "SAMEORIGIN"

# Trust HTTPS origins for CSRF.
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host]

# ---------------------------------------------------------------------------
# REST Framework - enforce throttling for public API keys
# ---------------------------------------------------------------------------
#
# Two complementary limits prevent both burst abuse and sustained overuse:
#   public_min  - no single client can exhaust the minute budget in one go
#   public_hour - sustained usage cap across a rolling hour window
#   anon        - fallback for unauthenticated requests, should be blocked by permissions but just in case
#   internal    - no limit; internal callers are trusted
#
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.core.throttles.PublicKeyMinuteThrottle",
        "apps.core.throttles.PublicKeyHourThrottle",
        "apps.core.throttles.InternalKeyThrottle",
        # fallback for unauthenticated requests, should be blocked by permissions but just in case
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "public_min": "40/minute",
        "public_hour": "800/hour",
        # fallback for unauthenticated requests, should be blocked by permissions but just in case
        "anon": "10/minute",
        "internal": None,
    },
}
