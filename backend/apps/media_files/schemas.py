"""OpenAPI schema decorators for the Media Files app."""

from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view

from apps.core.openapi import (
    DELETE_ERRORS,
    ITEM_ERRORS,
    READ_ERRORS,
    RESPONSE_204_DELETED,
    WRITE_ERRORS,
)

from .serializers import MediaFileSerializer, MediaFileUploadSerializer

# ===========================================================================
# MediaFile - examples
# ===========================================================================

_MEDIA_FILE_RESPONSE = OpenApiExample(
    "Media file - response",
    summary="A stored media file",
    value={
        "id": "4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3",
        "external_id": None,
        "file": "/media/uploads/4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3.pdf",
        "original_name": "season-brochure-2026.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 2843921,
        "file_type": "pdf",
        "uploaded_by": 7,
        "created_at": "2026-04-08T10:12:00Z",
    },
    response_only=True,
)

_MEDIA_FILE_IMAGE_RESPONSE = OpenApiExample(
    "Media file - image response",
    summary="An uploaded poster image",
    value={
        "id": "9a7a3b8a-3bb6-4179-a52d-4f0a8fa9d921",
        "external_id": None,
        "file": "/media/uploads/9a7a3b8a-3bb6-4179-a52d-4f0a8fa9d921.png",
        "original_name": "poster-premiere.png",
        "mime_type": "image/png",
        "size_bytes": 918273,
        "file_type": "image",
        "uploaded_by": 7,
        "created_at": "2026-04-08T10:18:00Z",
    },
    response_only=True,
)

_MEDIA_FILE_INPUT = OpenApiExample(
    "Media file - request body",
    summary="Multipart upload payload for a new media file",
    value={
        "file": "<binary file>",
    },
    request_only=True,
)


# ===========================================================================
# MediaFile - per-action schemas
# ===========================================================================

_MEDIA_FILE_LIST = extend_schema(
    summary="List all media files",
    description=(
        "Returns a paginated list of all **MediaFile** objects ordered by newest first.\n\n"
        "Use this endpoint to populate the media overview page for posters, brochures, "
        "and other print materials."
    ),
    responses={200: MediaFileSerializer, **READ_ERRORS},
    examples=[_MEDIA_FILE_RESPONSE, _MEDIA_FILE_IMAGE_RESPONSE],
)

_MEDIA_FILE_RETRIEVE = extend_schema(
    summary="Retrieve a media file",
    description=(
        "Returns the full representation of a single **MediaFile** object, "
        "including its stored file URL and metadata."
    ),
    responses={200: MediaFileSerializer, **ITEM_ERRORS},
    examples=[_MEDIA_FILE_RESPONSE],
)

_MEDIA_FILE_CREATE = extend_schema(
    summary="Upload a media file",
    description=(
        "Uploads a new **MediaFile**.\n\n"
        "Supported file types:\n"
        "- JPEG\n"
        "- PNG\n"
        "- WEBP\n"
        "- PDF\n\n"
        "The backend derives and stores metadata such as the original filename, "
        "MIME type, file size, and normalized internal file type.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=MediaFileUploadSerializer,
    responses={201: MediaFileSerializer, **WRITE_ERRORS},
    examples=[_MEDIA_FILE_INPUT, _MEDIA_FILE_RESPONSE],
)

_MEDIA_FILE_DESTROY = extend_schema(
    summary="Delete a media file",
    description=(
        "Permanently removes a **MediaFile** from the system.\n\n"
        "> **Warning:** This also removes the underlying stored file. "
        "This action is irreversible.\n\n"
        "> **Requires an internal API key.**"
    ),
    responses={204: RESPONSE_204_DELETED, **DELETE_ERRORS},
)


# ===========================================================================
# Assembled decorator - imported and applied in views.py
# ===========================================================================

media_file_schema = extend_schema_view(
    list=_MEDIA_FILE_LIST,
    retrieve=_MEDIA_FILE_RETRIEVE,
    create=_MEDIA_FILE_CREATE,
    destroy=_MEDIA_FILE_DESTROY,
)
