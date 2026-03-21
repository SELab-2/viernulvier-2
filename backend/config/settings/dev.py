import os

from corsheaders.defaults import default_headers

from . import base as base_settings

for setting_name in dir(base_settings):
    if setting_name.isupper():
        globals()[setting_name] = getattr(base_settings, setting_name)

REST_FRAMEWORK = globals().get("REST_FRAMEWORK", {})
INSTALLED_APPS = list(globals().get("INSTALLED_APPS", []))
MIDDLEWARE = list(globals().get("MIDDLEWARE", []))

DEBUG = True
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "").split(",") if host.strip()]


REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework_xml.renderers.XMLRenderer",
        "rest_framework_yaml.renderers.YAMLRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.core.throttles.PublicKeyMinuteThrottle",
        "apps.core.throttles.PublicKeyHourThrottle",
        "apps.core.throttles.InternalKeyThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "internal": None,
        "public_min": None,
        "public_hour": None,
    },
}

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa
INTERNAL_IPS = ["127.0.0.1"]

INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", *MIDDLEWARE]
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
CORS_ALLOW_HEADERS = [*default_headers, "x-api-key"]
