"""ViewSets for the Media Files app."""

from drf_spectacular.utils import extend_schema

from apps.core.views import ApiModelViewSet

from .filters import MediaFileFilter
from .models import MediaFile
from .schemas import media_file_schema
from .serializers import MediaFileSerializer, MediaFileUploadSerializer

_MEDIA = "Media Files"


@extend_schema(tags=[_MEDIA])
@media_file_schema
class MediaFileViewSet(ApiModelViewSet):
    queryset = MediaFile.objects.select_related("uploaded_by").order_by("-created_at")
    serializer_class = MediaFileSerializer
    filterset_class = MediaFileFilter
    ordering_fields = ["id", "created_at", "size_bytes", "mime_type", "file_type"]
    ordering = ["-created_at"]
    search_fields = ["original_name", "mime_type"]

    def get_serializer_class(self):
        if getattr(self, "action", None) == "create":
            return MediaFileUploadSerializer
        return MediaFileSerializer
    