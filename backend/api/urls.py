"""
URL configuration for the API app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Create a router and register our viewsets with it.
router = DefaultRouter() 

urlpatterns = [
    path('', include(router.urls)), # Include the router URLs
    path('schema/', SpectacularAPIView.as_view(), name='schema'), # API schema view
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), # API documentation view