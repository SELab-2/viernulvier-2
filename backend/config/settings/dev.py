from .base import *
import os

DEBUG = True
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]


REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# If you want to enable throttling in development for testing purposes, you can override the throttle classes and rates here.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_CLASSES': [
        'apps.core.throttles.PublicKeyMinuteThrottle',
        'apps.core.throttles.PublicKeyHourThrottle',
        'apps.core.throttles.InternalKeyThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        "internal": None,
        "public_min": None,
        "public_hour": None,
    },
}

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa
INTERNAL_IPS = ["127.0.0.1"]
