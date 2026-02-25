from rest_framework.viewsets import ModelViewSet
from apps.core.permissions import HasPublicApiKey, HasInternalApiKey
from .models import Production
from .serializers import ProductionSerializer


class ProductionViewSet(ModelViewSet):
    """
    API endpoint for managing Productions.

    Behavior:
        - Public API key  -> read-only
        - Internal API key -> full CRUD

    Optimized with prefetch_related to avoid N+1 queries
    when accessing translations.
    """

    queryset = Production.objects.prefetch_related(
        'translations', 
        'tags', 
        'uit_database_theme', 
        'uit_database_type'
    ).all()
    serializer_class = ProductionSerializer