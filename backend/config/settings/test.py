from . import base as base_settings

for setting_name in dir(base_settings):
    if setting_name.isupper():
        globals()[setting_name] = getattr(base_settings, setting_name)

REST_FRAMEWORK = globals().get("REST_FRAMEWORK", {})

# Test settings for the Django project. These settings are used when running tests.

# Use an in-memory SQLite database for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Test settings: throttling is disabled to avoid interference with test cases
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],  # No throttling during tests
    "DEFAULT_THROTTLE_RATES": {
        "internal": None,
        "public_min": "1/minute",
        "public_hour": None,
        "public": None,
    },
}
