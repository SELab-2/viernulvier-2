"""
OpenAPI schema decorators for the Media app.

Keeping all drf-spectacular annotations here means views.py stays focused
on routing logic only. Each action is defined as a private variable and
assembled into two `extend_schema_view` decorators at the bottom of the file.
"""

from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
)

from apps.core.openapi import (
    RESPONSE_204_DELETED,
    RESPONSE_400,
    RESPONSE_401,
    RESPONSE_403,
    RESPONSE_404,
)

from .serializers import MediaGallerySerializer, MediaItemSerializer

# ===========================================================================
# Shared nested examples
# ===========================================================================

_CROP_EXAMPLE = {
    "id": 1,
    "name": "hd_ready",
    "image_url": "https://cdn.example.com/media/crops/2024/01/hd_ready.jpg",
}

_MEDIA_ITEM_EXAMPLE = {
    "id": 1,
    "gallery": {
        "id": 1,
        "name": "Production Images 2024",
    },
    "type": "foto",
    "format": "image/jpeg",
    "original_filename": "poster_nl.jpg",
    "position": 0,
    "width": 1920,
    "height": 1080,
    "title": {"nl": "Affiche", "en": "Poster", "fr": "Affiche"},
    "description": {
        "nl": "De officiële affiche.",
        "en": "The official poster.",
        "fr": "L'affiche officielle.",
    },
    "credits": {
        "nl": "Foto: Jan Janssen",
        "en": "Photo: Jan Janssen",
        "fr": "Photo : Jan Janssen",
    },
    "link": {"nl": "", "en": "", "fr": ""},
    "crops": [_CROP_EXAMPLE],
}


# ===========================================================================
# MediaGallery - examples
# ===========================================================================

_GALLERY_RESPONSE = OpenApiExample(
    "MediaGallery - response",
    summary="A gallery with nested media items",
    value={
        "id": 1,
        "name": "Production Images 2024",
        "media_items": [_MEDIA_ITEM_EXAMPLE],
    },
    response_only=True,
)

_GALLERY_INPUT = OpenApiExample(
    "MediaGallery - request body",
    summary="Payload for creating a new gallery",
    value={"name": "Production Images 2024"},
    request_only=True,
)

_GALLERY_PARTIAL_INPUT = OpenApiExample(
    "MediaGallery - partial request body",
    summary="Only the fields you want to change",
    value={"name": "Production Images 2025"},
    request_only=True,
)


# ===========================================================================
# MediaGallery - per-action schemas
# ===========================================================================

_GALLERY_LIST = extend_schema(
    summary="List all media galleries",
    description=(
        "Returns a paginated list of all **MediaGallery** objects.\n\n"
        "Each gallery includes its full nested list of media items with "
        "translated metadata represented as language-code dictionaries "
        '(e.g. {"en": "Poster", "fr": "Affiche"}) and crop variants.'
    ),
    responses={
        200: MediaGallerySerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_GALLERY_RESPONSE],
)

_GALLERY_RETRIEVE = extend_schema(
    summary="Retrieve a media gallery",
    description=(
        "Returns the full representation of a single **MediaGallery** "
        "identified by its primary key, including all nested media items "
        "with localised metadata and crop variants."
    ),
    responses={
        200: MediaGallerySerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_GALLERY_RESPONSE],
)

