from .base import *  # noqa: F403, F401

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


REST_FRAMEWORK = {
    **REST_FRAMEWORK, # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

<<<<<<< HEAD
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa
INTERNAL_IPS = ["127.0.0.1"]
=======
INSTALLED_APPS += ["debug_toolbar"] # noqa: F405
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"] # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]
>>>>>>> bc697e9 (chore: re-added mistakes)
