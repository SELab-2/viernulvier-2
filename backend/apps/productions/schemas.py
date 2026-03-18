"""
OpenAPI schema decorators for the Productions app.

Keeping all drf-spectacular annotations here means views.py stays focused
on routing logic only. Each action is defined as a private variable and
assembled into a single ``extend_schema_view`` decorator at the bottom of
the file.

Productions are the core catalogue entity. A production groups one or more
events and carries translatable metadata (title, description, artist name,
etc.) as well as genre and tag classifications.
"""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
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

from .serializers import ProductionSerializer

# ===========================================================================
# Production - examples
# ===========================================================================

_PRODUCTION_RESPONSE = OpenApiExample(
    "Production - response",
    summary="A production with localised fields and nested relations",
    value={
        "id": 1,
        "attendance_mode": "offline",
        "performer_type": "group",
        "media_gallery": 4,
        "uit_database_theme": {"id": 3, "name": "Theater"},
        "uit_database_type": {"id": 7, "name": "Voorstelling"},
        "title": "De Laatste Avond",
        "artist_name": "Collectief Morgen",
        "tagline": "Een ode aan vergankelijkheid",
        "teaser": "Een indringende voorstelling over verlies en hoop.",
        "description": "Volledige beschrijving van de productie...",
        "tags": [
            {
                "id": 12,
                "type": "theme",
                "name": "Hedendaags",
                "url": "",
                "source": "",
                "source_type": "",
                "is_external": False,
                "is_enabled": True,
                "short_description": None,
                "url_title": "",
            }
        ],
        "genres": [{"id": 2, "type": "theater", "name": "Theater"}],
    },
    response_only=True,
)

_PRODUCTION_INPUT = OpenApiExample(
    "Production - request body",
    summary="Payload for creating a new production",
    value={
        "attendance_mode": "offline",
        "performer_type": "group",
        "uit_database_theme": 3,
        "uit_database_type": 7,
        "media_gallery": None,
    },
    request_only=True,
)

_PRODUCTION_PARTIAL_INPUT = OpenApiExample(
    "Production - partial request body",
    summary="Only the fields you want to change",
    value={"attendance_mode": "online", "performer_type": "solo"},
    request_only=True,
)


# ===========================================================================
# Production - per-action schemas
# ===========================================================================

_PRODUCTION_LIST = extend_schema(
    summary="List all productions",
    description=(
        "Returns a paginated list of all **Production** objects ordered by descending `id`.\n\n"
        "Translated fields (`title`, `artist_name`, `tagline`, `teaser`, `description`) "
        "are returned as language-code dictionaries "
        '(e.g. {"en": "Title", "fr": "Titre"}).\n\n'
        "Nested `genres` are returned in their configured `position` order. "
        "Nested `tags` and `genres` carry their own translated fields as dictionaries."
    ),
    responses={
        200: ProductionSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_PRODUCTION_RESPONSE],
)

_PRODUCTION_RETRIEVE = extend_schema(
    summary="Retrieve a production",
    description=(
        "Returns the full representation of a single **Production** identified "
        "by its primary key.\n\n"
        "All translated fields are returned as language-code dictionaries. "
        "Genres are ordered by their `position` value."
        "Use `?include=events` to include all related events in the response."
    ),
    parameters=[
        OpenApiParameter(
            name="include",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Comma-separated list of relations to include. Accepted values: `events`.",
            examples=[
                OpenApiExample("No includes", value=""),
                OpenApiExample("Include events", value="events"),
            ],
        )
    ],

    responses={
        200: ProductionSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_PRODUCTION_RESPONSE],
)

_PRODUCTION_CREATE = extend_schema(
    summary="Create a production",
    description=(
        "Creates a new **Production**.\n\n"
        "- `attendance_mode` accepts `offline` or `online`.\n"
        "- `performer_type` accepts `group` or `solo`.\n"
        "- `uit_database_theme` and `uit_database_type` are optional FK references.\n"
        "- Translated fields (title, description, etc.) are managed via the "
        "  **Production Translation** endpoints.\n"
        "- Tags and genres are managed via their dedicated through-table endpoints.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=ProductionSerializer,
    responses={
        201: ProductionSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_PRODUCTION_INPUT, _PRODUCTION_RESPONSE],
)

_PRODUCTION_UPDATE = extend_schema(
    summary="Replace a production",
    description=(
        "Fully replaces an existing **Production**. "
        "All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=ProductionSerializer,
    responses={
        200: ProductionSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_PRODUCTION_INPUT, _PRODUCTION_RESPONSE],
)

_PRODUCTION_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a production",
    description=(
        "Updates one or more fields of an existing **Production** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=ProductionSerializer,
    responses={
        200: ProductionSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_PRODUCTION_PARTIAL_INPUT, _PRODUCTION_RESPONSE],
)

_PRODUCTION_DESTROY = extend_schema(
    summary="Delete a production",
    description=(
        "Permanently removes a **Production** from the system.\n\n"
        "> **Warning:** All associated translations, genre links, tag links, and "
        "events are also deleted (cascade). This action is irreversible.\n\n"
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
# Assembled decorator - imported and applied in views.py
# ===========================================================================

production_schema = extend_schema_view(
    list=_PRODUCTION_LIST,
    retrieve=_PRODUCTION_RETRIEVE,
    create=_PRODUCTION_CREATE,
    update=_PRODUCTION_UPDATE,
    partial_update=_PRODUCTION_PARTIAL_UPDATE,
    destroy=_PRODUCTION_DESTROY,
)
