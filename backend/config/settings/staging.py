import os

from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

CSRF_TRUSTED_ORIGINS = [f"http://{host.strip()}" for host in ALLOWED_HOSTS if host.strip()]
