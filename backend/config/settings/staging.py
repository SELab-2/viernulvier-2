from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

CSRF_TRUSTED_ORIGINS = [
    f"http://{host.strip()}" for host in ALLOWED_HOSTS if host.strip()
]
