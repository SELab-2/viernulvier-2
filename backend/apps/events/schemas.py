"""
OpenAPI schema decorators for the Events app.

Keeping all drf-spectacular annotations here means views.py stays focused
on routing logic only. Each action is defined as a private variable and
assembled into a single ``extend_schema_view`` decorator at the bottom of
the file.

An event is a scheduled occurrence of a production in a specific hall.
Each event carries zero or more ``EventPrice`` entries that define capacity
and pricing per price rank.
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

from .serializers import EventSerializer

# ===========================================================================
# Event - examples
# ===========================================================================

_EVENT_RESPONSE = OpenApiExample(
    "Event - response",
    summary="An event with nested prices",
    value={
        "id": 42,
        "production": {
            "id": 1,
            "attendance_mode": "offline",
            "performer_type": "group",
            "uit_database_theme": {"id": 2, "name": "Theater"},
            "uit_database_type": {"id": 6, "name": "Voorstelling"},
            "display_title": "Hamlet",
            "display_artist_name": "Toneelhuis",
            "title": {"nl": "Hamlet", "en": "Hamlet", "fr": "Hamlet"},
            "artist_name": {"nl": "Toneelhuis", "en": "Toneelhuis", "fr": "Toneelhuis"},
            "tagline": {"nl": "Een klassieker", "en": "A classic", "fr": "Un classique"},
            "teaser": {"nl": "Korte teaser", "en": "Short teaser", "fr": "Court teaser"},
            "description": {"nl": "Lange beschrijving", "en": "Long description", "fr": "Description longue"},
            "tags": [],
            "genres": [],
        },
        "hall": {
            "id": 3,
            "space": {
                "id": 9,
                "location": {
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
                    "display_name": "Royal Theatre of the Mint",
                },
                "name": {"nl": "Grote Zaal", "en": "Main Hall", "fr": "Grande Salle"},
                "display_name": "Main Hall",
            },
            "seat_selection": True,
            "open_seating": False,
            "name": {"nl": "Rode Zaal", "en": "Red Hall", "fr": "Salle Rouge"},
            "display_name": "Red Hall",
            "remark": {
                "nl": "Rolstoelplaatsen beschikbaar op rij A.",
                "en": "Wheelchair spaces available in row A.",
                "fr": "Places pour fauteuils roulants disponibles en rangée A.",
            },
        },
        "production_display": "Hamlet",
        "hall_display": "Red Hall",
        "starts_at": "2025-09-15T19:30:00Z",
        "ends_at": "2025-09-15T21:30:00Z",
        "prices": [
            {
                "id": 101,
                "event": 42,
                "price": {
                    "id": 1,
                    "type": "standard",
                    "visibility": "public",
                    "membership": "",
                    "minimum": None,
                    "maximum": None,
                    "step": None,
                    "sort_order": 1,
                    "cineville_box": False,
                    "description": {"nl": "Standaard", "en": "Standard", "fr": "Standard"},
                    "display_description": "Standard",
                },
                "price_rank": {
                    "id": 1,
                    "position": 1,
                    "sold_out_buffer": 0,
                    "description": {"nl": "Normaal", "en": "Regular", "fr": "Normal"},
                    "display_description": "Regular",
                },
                "price_rank_display": "Regular",
                "price_display": "Standard",
                "amount": "18.00",
                "available": 120,
            },
            {
                "id": 102,
                "event": 42,
                "price": {
                    "id": 2,
                    "type": "student",
                    "visibility": "public",
                    "membership": "",
                    "minimum": None,
                    "maximum": None,
                    "step": None,
                    "sort_order": 2,
                    "cineville_box": False,
                    "description": {"nl": "Student", "en": "Student", "fr": "Étudiant"},
                    "display_description": "Student",
                },
                "price_rank": {
                    "id": 2,
                    "position": 2,
                    "sold_out_buffer": 0,
                    "description": {"nl": "Laat", "en": "Late", "fr": "Tardif"},
                    "display_description": "Late",
                },
                "price_rank_display": "Late",
                "price_display": "Student",
                "amount": "12.00",
                "available": 40,
            },
        ],
    },
    response_only=True,
)

_EVENT_NO_HALL_RESPONSE = OpenApiExample(
    "Event - response (no hall)",
    summary="An online event without a hall assignment",
    value={
        "id": 55,
        "production": {
            "id": 7,
            "attendance_mode": "online",
            "performer_type": "solo",
            "uit_database_theme": None,
            "uit_database_type": None,
            "display_title": "Livestream Concert",
            "display_artist_name": "Artist X",
            "title": {"nl": "Livestream Concert", "en": "Livestream Concert", "fr": "Concert en direct"},
            "artist_name": {"nl": "Artist X", "en": "Artist X", "fr": "Artist X"},
            "tagline": {},
            "teaser": {},
            "description": {},
            "tags": [],
            "genres": [],
        },
        "hall": None,
        "production_display": "Livestream Concert",
        "hall_display": None,
        "starts_at": "2025-10-01T20:00:00Z",
        "ends_at": "2025-10-01T21:00:00Z",
        "prices": [],
    },
    response_only=True,
)

_EVENT_INPUT = OpenApiExample(
    "Event - request body",
    summary="Payload for creating a new event (use *_id fields for input)",
    value={
        "production_id": 1,
        "hall_id": 3,
        "starts_at": "2025-09-15T19:30:00Z",
        "ends_at": "2025-09-15T21:30:00Z",
    },
    request_only=True,
)

_EVENT_PARTIAL_INPUT = OpenApiExample(
    "Event - partial request body",
    summary="Only the fields you want to change (use *_id fields for input)",
    value={"starts_at": "2025-09-15T20:00:00Z"},
    request_only=True,
)


# ===========================================================================
# EventPrice - examples
# ===========================================================================

_EVENT_PRICE_RESPONSE = OpenApiExample(
    "EventPrice - response",
    summary="A single price entry for an event",
    value={
        "id": 101,
        "event": 42,
        "price": {
            "id": 1,
            "type": "standard",
            "visibility": "public",
            "membership": "",
            "minimum": None,
            "maximum": None,
            "step": None,
            "sort_order": 1,
            "cineville_box": False,
            "description": {"nl": "Standaard", "en": "Standard", "fr": "Standard"},
            "display_description": "Standard",
        },
        "price_rank": {
            "id": 1,
            "position": 1,
            "sold_out_buffer": 0,
            "description": {"nl": "Normaal", "en": "Regular", "fr": "Normal"},
            "display_description": "Regular",
        },
        "price_rank_display": "Regular",
        "price_display": "Standard",
        "amount": "18.00",
        "available": 120,
    },
    response_only=True,
)

_EVENT_PRICE_INPUT = OpenApiExample(
    "EventPrice - request body",
    summary="Payload for creating an event price",
    value={
        "event": 42,
        "price": 1,
        "price_rank": 1,
        "amount": "18.00",
        "available": 120,
    },
    request_only=True,
)

_EVENT_PRICE_PARTIAL_INPUT = OpenApiExample(
    "EventPrice - partial request body",
    summary="Only the fields you want to change",
    value={"available": 80},
    request_only=True,
)


# ===========================================================================
# Event - per-action schemas
# ===========================================================================

_EVENT_LIST = extend_schema(
    summary="List all events",
    description=(
        "Returns a paginated list of all **Event** objects ordered by `starts_at`.\n\n"
        "Each event includes a nested `prices` array with the associated "
        "``EventPrice`` entries (amount and available capacity per price rank).\n\n"
        "Events without a hall assignment (`hall: null`) represent online or "
        "location-independent occurrences."
    ),
    responses={
        200: EventSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_EVENT_RESPONSE, _EVENT_NO_HALL_RESPONSE],
)

_EVENT_RETRIEVE = extend_schema(
    summary="Retrieve an event",
    description=(
        "Returns the full representation of a single **Event** identified by its "
        "primary key, including all nested ``EventPrice`` entries."
    ),
    responses={
        200: EventSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_EVENT_RESPONSE],
)

_EVENT_CREATE = extend_schema(
    summary="Create an event",
    description=(
        "Creates a new **Event** for an existing production.\n\n"
        "- `production_id` is required (integer FK).\n"
        "- `hall_id` is optional (integer FK); omit or set to `null` for online events.\n"
        "- `ends_at` must be strictly later than `starts_at` - the API enforces "
        "  this with a database-level check constraint.\n"
        "- Prices must be added separately via the **Event Price** endpoints "
        "  after creation.\n\n"
        "On write, use `*_id` fields for related objects. On read, nested objects are returned.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=EventSerializer,
    responses={
        201: EventSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_EVENT_INPUT, _EVENT_RESPONSE],
)

_EVENT_UPDATE = extend_schema(
    summary="Replace an event",
    description=(
        "Fully replaces an existing **Event**. All writable fields must be supplied.\n\n"
        "On write, use `*_id` fields for related objects. On read, nested objects are returned.\n\n> "
        "**Requires an internal API key.**"
    ),
    request=EventSerializer,
    responses={
        200: EventSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_EVENT_INPUT, _EVENT_RESPONSE],
)

_EVENT_PARTIAL_UPDATE = extend_schema(
    summary="Partially update an event",
    description=(
        "Updates one or more fields of an existing **Event** without "
        "requiring a full payload.\n\n"
        "On write, use `*_id` fields for related objects. On read, nested objects are returned.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=EventSerializer,
    responses={
        200: EventSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_EVENT_PARTIAL_INPUT, _EVENT_RESPONSE],
)

_EVENT_DESTROY = extend_schema(
    summary="Delete an event",
    description=(
        "Permanently removes an **Event** from the system.\n\n"
        "> **Warning:** All associated ``EventPrice`` entries are also deleted "
        "(cascade). This action is irreversible.\n\n"
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

event_schema = extend_schema_view(
    list=_EVENT_LIST,
    retrieve=_EVENT_RETRIEVE,
    create=_EVENT_CREATE,
    update=_EVENT_UPDATE,
    partial_update=_EVENT_PARTIAL_UPDATE,
    destroy=_EVENT_DESTROY,
)
