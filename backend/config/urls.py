"""
Root URL configuration for the viernulvier_archive project.

All API routes are delegated to ``api.urls``. The health check endpoint
sits at the root level so it is always reachable, even when the API
prefix changes.

Debug toolbar and static media serving are only active when ``DEBUG``
is ``True`` - they must never be enabled in production.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .health import health

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
        *urlpatterns,
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    ]
