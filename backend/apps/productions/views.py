from django.db.models import Prefetch
from apps.core.views import ApiModelViewSet
from .models import Production, ProductionGenre
from .serializers import ProductionSerializer


class ProductionViewSet(ApiModelViewSet):
    """
    API endpoint for managing Productions.

    Behavior:
        - Public API key  -> read-only
        - Internal API key -> full CRUD

    Fully optimized to prevent N+1 queries.
    """

    serializer_class = ProductionSerializer

    queryset = (
        Production.objects
        .select_related(
            "uit_database_theme",
            "uit_database_type",
        )
        .prefetch_related(
            "translations__language",
            "tags",
            "tags__translations__language",
            Prefetch(
                "productiongenre_set",
                queryset=ProductionGenre.objects
                    .select_related("genre")
                    .order_by("position"),
                to_attr="prefetched_production_genres",
            ),
        )
    )