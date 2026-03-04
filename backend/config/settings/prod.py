import os

from .base import *  # noqa: F403, F401

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

CSRF_TRUSTED_ORIGINS = [
    f"https://{host.strip()}" for host in ALLOWED_HOSTS if host.strip()
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    # Authentication and permissions are already configured in base.py
    # Throttling is only enforced in production; no limits apply in development.
    'DEFAULT_THROTTLE_CLASSES': [
        'apps.core.throttles.PublicKeyMinuteThrottle', # Burst: per minute
        'apps.core.throttles.PublicKeyHourThrottle',   # Sustained: per hour
        'apps.core.throttles.InternalKeyThrottle',     # Unrestricted
    ],
    'DEFAULT_THROTTLE_RATES': {
        'public_min': '40/minute', # So a single client can't exhaust the entire minute budget in one burst
        'public_hour': '800/hour', # Allows for sustained usage without hitting limits too quickly, while still protecting against abuse.
        'internal': None,
    },
}
