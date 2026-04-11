"""ViewSets for the Media Files app."""

from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.serializers import BaseSerializer

from apps.core.views import ApiModelViewSet

from .filters import MediaFileFilter
from .models import MediaFile
from .schemas import media_file_schema
from .serializers import MediaFileSerializer, MediaFileUploadSerializer

_MEDIA = "Media Files"


@extend_schema(tags=[_MEDIA])
@media_file_schema
class MediaFileViewSet(ApiModelViewSet):
    """CRUD endpoints for uploaded media files."""

    queryset = MediaFile.objects.select_related("uploaded_by").order_by("-created_at")
    serializer_class = MediaFileSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_class = MediaFileFilter
    ordering_fields = ["id", "created_at", "size_bytes", "mime_type", "file_type"]
    ordering = ["-created_at"]
    search_fields = ["filename", "mime_type", "uploaded_by__username"]

    def get_serializer_class(self) -> type[BaseSerializer]:
        """Return the upload serializer for create and the read serializer otherwise."""
        if getattr(self, "action", None) == "create":
            return MediaFileUploadSerializer
        return MediaFileSerializer
