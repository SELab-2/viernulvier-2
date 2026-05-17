"""OpenAPI schema decorators and examples for the Tags app."""

from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view

from apps.core.openapi import (
    DELETE_ERRORS,
    ITEM_ERRORS,
    MUTATE_ERRORS,
    READ_ERRORS,
    RESPONSE_204_DELETED,
    WRITE_ERRORS,
)

from .serializers import TagSerializer

# ===========================================================================
# Tag - examples
# ===========================================================================

_TAG_RESPONSE = OpenApiExample(
    "Tag - response",
    summary="A tag with localised fields and optional image",
    value={
        "id": 12,
        "url": "https://example.com/tags/hedendaags",
        "source": "uitdatabank",
        "type": "theme",
        "is_enabled": True,
        "image": "/media/tag_images/hedendaags.jpg",
        "display_name": "Contemporary",
        "display_short_description": "Contemporary performing arts and theatre.",
        "display_excerpt": "Contemporary arts overview.",
        "display_url_title": "contemporary",
        "first_production_start": "2024-01-01T19:00:00Z",
        "last_production_end": "2024-12-31T22:00:00Z",
        "name": "Contemporary",
        "short_description": "Contemporary performing arts and theatre.",
        "excerpt": "Contemporary arts overview.",
        "url_title": "contemporary",
    },
    response_only=True,
)

_TAG_INTERNAL_RESPONSE = OpenApiExample(
    "Tag - internal (system) response",
    summary="A tag created internally without an external source (image fallback example)",
    value={
        "id": 5,
        "url": "",
        "source": "",
        "type": "audience",
        "is_enabled": True,
        "image": "/media/productions/most-recent-image.jpg",
        "display_name": "Family friendly",
        "display_short_description": None,
        "display_excerpt": None,
        "display_url_title": "family-friendly",
        "first_production_start": None,
        "last_production_end": None,
        "name": "Family friendly",
        "short_description": None,
        "excerpt": None,
        "url_title": "family-friendly",
    },
    response_only=True,
)

_TAG_INPUT = OpenApiExample(
    "Tag - request body",
    summary="Payload for creating a new tag",
    value={
        "url": "",
        "source": "",
        "type": "audience",
        "is_enabled": True,
    },
    request_only=True,
)

_TAG_PARTIAL_INPUT = OpenApiExample(
    "Tag - partial request body",
    summary="Only the fields you want to change",
    value={"is_enabled": False},
    request_only=True,
)


# ===========================================================================
# Tag - per-action schemas
# ===========================================================================

_TAG_LIST = extend_schema(
    summary="List all tags",
    description=(
        "Returns a paginated list of all **Tag** objects ordered by `id`.\n\n"
        "The `image` field contains the uploaded image for the tag, or if not set, the image of the most recent production using this tag (if available).\n\n"
        "Translated fields (`name`, `excerpt`, `short_description`, `url_title`) are "
        "returned as language-code dictionaries "
        '(e.g. {"en": "Contemporary", "fr": "Contemporain"}).'
    ),
    responses={200: TagSerializer, **READ_ERRORS},
    examples=[_TAG_RESPONSE, _TAG_INTERNAL_RESPONSE],
)

_TAG_RETRIEVE = extend_schema(
    summary="Retrieve a tag",
    description=(
        "Returns the full representation of a single **Tag**.\n\n"
        "The `image` field contains the uploaded image for the tag, or if not set, the image of the most recent production using this tag (if available).\n\n"
        "Translated fields are returned as language-code dictionaries "
        '(e.g. {"en": "Contemporary", "fr": "Contemporain"}).'
    ),
    responses={200: TagSerializer, **ITEM_ERRORS},
    examples=[_TAG_RESPONSE],
)

_TAG_CREATE = extend_schema(
    summary="Create a tag",
    description=(
        "Creates a new **Tag**.\n\n"
        "- `type` is used as a classification label (e.g. `theme`, `audience`).\n"
        "- Localised fields (`name`, `excerpt`, `short_description`, `url_title`) must be added "
        "via the **Tag Translation** endpoints after creation.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=TagSerializer,
    responses={201: TagSerializer, **WRITE_ERRORS},
    examples=[_TAG_INPUT, _TAG_RESPONSE],
)

_TAG_UPDATE = extend_schema(
    summary="Replace a tag",
    description=(
        "Fully replaces an existing **Tag**. All writable fields must be supplied.\n\n> **Requires an internal API key.**"
    ),
    request=TagSerializer,
    responses={200: TagSerializer, **MUTATE_ERRORS},
    examples=[_TAG_INPUT, _TAG_RESPONSE],
)

_TAG_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a tag",
    description=(
        "Updates one or more fields of an existing **Tag** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=TagSerializer,
    responses={200: TagSerializer, **MUTATE_ERRORS},
    examples=[_TAG_PARTIAL_INPUT, _TAG_RESPONSE],
)

_TAG_DESTROY = extend_schema(
    summary="Delete a tag",
    description=(
        "Permanently removes a **Tag** from the system.\n\n"
        "> **Warning:** All associated translations and links to productions are "
        "also deleted. This action is irreversible.\n\n"
        "> **Requires an internal API key.**"
    ),
    responses={204: RESPONSE_204_DELETED, **DELETE_ERRORS},
)


# ===========================================================================
# Assembled decorator - imported and applied in views.py
# ===========================================================================

tag_schema = extend_schema_view(
    list=_TAG_LIST,
    retrieve=_TAG_RETRIEVE,
    create=_TAG_CREATE,
    update=_TAG_UPDATE,
    partial_update=_TAG_PARTIAL_UPDATE,
    destroy=_TAG_DESTROY,
)
