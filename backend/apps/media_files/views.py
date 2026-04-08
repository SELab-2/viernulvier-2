"""ViewSets for the Media Files app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.

Media files represent uploaded assets such as images (posters) and PDFs
(brochures, documents). Each file stores metadata such as MIME type,
file size, and uploader.
"""

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
    """CRUD endpoints for MediaFile objects.

    Media files are uploaded assets such as images and PDF documents.

    Filtering
    ---------
    ``?file_type=pdf``
        Exact match on normalized file type (e.g. `pdf`, `image`).
    ``?mime_type=application/pdf``
        Exact match on MIME type.
    ``?original_name=poster``
        Case-insensitive substring match on original filename.
    ``?uploaded_by=7``
        Exact match on uploader user id.
    ``?external_id=abc``
        Exact match on external identifier.

    Ordering
    --------
    ``?ordering=created_at`` / ``?ordering=-created_at``
        Order by upload timestamp.
    ``?ordering=size_bytes`` / ``?ordering=-size_bytes``
        Order by file size.
    ``?ordering=id`` / ``?ordering=-id``
        Order by identifier.

    Search
    ------
    ``?search=poster``
        Full-text search across original filename and MIME type.
    """

    queryset = MediaFile.objects.select_related("uploaded_by").order_by("-created_at")

    filterset_class = MediaFileFilter

    ordering_fields = ["id", "created_at", "size_bytes", "mime_type", "file_type"]
    ordering = ["-created_at"]

    search_fields = ["original_name", "mime_type"]

    def get_serializer_class(self):
        """Use a dedicated serializer for uploads (POST)."""
        if self.action == "create":
            return MediaFileUploadSerializer
        return MediaFileSerializer
    