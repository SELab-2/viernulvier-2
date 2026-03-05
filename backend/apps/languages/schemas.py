"""
OpenAPI schema decorators for the Language app.

Keeping all drf-spectacular annotations here means views.py stays focused
on routing logic only. Each action is defined as a private variable and
assembled into one `extend_schema_view` decorator at the bottom of the file.
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

from .serializers import LanguageSerializer

# ===========================================================================
# Language — examples
# ===========================================================================

_LANGUAGE_RESPONSE = OpenApiExample(
    "Language — response",
    summary="A language object",
    value={"code": "nl", "name": "Dutch", "is_active": True},
    response_only=True,
)

_LANGUAGE_INPUT = OpenApiExample(
    "Language — request body",
    summary="Payload for creating a new language",
    value={"code": "fr", "name": "French", "is_active": False},
    request_only=True,
)

_LANGUAGE_PARTIAL_INPUT = OpenApiExample(
    "Language — partial request body",
    summary="Only the fields you want to change",
    value={"is_active": True},
    request_only=True,
)


# ===========================================================================
# Language — per-action schemas
# ===========================================================================

_LANGUAGE_LIST = extend_schema(
    summary="List all languages",
    description=(
        "Returns a paginated list of all **Language** objects.\n\n"
        "Languages are identified by their ISO 639-1 `code` (e.g. `en`, `nl`, `fr`). "
        "Only languages with `is_active = true` are surfaced in consumer-facing "
        "interfaces; inactive languages are still returned here for management purposes."
    ),
    responses={
        200: LanguageSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_LANGUAGE_RESPONSE],
)

_LANGUAGE_RETRIEVE = extend_schema(
    summary="Retrieve a language",
    description=(
        "Returns the full representation of a single **Language** identified by its ISO 639-1 `code` (e.g. `en`, `nl`)."
    ),
    responses={
        200: LanguageSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_LANGUAGE_RESPONSE],
)

_LANGUAGE_CREATE = extend_schema(
    summary="Create a language",
    description=(
        "Creates a new **Language**.\n\n"
        "- `code` must be a valid ISO 639-1 two-letter code (e.g. `en`, `nl`, `fr`).\n"
        "- `name` is the human-readable English name of the language.\n"
        "- Set `is_active` to `false` while translations are still being "
        "  implemented; flip to `true` once the language is ready for consumers.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=LanguageSerializer,
    responses={
        201: LanguageSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_LANGUAGE_INPUT, _LANGUAGE_RESPONSE],
)

_LANGUAGE_UPDATE = extend_schema(
    summary="Replace a language",
    description=(
        "Fully replaces an existing **Language**. "
        "All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=LanguageSerializer,
    responses={
        200: LanguageSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_LANGUAGE_INPUT, _LANGUAGE_RESPONSE],
)

_LANGUAGE_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a language",
    description=(
        "Updates one or more fields of an existing **Language** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=LanguageSerializer,
    responses={
        200: LanguageSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_LANGUAGE_PARTIAL_INPUT, _LANGUAGE_RESPONSE],
)

_LANGUAGE_DESTROY = extend_schema(
    summary="Delete a language",
    description=(
        "Permanently removes a **Language** from the system.\n\n"
        "> **Warning:** Deleting a language cascades to all translations that "
        "reference it across every app (genres, locations, spaces, halls, …). "
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
# Assembled decorator — imported and applied in views.py
# ===========================================================================

language_schema = extend_schema_view(
    list=_LANGUAGE_LIST,
    retrieve=_LANGUAGE_RETRIEVE,
    create=_LANGUAGE_CREATE,
    update=_LANGUAGE_UPDATE,
    partial_update=_LANGUAGE_PARTIAL_UPDATE,
    destroy=_LANGUAGE_DESTROY,
)
