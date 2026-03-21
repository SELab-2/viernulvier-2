"""
URL configuration for the viernulvier_archive API (v1).

All viewsets are registered on a single ``DefaultRouter``. The router
generates the standard list / detail URL pairs for every resource.

Schema and documentation endpoints are versioned alongside the API so
that clients always access the docs that match the version they are
calling.

    /api/v1/          - browsable resource index (router root)
    /api/schema/      - raw OpenAPI 3 schema (YAML)
    /api/docs/        - Swagger UI
    /api/redoc/       - ReDoc UI
"""

from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from apps.events.views import EventViewSet
from apps.genres.views import GenreUseAsViewSet, GenreViewSet
from apps.import_log.views import ImportLogViewSet
from apps.languages.views import LanguageViewSet
from apps.locations.views import HallViewSet, LocationViewSet, SpaceViewSet
from apps.media_library.views import MediaGalleryViewSet, MediaItemViewSet
from apps.pricing.views import PriceRankViewSet, PriceViewSet
from apps.productions.views import ProductionViewSet
from apps.tags.views import TagViewSet

router = DefaultRouter()

# Reference / taxonomy resources
router.register(r"languages", LanguageViewSet, basename="language")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"genres", GenreViewSet, basename="genre")
router.register(r"genre-use-as", GenreUseAsViewSet, basename="genre-use-as")
router.register(r"price-ranks", PriceRankViewSet, basename="price-rank")
router.register(r"prices", PriceViewSet, basename="price")

# Location hierarchy
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"spaces", SpaceViewSet, basename="space")
router.register(r"halls", HallViewSet, basename="hall")

# Core content
router.register(r"productions", ProductionViewSet, basename="production")
router.register(r"events", EventViewSet, basename="event")

# Media
router.register(r"media-galleries", MediaGalleryViewSet, basename="media-gallery")
router.register(r"media-items", MediaItemViewSet, basename="media-item")

# Import pipeline
router.register(r"import-logs", ImportLogViewSet, basename="import-log")

urlpatterns = [
    path("v1/", include(router.urls)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
