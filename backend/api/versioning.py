"""
API versioning for the viernulvier_archive project.

Uses URL path versioning so the version is explicit in every request,
visible in logs, and cacheable by CDNs without special header config.

Supported versions
------------------
v1  - current stable version

Adding a new version
--------------------
1. Add the version string to ``ALLOWED_VERSIONS``.
2. Register a new ``include()`` block in ``api/urls.py``.
3. Override only the viewsets that change; unchanged resources keep
   pointing at the same view class.
4. Bump ``DEFAULT_VERSION`` once v2 becomes the stable default.
"""

API_VERSION_V1 = "v1"

ALLOWED_API_VERSIONS = [API_VERSION_V1]
DEFAULT_API_VERSION = API_VERSION_V1

VERSIONING_SETTINGS = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": DEFAULT_API_VERSION,
    "ALLOWED_VERSIONS": ALLOWED_API_VERSIONS,
    "VERSION_PARAM": "version",
}
