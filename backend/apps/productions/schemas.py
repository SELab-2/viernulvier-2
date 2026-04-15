"""
OpenAPI schema decorators for the Productions app.
"""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

from apps.core.openapi import (
    DELETE_ERRORS,
    ITEM_ERRORS,
    MUTATE_ERRORS,
    READ_ERRORS,
    RESPONSE_204_DELETED,
    WRITE_ERRORS,
)

from .serializers import ProductionSerializer

# ===========================================================================
# Production - examples
# ===========================================================================

_PRODUCTION_RESPONSE = OpenApiExample(
    "Production - response",
    summary="A production with localised fields and nested relations, without events",
    value={
        "id": 1,
        "attendance_mode": "offline",
        "performer_type": "group",
        "first_event_start": "2025-09-15T19:30:00Z",
        "last_event_end": "2025-11-02T21:30:00Z",
        "media_gallery": {"id": 706, "name": "home", "media_items": []},
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
                "description": {"nl": "Eigentijdse dans- en theaterwerken.", "en": "Contemporary dance and theatre works."},
            }
        ],
        "genres": [{"id": 2, "type": "theater", "name": "Theater"}],
    },
    response_only=True,
)

_PRODUCTION_RESPONSE_WITH_EVENTS = OpenApiExample(
    "Production - response - events",
    summary="A production with localised fields and nested relations, including events",
    value={
        "id": 1,
        "attendance_mode": "offline",
        "performer_type": "group",
        "first_event_start": "2025-09-15T19:30:00Z",
        "last_event_end": "2025-09-15T21:30:00Z",
        "media_gallery": {"id": 706, "name": "home", "media_items": []},
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
                "description": {},
            }
        ],
        "genres": [{"id": 2, "type": "theater", "name": "Theater"}],
        "events": [
            {
                "id": 42,
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
                "hall_display": "Red Hall",
                "starts_at": "2025-09-15T19:30:00Z",
                "ends_at": "2025-09-15T21:30:00Z",
                "prices": [],
            },
        ],
    },
    response_only=True,
)

_PRODUCTION_RESPONSE_WITH_RELATED = OpenApiExample(
    "Production - response - related",
    summary="A production including related productions grouped by tag",
    value={
        "id": 1,
        "attendance_mode": "offline",
        "performer_type": "group",
        "media_gallery": {"id": 706, "name": "home", "media_items": []},
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
                "description": {"nl": "Eigentijdse dans- en theaterwerken."},
            }
        ],
        "genres": [{"id": 2, "type": "theater", "name": "Theater"}],
        "related": [
            {
                "tag": {
                    "id": 12,
                    "name": "Hedendaags",
                    "display_name": "Hedendaags",
                },
                "productions": [
                    {
                        "id": 2,
                        "title": {"nl": "Andere productie"},
                        "display_name": "Andere productie",
                        "artist_name": {"nl": "Andere maker"},
                        "media_gallery": {"id": 800, "name": "gallery-2", "media_items": []},
                    }
                ],
            }
        ],
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
        "Nested `tags` and `genres` carry their own translated fields as dictionaries. "
        "Each tag also exposes a `description` dictionary containing per-production "
        "context notes in all available languages; the dictionary is empty when no "
        "descriptions have been added for that tag."
    ),
    responses={200: ProductionSerializer, **READ_ERRORS},
    examples=[_PRODUCTION_RESPONSE],
)

_PRODUCTION_RETRIEVE = extend_schema(
    summary="Retrieve a production",
    description=(
        "Returns the full representation of a single **Production** identified "
        "by its primary key.\n\n"
        "All translated fields are returned as language-code dictionaries. "
        "Genres are ordered by their `position` value. "
        "Each tag exposes a `description` dictionary with per-production context notes "
        "per language; the dictionary is empty when no descriptions have been added. "
        "`include=related` returns productions grouped by tag, where each related tag "
        "is compact and only exposes `id`, `name`, and `display_name`. "
        "Use `?include=events` to include all related events in the response, or "
        "`?include=related` to include related productions grouped by tag."
    ),
    parameters=[
        OpenApiParameter(
            name="include",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Comma-separated list of relations to include. Accepted values: `events`, `related`.",
            examples=[
                OpenApiExample("No includes", value=""),
                OpenApiExample("Include events", value="events"),
                OpenApiExample("Include related", value="related"),
            ],
        )
    ],
    responses={200: ProductionSerializer, **ITEM_ERRORS},
    examples=[_PRODUCTION_RESPONSE, _PRODUCTION_RESPONSE_WITH_EVENTS, _PRODUCTION_RESPONSE_WITH_RELATED],
)

_PRODUCTION_CREATE = extend_schema(
    summary="Create a production",
    description=(
        "Creates a new **Production**.\n\n"
        "- `attendance_mode` accepts `offline` or `online`.\n"
        "- `performer_type` accepts `group` or `solo`.\n"
        "- `uit_database_theme` and `uit_database_type` are optional FK references.\n"
        "- Translated fields (title, description, etc.) are managed via the "
        "**Production Translation** endpoints.\n"
        "- Tags and genres are managed via their dedicated through-table endpoints.\n"
        "- Per-production tag descriptions are managed via the "
        "**Production Tag Translation** endpoints.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=ProductionSerializer,
    responses={201: ProductionSerializer, **WRITE_ERRORS},
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
    responses={200: ProductionSerializer, **MUTATE_ERRORS},
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
    responses={200: ProductionSerializer, **MUTATE_ERRORS},
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
    responses={204: RESPONSE_204_DELETED, **DELETE_ERRORS},
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
