"""
OpenAPI schema decorators for the Pricing app.

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
from .serializers import PriceRankSerializer, PriceSerializer


# ===========================================================================
# Price — examples
# ===========================================================================

_PRICE_RESPONSE = OpenApiExample(
    "Price — response",
    summary="A price category with a localised description",
    value={
        "id": 1,
        "type": "full",
        "visibility": "public",
        "membership": "",
        "minimum": None,
        "maximum": None,
        "step": None,
        "sort_order": 0,
        "cineville_box": False,
        "description": {"nl": "Volledig tarief", "en": "Full price", "fr": "Plein tarif"},
    },
    response_only=True,
)

_PRICE_VARIABLE_RESPONSE = OpenApiExample(
    "Price — variable pricing response",
    summary="A price category with variable pricing bounds",
    value={
        "id": 2,
        "type": "variable",
        "visibility": "public",
        "membership": "",
        "minimum": 500,
        "maximum": 2500,
        "step": 100,
        "sort_order": 1,
        "cineville_box": False,
        "description": {"nl": "Zelf kiezen", "en": "Pay what you want", "fr": "Prix libre"},
    },
    response_only=True,
)

_PRICE_INPUT = OpenApiExample(
    "Price — request body",
    summary="Payload for creating a new price",
    value={
        "type": "student",
        "visibility": "public",
        "membership": "",
        "minimum": None,
        "maximum": None,
        "step": None,
        "sort_order": 2,
        "cineville_box": False,
    },
    request_only=True,
)

_PRICE_PARTIAL_INPUT = OpenApiExample(
    "Price — partial request body",
    summary="Only the fields you want to change",
    value={"sort_order": 5, "cineville_box": True},
    request_only=True,
)


# ===========================================================================
# Price — per-action schemas
# ===========================================================================

_PRICE_LIST = extend_schema(
    summary="List all prices",
    description=(
        "Returns a paginated list of all **Price** objects ordered by `sort_order`.\n\n"
        "The `description` field contains all available translations as a "
        "language-code dictionary (e.g. {\"en\": \"Early Bird\", \"fr\": \"Prévente\"})."
    ),
    responses={
        200: PriceSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_PRICE_RESPONSE, _PRICE_VARIABLE_RESPONSE],
)

_PRICE_RETRIEVE = extend_schema(
    summary="Retrieve a price",
    description=(
        "Returns the full representation of a single **Price** identified "
        "by its primary key, including variable-pricing bounds and the "
        "localised description."
    ),
    responses={
        200: PriceSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_PRICE_RESPONSE],
)

_PRICE_CREATE = extend_schema(
    summary="Create a price",
    description=(
        "Creates a new **Price** category.\n\n"
        "- `type` and `visibility` are required.\n"
        "- For variable pricing, set `minimum`, `maximum`, and `step` together — "
        "  or leave all three as `null` for a fixed price.\n"
        "- Localised descriptions must be added via the **Price Translation** "
        "  endpoints after creation.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=PriceSerializer,
    responses={
        201: PriceSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_PRICE_INPUT, _PRICE_RESPONSE],
)

_PRICE_UPDATE = extend_schema(
    summary="Replace a price",
    description=(
        "Fully replaces an existing **Price**. "
        "All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=PriceSerializer,
    responses={
        200: PriceSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_PRICE_INPUT, _PRICE_RESPONSE],
)

_PRICE_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a price",
    description=(
        "Updates one or more fields of an existing **Price** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=PriceSerializer,
    responses={
        200: PriceSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_PRICE_PARTIAL_INPUT, _PRICE_RESPONSE],
)

_PRICE_DESTROY = extend_schema(
    summary="Delete a price",
    description=(
        "Permanently removes a **Price** from the system.\n\n"
        "> **Warning:** All associated translations are also deleted, and any "
        "events or tickets linked to this price may be affected. "
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
# PriceRank — examples
# ===========================================================================

_PRICE_RANK_RESPONSE = OpenApiExample(
    "PriceRank — response",
    summary="A price rank availability tier",
    value={
        "id": 1,
        "position": 1,
        "sold_out_buffer": 0,
        "description": {"nl": "Eerste rang", "en": "First tier", "fr": "Premier rang"},
    },
    response_only=True,
)

_PRICE_RANK_INPUT = OpenApiExample(
    "PriceRank — request body",
    summary="Payload for creating a new price rank",
    value={"position": 2, "sold_out_buffer": 10},
    request_only=True,
)

_PRICE_RANK_PARTIAL_INPUT = OpenApiExample(
    "PriceRank — partial request body",
    summary="Only the fields you want to change",
    value={"sold_out_buffer": 5},
    request_only=True,
)


# ===========================================================================
# PriceRank — per-action schemas
# ===========================================================================

_PRICE_RANK_LIST = extend_schema(
    summary="List all price ranks",
    description=(
        "Returns a paginated list of all **PriceRank** objects ordered by `position`.\n\n"
        "Price ranks define the ordered availability tiers that control when a "
        "price level is considered sold out. "
        "The `description` field contains all available translations as a "
        "language-code dictionary (e.g. {\"en\": \"Standard\", \"fr\": \"Standard\"})."
    ),
    responses={
        200: PriceRankSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_PRICE_RANK_RESPONSE],
)

_PRICE_RANK_RETRIEVE = extend_schema(
    summary="Retrieve a price rank",
    description=(
        "Returns the full representation of a single **PriceRank** identified "
        "by its primary key, including the sold-out buffer and the localised description."
    ),
    responses={
        200: PriceRankSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_PRICE_RANK_RESPONSE],
)

_PRICE_RANK_CREATE = extend_schema(
    summary="Create a price rank",
    description=(
        "Creates a new **PriceRank**.\n\n"
        "- `position` is required and must be unique across all price ranks.\n"
        "- Localised descriptions must be added via the **Price Rank Translation** "
        "  endpoints after creation.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=PriceRankSerializer,
    responses={
        201: PriceRankSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
    },
    examples=[_PRICE_RANK_INPUT, _PRICE_RANK_RESPONSE],
)

_PRICE_RANK_UPDATE = extend_schema(
    summary="Replace a price rank",
    description=(
        "Fully replaces an existing **PriceRank**. "
        "All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=PriceRankSerializer,
    responses={
        200: PriceRankSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_PRICE_RANK_INPUT, _PRICE_RANK_RESPONSE],
)

_PRICE_RANK_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a price rank",
    description=(
        "Updates one or more fields of an existing **PriceRank** without "
        "requiring a full payload.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=PriceRankSerializer,
    responses={
        200: PriceRankSerializer,
        400: RESPONSE_400,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    },
    examples=[_PRICE_RANK_PARTIAL_INPUT, _PRICE_RANK_RESPONSE],
)

_PRICE_RANK_DESTROY = extend_schema(
    summary="Delete a price rank",
    description=(
        "Permanently removes a **PriceRank** from the system.\n\n"
        "> **Warning:** All associated translations are also deleted. "
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

price_schema = extend_schema_view(
    list=_PRICE_LIST,
    retrieve=_PRICE_RETRIEVE,
    create=_PRICE_CREATE,
    update=_PRICE_UPDATE,
    partial_update=_PRICE_PARTIAL_UPDATE,
    destroy=_PRICE_DESTROY,
)

price_rank_schema = extend_schema_view(
    list=_PRICE_RANK_LIST,
    retrieve=_PRICE_RANK_RETRIEVE,
    create=_PRICE_RANK_CREATE,
    update=_PRICE_RANK_UPDATE,
    partial_update=_PRICE_RANK_PARTIAL_UPDATE,
    destroy=_PRICE_RANK_DESTROY,
)