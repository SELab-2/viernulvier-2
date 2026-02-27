"""
URL configuration for the API app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.pricing.views import PriceViewSet, PriceRankViewSet
from apps.languages.views import LanguageViewSet
from apps.media_library.views import MediaGalleryViewSet, MediaItemViewSet
from apps.import_log.views import ImportLogViewSet
from apps.tags.views import TagViewSet
from apps.productions.views import ProductionViewSet
from apps.genres.views import GenreUseAsViewSet, GenreViewSet
from apps.locations.views import HallViewSet, LocationViewSet, SpaceViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()

# TODO register viewsets here
router.register(r'languages', LanguageViewSet, basename='language')
router.register(r'media-galleries', MediaGalleryViewSet, basename='media-gallery')
router.register(r'media-items', MediaItemViewSet, basename='media-item')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'productions', ProductionViewSet, basename='production')
router.register(r"genre-use-as", GenreUseAsViewSet, basename="genre-use-as")
router.register(r"genres", GenreViewSet, basename="genre")
#router.register("events", EventViewSet, basename="event")
router.register(r"import-logs", ImportLogViewSet, basename="import-log")
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"spaces", SpaceViewSet, basename="space")
router.register(r"halls", HallViewSet, basename="hall")
router.register(r"prices", PriceViewSet, basename="price")
router.register(r"price-ranks", PriceRankViewSet, basename="price-rank")

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # API schema view
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # OpenAPI documentation
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Redoc documentation
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]