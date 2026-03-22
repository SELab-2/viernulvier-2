"""
ASGI config for the viernulvier_archive project.

Exposes the ASGI callable as ``application``. Used by ASGI servers such
as Uvicorn or Daphne.

The settings module defaults to ``config.settings.prod``. Override with
the ``DJANGO_SETTINGS_MODULE`` environment variable when running locally
or in tests.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()