_GALLERY_CREATE = extend_schema(
    summary="Create a media gallery",
    description=(
        "Creates a new **MediaGallery**.\n\n"
        "After creation, add media items via the **Media Item** endpoints.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=MediaGallerySerializer,
    responses={
        201: MediaGallerySerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_GALLERY_INPUT, _GALLERY_RESPONSE],
)

_GALLERY_UPDATE = extend_schema(
    summary="Replace a media gallery",
    description=(
        "Fully replaces an existing **MediaGallery**. "
        "All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=MediaGallerySerializer,
    responses={
        200: MediaGallerySerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_GALLERY_INPUT, _GALLERY_RESPONSE],
)

_GALLERY_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a media gallery",
    description=(
        "Updates one or more fields of an existing **MediaGallery** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=MediaGallerySerializer,
    responses={
        200: MediaGallerySerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_GALLERY_PARTIAL_INPUT, _GALLERY_RESPONSE],
)

_GALLERY_DESTROY = extend_schema(
    summary="Delete a media gallery",
    description=(
        "Permanently removes a **MediaGallery** from the archive.\n\n"
        "> **Warning:** All associated media items, their translations, and "
        "their crop variants are also deleted. This action is irreversible.\n\n"
        "> **Requires an internal API key.**"
    ),
    responses={
        204: RESPONSE_204_DELETED,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
)


# ===========================================================================
# MediaItem - examples
# ===========================================================================

_ITEM_RESPONSE = OpenApiExample(
    "MediaItem - response",
    summary="A media item with localised metadata and crops",
    value=_MEDIA_ITEM_EXAMPLE,
    response_only=True,
)

_ITEM_INPUT = OpenApiExample(
    "MediaItem - request body",
    summary="Payload for creating a new media item",
    description=(
        "`gallery_id` and `type` are required. Localised metadata is added via the translation endpoints after creation."
    ),
    value={
        "gallery_id": 1,
        "type": "foto",
        "format": "image/jpeg",
        "original_filename": "poster_nl.jpg",
        "position": 0,
        "width": 1920,
        "height": 1080,
    },
    request_only=True,
)

_ITEM_PARTIAL_INPUT = OpenApiExample(
    "MediaItem - partial request body",
    summary="Only the fields you want to change",
    value={"position": 2},
    request_only=True,
)


# ===========================================================================
# MediaItem - per-action schemas
# ===========================================================================

_ITEM_LIST = extend_schema(
    summary="List all media items",
    description=(
        "Returns a paginated list of all **MediaItem** objects across all galleries.\n\n"
        "Each item includes its translated metadata as language-code dictionaries "
        '(e.g. {"en": "Poster", "fr": "Affiche"}) and all pre-rendered crop variants.'
    ),
    responses={
        200: MediaItemSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_ITEM_RESPONSE],
)

_ITEM_RETRIEVE = extend_schema(
    summary="Retrieve a media item",
    description=(
        "Returns the full representation of a single **MediaItem** identified "
        "by its primary key, including localised metadata and all crop variants."
    ),
    responses={
        200: MediaItemSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_ITEM_RESPONSE],
)

_ITEM_CREATE = extend_schema(
    summary="Create a media item",
    description=(
        "Creates a new **MediaItem** within an existing gallery.\n\n"
        "- `gallery_id` (FK) and `type` are required.\n"
        "- Localised metadata (`title`, `description`, `credits`, `link`) must be "
        "  added via the **Media Item Translation** endpoints after creation.\n"
        "- Crop variants are populated automatically by the scraper sync pipeline.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=MediaItemSerializer,
    responses={
        201: MediaItemSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_ITEM_INPUT, _ITEM_RESPONSE],
)

_ITEM_UPDATE = extend_schema(
    summary="Replace a media item",
    description=(
        "Fully replaces an existing **MediaItem**. "
        "All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=MediaItemSerializer,
    responses={
        200: MediaItemSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_ITEM_INPUT, _ITEM_RESPONSE],
)

_ITEM_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a media item",
    description=(
        "Updates one or more fields of an existing **MediaItem** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=MediaItemSerializer,
    responses={
        200: MediaItemSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_ITEM_PARTIAL_INPUT, _ITEM_RESPONSE],
)

_ITEM_DESTROY = extend_schema(
    summary="Delete a media item",
    description=(
        "Permanently removes a **MediaItem** from the archive.\n\n"
        "> **Warning:** All associated translations and crop variants are also "
        "deleted. This action is irreversible.\n\n"
        "> **Requires an internal API key.**"
    ),
    responses={
        204: RESPONSE_204_DELETED,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
)


# ===========================================================================
# Assembled decorators - imported and applied in views.py
# ===========================================================================

media_gallery_schema = extend_schema_view(
    list=_GALLERY_LIST,
    retrieve=_GALLERY_RETRIEVE,
    create=_GALLERY_CREATE,
    update=_GALLERY_UPDATE,
    partial_update=_GALLERY_PARTIAL_UPDATE,
    destroy=_GALLERY_DESTROY,
)

media_item_schema = extend_schema_view(
    list=_ITEM_LIST,
    retrieve=_ITEM_RETRIEVE,
    create=_ITEM_CREATE,
    update=_ITEM_UPDATE,
    partial_update=_ITEM_PARTIAL_UPDATE,
    destroy=_ITEM_DESTROY,
)
