"""
URL configuration for the API app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.languages.views import LanguageViewSet
from apps.tags.views import TagViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()

# TODO register viewsets here
router.register(r'languages', LanguageViewSet, basename='language')
router.register(r'tags', TagViewSet, basename='tag')
#router.register(r'productions', ProductionViewSet, basename='production')
#router.register("events", EventViewSet, basename="event")
#router.register("locations", LocationViewSet, basename="location")
#router.register("halls", HallViewSet, basename="hall")
#router.register("genres", GenreViewSet, basename="genre")
#router.register("prices", PriceViewSet, basename="price")
#router.register("price-ranks", PriceRankViewSet, basename="price-rank")
#router.register("import-logs", ImportLogViewSet, basename="import-log")

urlpatterns = [
    path('', include(router.urls)), # Include the router URLs
    path('schema/', SpectacularAPIView.as_view(), name='schema'), # API schema view
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), # API documentation view
]