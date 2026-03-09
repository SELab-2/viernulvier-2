"""
OpenAPI schema decorators for the Genre app.

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
    RESPONSE_400,
    RESPONSE_401,
    RESPONSE_403,
    RESPONSE_404,
    RESPONSE_204_DELETED,
)
from .serializers import GenreSerializer, GenreUseAsSerializer


# ===========================================================================
# GenreUseAs — examples
# ===========================================================================

_USE_AS_RESPONSE = OpenApiExample(
    "GenreUseAs — response",
    summary="A usage-context object",
    value={"id": 1, "name": "genre"},
    response_only=True,
)

_USE_AS_INPUT = OpenApiExample(
    "GenreUseAs — request body",
    summary="Payload for creating or updating a usage context",
    value={"name": "category"},
    request_only=True,
)

_USE_AS_PARTIAL_INPUT = OpenApiExample(
    "GenreUseAs — partial request body",
    summary="Only the fields you want to change",
    value={"name": "updated-tag"},
    request_only=True,
)


# ===========================================================================
# GenreUseAs — per-action schemas
# ===========================================================================

_USE_AS_LIST = extend_schema(
    summary="List all genre usage contexts",
    description=(
        "Returns a paginated list of all **GenreUseAs** objects.\n\n"
        "These objects define the *role* a genre plays in the system — "
        "for example as a production classification (`genre`) or as a "
        "lightweight label (`tag`)."
    ),
    responses={
        200: GenreUseAsSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_USE_AS_RESPONSE],
)

_USE_AS_RETRIEVE = extend_schema(
    summary="Retrieve a genre usage context",
    description=(
        "Returns the full representation of a single **GenreUseAs** object "
        "identified by its primary key."
    ),
    responses={
        200: GenreUseAsSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_USE_AS_RESPONSE],
)

_USE_AS_CREATE = extend_schema(
    summary="Create a genre usage context",
    description=(
        "Creates a new **GenreUseAs** object.\n\n"
        "The `name` should describe the intended role in plain English "
        "(e.g. `genre`, `tag`, `category`).\n\n"
        "> **Requires an internal API key.**"
    ),
    request=GenreUseAsSerializer,
    responses={
        201: GenreUseAsSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_USE_AS_INPUT, _USE_AS_RESPONSE],
)

_USE_AS_UPDATE = extend_schema(
    summary="Replace a genre usage context",
    description=(
        "Fully replaces an existing **GenreUseAs** object. "
        "All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=GenreUseAsSerializer,
    responses={
        200: GenreUseAsSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_USE_AS_INPUT, _USE_AS_RESPONSE],
)

_USE_AS_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a genre usage context",
    description=(
        "Updates one or more fields of an existing **GenreUseAs** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=GenreUseAsSerializer,
    responses={
        200: GenreUseAsSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_USE_AS_PARTIAL_INPUT, _USE_AS_RESPONSE],
)

_USE_AS_DESTROY = extend_schema(
    summary="Delete a genre usage context",
    description=(
        "Permanently removes a **GenreUseAs** object.\n\n"
        "> **Warning:** Deleting a usage context cascades to all genres "
        "that reference it. This action is irreversible.\n\n"
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
# Genre — examples
# ===========================================================================

_GENRE_RESPONSE_MULTILINGUAL = OpenApiExample(
    "Genre — Multilingual Response",
    summary="Example of a genre with all available translations",
    value={
        "id": 10,
        "type": "theater",
        "use_as": 1,
        "name": {"nl": "Theater", "en": "Theatre", "fr": "Théâtre"},
    },
    response_only=True,
)

_GENRE_INPUT = OpenApiExample(
    "Genre — request body",
    summary="Payload for creating a new genre",
    description=(
        "Only `type` and `use_as` are required. "
        "Localised names are added via the translation endpoints after creation."
    ),
    value={"type": "contemporary_dance", "use_as": 1},
    request_only=True,
)

_GENRE_PARTIAL_INPUT = OpenApiExample(
    "Genre — partial request body",
    summary="Only the fields you want to change",
    value={"use_as": 2},
    request_only=True,
)


# ===========================================================================
# Genre — per-action schemas
# ===========================================================================

_GENRE_LIST = extend_schema(
    summary="List all genres",
    description=("Returns a paginated list of all **Genre** objects.\n\n"),
    responses={
        200: GenreSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_GENRE_RESPONSE_MULTILINGUAL],
)

_GENRE_RETRIEVE = extend_schema(
    summary="Retrieve a genre",
    description=(
        "Returns the full representation of a single **Genre** identified "
        "by its primary key, including its technical type, usage context, "
        "and localised display name.\n\n"
    ),
    responses={
        200: GenreSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_GENRE_RESPONSE_MULTILINGUAL],
)

_GENRE_CREATE = extend_schema(
    summary="Create a genre",
    description=(
        "Creates a new **Genre** in the archive.\n\n"
        "- The `type` field is an internal technical identifier and must "
        "  use `snake_case` (e.g. `contemporary_dance`, `festival`).\n"
        "- Localised display names must be added via the **Genre Translation** "
        "  endpoints after the genre has been created.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=GenreSerializer,
    responses={
        201: GenreSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_GENRE_INPUT, _GENRE_RESPONSE_MULTILINGUAL],
)

_GENRE_UPDATE = extend_schema(
    summary="Replace a genre",
    description=(
        "Fully replaces an existing **Genre**. "
        "All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=GenreSerializer,
    responses={
        200: GenreSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
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
    responses={
        200: GenreSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
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
    responses={
        204: RESPONSE_204_DELETED,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
)


# ===========================================================================
# Assembled decorators — imported and applied in views.py
# ===========================================================================

genre_use_as_schema = extend_schema_view(
    list=_USE_AS_LIST,
    retrieve=_USE_AS_RETRIEVE,
    create=_USE_AS_CREATE,
    update=_USE_AS_UPDATE,
    partial_update=_USE_AS_PARTIAL_UPDATE,
    destroy=_USE_AS_DESTROY,
)

genre_schema = extend_schema_view(
    list=_GENRE_LIST,
    retrieve=_GENRE_RETRIEVE,
    create=_GENRE_CREATE,
    update=_GENRE_UPDATE,
    partial_update=_GENRE_PARTIAL_UPDATE,
    destroy=_GENRE_DESTROY,
)
