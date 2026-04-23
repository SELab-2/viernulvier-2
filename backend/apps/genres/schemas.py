"""
OpenAPI schema decorators for the Genre app.
"""

from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view

from apps.core.openapi import (
    DELETE_ERRORS,
    ITEM_ERRORS,
    MUTATE_ERRORS,
    READ_ERRORS,
    RESPONSE_204_DELETED,
    WRITE_ERRORS,
)

from .serializers import GenreSerializer

# ===========================================================================
# Genre - examples
# ===========================================================================

_GENRE_RESPONSE_MULTILINGUAL = OpenApiExample(
    "Genre - Multilingual Response",
    summary="Example of a genre with all available translations",
    value={
        "id": 10,
        "vendor_id": "theater-123",
        "type": "theater",
        "name": {"nl": "Theater", "en": "Theatre", "fr": "Théâtre"},
    },
    response_only=True,
)

_GENRE_INPUT = OpenApiExample(
    "Genre - request body",
    summary="Payload for creating a new genre",
    description=("Only `type` is required. Localised names are added via the translation endpoints after creation."),
    value={"type": "contemporary_dance", "vendor_id": "theater-123"},
    request_only=True,
)

_GENRE_PARTIAL_INPUT = OpenApiExample(
    "Genre - partial request body",
    summary="Only the fields you want to change",
    value={"vendor_id": "theater-123"},
    request_only=True,
)


# ===========================================================================
# Genre - per-action schemas
# ===========================================================================

_GENRE_LIST = extend_schema(
    summary="List all genres",
    description="Returns a paginated list of all **Genre** objects.",
    responses={200: GenreSerializer, **READ_ERRORS},
    examples=[_GENRE_RESPONSE_MULTILINGUAL],
)

_GENRE_RETRIEVE = extend_schema(
    summary="Retrieve a genre",
    description=(
        "Returns the full representation of a single **Genre** identified "
        "by its primary key, including its technical type "
        "and localised display name."
    ),
    responses={200: GenreSerializer, **ITEM_ERRORS},
    examples=[_GENRE_RESPONSE_MULTILINGUAL],
)

_GENRE_CREATE = extend_schema(
    summary="Create a genre",
    description=(
        "Creates a new **Genre** in the archive.\n\n"
        "- The `type` field is an internal technical identifier and must "
        "use `snake_case` (e.g. `contemporary_dance`, `festival`).\n"
        "- Localised display names must be added via the **Genre Translation** "
        "endpoints after the genre has been created.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=GenreSerializer,
    responses={201: GenreSerializer, **WRITE_ERRORS},
    examples=[_GENRE_INPUT, _GENRE_RESPONSE_MULTILINGUAL],
)

_GENRE_UPDATE = extend_schema(
    summary="Replace a genre",
    description=(
        "Fully replaces an existing **Genre**. All writable fields must be supplied.\n\n> **Requires an internal API key.**"
    ),
    request=GenreSerializer,
    responses={200: GenreSerializer, **MUTATE_ERRORS},
    examples=[_GENRE_INPUT, _GENRE_RESPONSE_MULTILINGUAL],
)

_GENRE_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a genre",
    description=(
        "Updates one or more fields of an existing **Genre** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=GenreSerializer,
    responses={200: GenreSerializer, **MUTATE_ERRORS},
    examples=[_GENRE_PARTIAL_INPUT, _GENRE_RESPONSE_MULTILINGUAL],
)

_GENRE_DESTROY = extend_schema(
    summary="Delete a genre",
    description=(
        "Permanently removes a **Genre** from the archive.\n\n"
        "> **Warning:** All associated translations are also deleted, "
        "and linked productions may be affected. This action is irreversible.\n\n"
        "> **Requires an internal API key.**"
    ),
    responses={204: RESPONSE_204_DELETED, **DELETE_ERRORS},
)


# ===========================================================================
# Assembled decorators - imported and applied in views.py
# ===========================================================================

genre_schema = extend_schema_view(
    list=_GENRE_LIST,
    retrieve=_GENRE_RETRIEVE,
    create=_GENRE_CREATE,
    update=_GENRE_UPDATE,
    partial_update=_GENRE_PARTIAL_UPDATE,
    destroy=_GENRE_DESTROY,
)
