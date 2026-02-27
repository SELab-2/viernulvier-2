"""
URL configuration for the API app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.pricing.views import PriceViewSet, PriceRankViewSet
from apps.languages.views import LanguageViewSet
from apps.genres.views import GenreUseAsViewSet, GenreViewSet
from apps.locations.views import HallViewSet, LocationViewSet, SpaceViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()

# TODO register viewsets here
router.register(r"languages", LanguageViewSet, basename="language")
router.register(r"genre-use-as", GenreUseAsViewSet, basename="genre-use-as")
router.register(r"genres", GenreViewSet, basename="genre")
#router.register(r'productions', ProductionViewSet, basename='production')
#router.register("events", EventViewSet, basename="event")
router.register("locations", LocationViewSet, basename="location")
router.register("spaces", SpaceViewSet, basename="space")
router.register("halls", HallViewSet, basename="hall")
#router.register("tags", TagViewSet, basename="tag")
router.register("prices", PriceViewSet, basename="price")
router.register("price-ranks", PriceRankViewSet, basename="price-rank")
#router.register("import-logs", ImportLogViewSet, basename="import-log")

urlpatterns = [
    path('', include(router.urls)), # Include the router URLs
    path('schema/', SpectacularAPIView.as_view(), name='schema'), # API schema view
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), # API documentation view
]