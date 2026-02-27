from .models import ImportLog
from .serializers import ImportLogSerializer
from apps.core.views import ApiReadOnlyViewSet

class ImportLogViewSet(ApiReadOnlyViewSet):
    """
    Read-only API endpoint for monitoring ImportLog records.

    Behavior:
        - Public API key  -> allowed (read-only by design)
        - Internal API key -> allowed (read-only by design)
        - No valid key     -> 401 / 403

    Write operations (POST, PUT, PATCH, DELETE) are intentionally
    not supported. Import logs are managed exclusively by the
    import pipeline, never via the API.

    Results are ordered from most recent to oldest via the
    model's default ordering ('-started_at').
    """

    queryset = ImportLog.objects.all()
    serializer_class = ImportLogSerializer