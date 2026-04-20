"""ViewSets for the Media Files app."""

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.serializers import BaseSerializer

from apps.core.views import ApiModelViewSet

from .filters import MediaFileFilter
from .models import MediaFile, MediaFileTranslation
from .schemas import media_file_schema
from .serializers import MediaFileSerializer, MediaFileUploadSerializer

_MEDIA = "Media Files"


@extend_schema(tags=[_MEDIA])
@media_file_schema
class MediaFileViewSet(ApiModelViewSet):
    """CRUD endpoints for uploaded media files."""

    queryset = MediaFile.objects.prefetch_related(
        Prefetch(
            "translations",
            queryset=MediaFileTranslation.objects.select_related("language"),
        )
    ).order_by("-created_at")
    serializer_class = MediaFileSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_class = MediaFileFilter
    ordering_fields = ["created_at", "size_bytes", "file_type"]
    ordering = ["-created_at"]
    search_fields = ["filename", "translations__description", "mime_type"]

    def get_serializer_class(self) -> type[BaseSerializer]:
        """Return the write serializer for create/update actions and read serializer otherwise."""
        if getattr(self, "action", None) in {"create", "update", "partial_update"}:
            return MediaFileUploadSerializer
        return MediaFileSerializer
