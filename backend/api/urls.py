"""
URL configuration for the viernulvier_archive API.

Structure
---------
/api/v1/      - current stable API
/api/schema/  - raw OpenAPI 3 schema (YAML)
/api/docs/    - Swagger UI
/api/redoc/   - ReDoc UI

Adding v2
---------
1. Create ``api/v2/urls.py`` with a new router that registers only the
   viewsets that changed. Import unchanged viewsets from v1 directly.
2. Add ``path("v2/", include(("api.v2.urls", "v2"), namespace="v2"))``
   below the v1 include.
3. Add ``"v2"`` to ``ALLOWED_API_VERSIONS`` in ``api/versioning.py``.
"""

from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("v1/", include(("api.v1.urls", "v1"), namespace="v1")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
