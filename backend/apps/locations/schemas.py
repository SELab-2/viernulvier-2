"""
OpenAPI schema decorators for the Locations app.

Keeping all drf-spectacular annotations here means views.py stays focused
on routing logic only. Each action is defined as a private variable and
assembled into three `extend_schema_view` decorators at the bottom of the file.
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

from .serializers import HallSerializer, LocationSerializer, SpaceSerializer

# ===========================================================================
# Location — examples
# ===========================================================================

_LOCATION_RESPONSE = OpenApiExample(
    "Location — response",
    summary="A location with a translated name",
    value={
        "id": 1,
        "street": "Kiekenmarkt",
        "number": "48",
        "postal_code": "1000",
        "city": "Brussels",
        "country": "Belgium",
        "phone_1": "+32 2 555 12 34",
        "phone_2": None,
        "is_own_location": True,
        "name": {
            "nl": "Koninklijke Muntschouwburg",
            "en": "Royal Theatre of the Mint",
            "fr": "Théâtre Royal de la Monnaie",
        },
    },
    response_only=True,
)

_LOCATION_INPUT = OpenApiExample(
    "Location — request body",
    summary="Payload for creating a new location",
    value={
        "street": "Kiekenmarkt",
        "number": "48",
        "postal_code": "1000",
        "city": "Brussels",
        "country": "Belgium",
        "phone_1": "+32 2 555 12 34",
        "phone_2": None,
        "is_own_location": True,
    },
    request_only=True,
)

_LOCATION_PARTIAL_INPUT = OpenApiExample(
    "Location — partial request body",
    summary="Only the fields you want to change",
    value={"phone_1": "+32 2 555 99 99", "is_own_location": False},
    request_only=True,
)


# ===========================================================================
# Location — per-action schemas
# ===========================================================================

_LOCATION_LIST = extend_schema(
    summary="List all locations",
    description=(
        "Returns a paginated list of all **Location** objects.\n\n"
        "Each location includes its full address, optional phone numbers, "
        "an ownership flag, and a `name` field containing all available "
        'translations as a dictionary (e.g. {"en": "City Hall", '
        '"fr": "Hôtel de Ville"}).'
    ),
    responses={
        200: LocationSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_LOCATION_RESPONSE],
)

_LOCATION_RETRIEVE = extend_schema(
    summary="Retrieve a location",
    description=(
        "Returns the full representation of a single **Location** identified "
        "by its primary key, including address details and the localised name."
    ),
    responses={
        200: LocationSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_LOCATION_RESPONSE],
)

_LOCATION_CREATE = extend_schema(
    summary="Create a location",
    description=(
        "Creates a new **Location**.\n\n"
        "- `street`, `number`, `postal_code`, `city`, and `country` are required.\n"
        "- Localised names must be added via the **Location Translation** "
        "  endpoints after the location has been created.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=LocationSerializer,
    responses={
        201: LocationSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_LOCATION_INPUT, _LOCATION_RESPONSE],
)

_LOCATION_UPDATE = extend_schema(
    summary="Replace a location",
    description=(
        "Fully replaces an existing **Location**. "
        "All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=LocationSerializer,
    responses={
        200: LocationSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_LOCATION_INPUT, _LOCATION_RESPONSE],
)

_LOCATION_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a location",
    description=(
        "Updates one or more fields of an existing **Location** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=LocationSerializer,
    responses={
        200: LocationSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_LOCATION_PARTIAL_INPUT, _LOCATION_RESPONSE],
)

_LOCATION_DESTROY = extend_schema(
    summary="Delete a location",
    description=(
        "Permanently removes a **Location** from the archive.\n\n"
        "> **Warning:** All associated translations, spaces, and halls are also "
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
# Space — examples
# ===========================================================================

_SPACE_RESPONSE = OpenApiExample(
    "Space — response",
    summary="A space with a translated name",
    value={
        "id": 3,
        "location": 1,
        "name": {
            "nl": "Grote Zaal",
            "en": "Main Hall",
            "fr": "Grande Salle",
        },
    },
    response_only=True,
)

_SPACE_INPUT = OpenApiExample(
    "Space — request body",
    summary="Payload for creating a new space",
    value={"location": 1},
    request_only=True,
)

_SPACE_PARTIAL_INPUT = OpenApiExample(
    "Space — partial request body",
    summary="Only the fields you want to change",
    value={"location": 2},
    request_only=True,
)


# ===========================================================================
# Space — per-action schemas
# ===========================================================================

_SPACE_LIST = extend_schema(
    summary="List all spaces",
    description=(
        "Returns a paginated list of all **Space** objects.\n\n"
        "A space is a distinct physical area within a location (e.g. a building "
        "or wing). It groups one or more halls under a single location."
    ),
    responses={
        200: SpaceSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_SPACE_RESPONSE],
)

_SPACE_RETRIEVE = extend_schema(
    summary="Retrieve a space",
    description=(
        "Returns the full representation of a single **Space** identified "
        "by its primary key, including its parent location and localised name."
    ),
    responses={
        200: SpaceSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_SPACE_RESPONSE],
)

_SPACE_CREATE = extend_schema(
    summary="Create a space",
    description=(
        "Creates a new **Space** under an existing location.\n\n"
        "- `location` (FK) is the only required field.\n"
        "- Localised names must be added via the **Space Translation** "
        "  endpoints after the space has been created.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=SpaceSerializer,
    responses={
        201: SpaceSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_SPACE_INPUT, _SPACE_RESPONSE],
)

_SPACE_UPDATE = extend_schema(
    summary="Replace a space",
    description=(
        "Fully replaces an existing **Space**. All writable fields must be supplied.\n\n> **Requires an internal API key.**"
    ),
    request=SpaceSerializer,
    responses={
        200: SpaceSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_SPACE_INPUT, _SPACE_RESPONSE],
)

_SPACE_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a space",
    description=(
        "Updates one or more fields of an existing **Space** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=SpaceSerializer,
    responses={
        200: SpaceSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_SPACE_PARTIAL_INPUT, _SPACE_RESPONSE],
)

_SPACE_DESTROY = extend_schema(
    summary="Delete a space",
    description=(
        "Permanently removes a **Space** from the archive.\n\n"
        "> **Warning:** All associated translations and halls are also deleted. "
        "This action is irreversible.\n\n"
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
# Hall — examples
# ===========================================================================

_HALL_RESPONSE = OpenApiExample(
    "Hall — response",
    summary="A hall with seating flags and translated fields",
    value={
        "id": 7,
        "space": 3,
        "seat_selection": True,
        "open_seating": False,
        "name": {
            "nl": "Rode Zaal",
            "en": "Red Hall",
            "fr": "Salle Rouge",
        },
        "remark": {
            "nl": "Rolstoelplaatsen beschikbaar op rij A.",
            "en": "Wheelchair spaces available in row A.",
            "fr": "Places pour fauteuils roulants disponibles en rangée A.",
        },
    },
    response_only=True,
)

_HALL_INPUT = OpenApiExample(
    "Hall — request body",
    summary="Payload for creating a new hall",
    value={"space": 3, "seat_selection": True, "open_seating": False},
    request_only=True,
)

_HALL_PARTIAL_INPUT = OpenApiExample(
    "Hall — partial request body",
    summary="Only the fields you want to change",
    value={"open_seating": True},
    request_only=True,
)


# ===========================================================================
# Hall — per-action schemas
# ===========================================================================

_HALL_LIST = extend_schema(
    summary="List all halls",
    description=(
        "Returns a paginated list of all **Hall** objects.\n\n"
        "A hall is a specific room or auditorium within a space. "
        "It carries seating configuration flags and supports localised "
        "`name` and `remark` fields."
    ),
    responses={
        200: HallSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_HALL_RESPONSE],
)

_HALL_RETRIEVE = extend_schema(
    summary="Retrieve a hall",
    description=(
        "Returns the full representation of a single **Hall** identified "
        "by its primary key, including its parent space, seating flags, "
        "and localised name and remark."
    ),
    responses={
        200: HallSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_HALL_RESPONSE],
)

_HALL_CREATE = extend_schema(
    summary="Create a hall",
    description=(
        "Creates a new **Hall** within an existing space.\n\n"
        "- `space` (FK) is required.\n"
        "- `seat_selection` and `open_seating` default to `false`.\n"
        "- Localised `name` and `remark` must be added via the **Hall Translation** "
        "  endpoints after the hall has been created.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=HallSerializer,
    responses={
        201: HallSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_HALL_INPUT, _HALL_RESPONSE],
)

_HALL_UPDATE = extend_schema(
    summary="Replace a hall",
    description=(
        "Fully replaces an existing **Hall**. All writable fields must be supplied.\n\n> **Requires an internal API key.**"
    ),
    request=HallSerializer,
    responses={
        200: HallSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_HALL_INPUT, _HALL_RESPONSE],
)

_HALL_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a hall",
    description=(
        "Updates one or more fields of an existing **Hall** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=HallSerializer,
    responses={
        200: HallSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_HALL_PARTIAL_INPUT, _HALL_RESPONSE],
)

_HALL_DESTROY = extend_schema(
    summary="Delete a hall",
    description=(
        "Permanently removes a **Hall** from the archive.\n\n"
        "> **Warning:** All associated translations are also deleted, "
        "and any events or performances linked to this hall may be affected. "
        "This action is irreversible.\n\n"
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

location_schema = extend_schema_view(
    list=_LOCATION_LIST,
    retrieve=_LOCATION_RETRIEVE,
    create=_LOCATION_CREATE,
    update=_LOCATION_UPDATE,
    partial_update=_LOCATION_PARTIAL_UPDATE,
    destroy=_LOCATION_DESTROY,
)

space_schema = extend_schema_view(
    list=_SPACE_LIST,
    retrieve=_SPACE_RETRIEVE,
    create=_SPACE_CREATE,
    update=_SPACE_UPDATE,
    partial_update=_SPACE_PARTIAL_UPDATE,
    destroy=_SPACE_DESTROY,
)

hall_schema = extend_schema_view(
    list=_HALL_LIST,
    retrieve=_HALL_RETRIEVE,
    create=_HALL_CREATE,
    update=_HALL_UPDATE,
    partial_update=_HALL_PARTIAL_UPDATE,
    destroy=_HALL_DESTROY,
)
