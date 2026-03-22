"""
Shared OpenAPI building blocks for the core app.

This module defines reusable :class:`~drf_spectacular.utils.OpenApiResponse`
objects for the HTTP status codes that appear across multiple apps. Every
response uses :data:`ProblemSerializer` so the generated schema exactly
mirrors the RFC 7807 body that ``custom_exception_handler`` emits.

Usage
-----
Import the convenience sets that match the action pattern::

    from apps.core.openapi import (
        READ_ERRORS,    # 401, 403
        ITEM_ERRORS,    # 401, 403, 404
        WRITE_ERRORS,   # 401, 403, 422
        MUTATE_ERRORS,  # 401, 403, 404, 422
        DELETE_ERRORS,  # 401, 403, 404
    )

Then spread them into ``extend_schema`` responses::

    _MY_LIST = extend_schema(
        responses={200: MySerializer, **READ_ERRORS},
    )

    _MY_CREATE = extend_schema(
        request=MySerializer,
        responses={201: MySerializer, **WRITE_ERRORS},
    )

Or pick individual codes when you need something non-standard::

    from apps.core.openapi import error_responses

    _MY_ACTION = extend_schema(
        responses={200: MySerializer, **error_responses(401, 403, 404, 422)},
    )
"""

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, inline_serializer
from rest_framework import serializers

# ---------------------------------------------------------------------------
# RFC 7807 Problem Details serializer
# ---------------------------------------------------------------------------
# Mirrors the exact shape that custom_exception_handler() produces so the
# generated schema stays accurate.

_ErrorItemSerializer = inline_serializer(
    name="ErrorItem",
    fields={
        "pointer": serializers.CharField(
            help_text='JSON Pointer to the failing field (e.g. "/email/0").',
        ),
        "detail": serializers.CharField(
            help_text="Human-readable explanation of this specific error.",
        ),
        "code": serializers.CharField(
            help_text='Machine-readable error code (e.g. "required", "invalid").',
        ),
    },
)

ProblemSerializer = inline_serializer(
    name="Problem",
    fields={
        "type": serializers.CharField(
            default="about:blank",
            help_text="URI identifying the problem type. Always `about:blank` unless a custom type is defined.",
        ),
        "title": serializers.CharField(
            help_text='Short summary of the problem (e.g. "Unprocessable Entity").',
        ),
        "status": serializers.IntegerField(
            help_text="HTTP status code, mirrored for convenience.",
        ),
        "detail": serializers.CharField(
            help_text="Human-readable explanation for this specific occurrence.",
        ),
        "instance": serializers.CharField(
            required=False,
            help_text="Request path that triggered the error (e.g. `/api/v1/languages/`).",
        ),
        "errors": serializers.ListField(
            child=_ErrorItemSerializer,
            required=False,
            help_text="Field-level errors. Present only on 422 responses.",
        ),
    },
)


# ---------------------------------------------------------------------------
# Internal factory
# ---------------------------------------------------------------------------


def _problem_response(description: str, example_value: dict) -> OpenApiResponse:
    return OpenApiResponse(
        response=ProblemSerializer,
        description=description,
        examples=[
            OpenApiExample(
                name="Example",
                value=example_value,
                response_only=True,
            )
        ],
    )


# ---------------------------------------------------------------------------
# 400 Bad Request
# ---------------------------------------------------------------------------

RESPONSE_400 = _problem_response(
    description=(
        "**Bad Request** - The request body could not be parsed.\n\n"
        "Returned for malformed JSON or an unreadable payload before validation "
        "even runs. For field-level validation failures, see **422**."
    ),
    example_value={
        "type": "about:blank",
        "title": "Bad Request",
        "status": 400,
        "detail": "Malformed request body: JSON parse error - Expecting value: line 1 column 1 (char 0)",
        "instance": "/api/v1/languages/",
    },
)

# ---------------------------------------------------------------------------
# 401 Unauthorized
# ---------------------------------------------------------------------------

RESPONSE_401 = _problem_response(
    description=(
        "**Unauthorized** - No API key was provided or the key is invalid.\n\n"
        "Include your key in every request:\n"
        "```\n"
        "X-API-Key: <your_key>\n"
        "```"
    ),
    example_value={
        "type": "about:blank",
        "title": "Unauthorized",
        "status": 401,
        "detail": "Authentication credentials were not provided.",
        "instance": "/api/v1/languages/",
    },
)

# ---------------------------------------------------------------------------
# 403 Forbidden
# ---------------------------------------------------------------------------

RESPONSE_403 = _problem_response(
    description=(
        "**Forbidden** - Your API key does not have sufficient permissions.\n\n"
        "Write operations require an **internal** key. Public keys are read-only."
    ),
    example_value={
        "type": "about:blank",
        "title": "Forbidden",
        "status": 403,
        "detail": "You do not have permission to perform this action.",
        "instance": "/api/v1/languages/",
    },
)

# ---------------------------------------------------------------------------
# 404 Not Found
# ---------------------------------------------------------------------------

RESPONSE_404 = _problem_response(
    description="**Not Found** - No resource exists with the given identifier.",
    example_value={
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "No Language matches the given query.",
        "instance": "/api/v1/languages/xx/",
    },
)

# ---------------------------------------------------------------------------
# 422 Unprocessable Entity
# ---------------------------------------------------------------------------

RESPONSE_422 = _problem_response(
    description=(
        "**Unprocessable Entity** - The payload was valid JSON but failed "
        "serializer validation.\n\n"
        "Field-level details are listed under `errors`. Each item includes a "
        "JSON Pointer (`/field/index`), a human-readable `detail`, and a "
        "machine-readable `code`."
    ),
    example_value={
        "type": "about:blank",
        "title": "Unprocessable Entity",
        "status": 422,
        "detail": "One or more validation errors occurred.",
        "instance": "/api/v1/languages/",
        "errors": [
            {
                "pointer": "/code/0",
                "detail": "This field is required.",
                "code": "required",
            },
            {
                "pointer": "/code/1",
                "detail": "Ensure this value has at most 2 characters.",
                "code": "max_length",
            },
        ],
    },
)

# ---------------------------------------------------------------------------
# 204 No Content
# ---------------------------------------------------------------------------

RESPONSE_204_DELETED = OpenApiResponse(
    description="**No Content** - The resource was permanently deleted. The response body is empty.",
)


# ---------------------------------------------------------------------------
# error_responses() helper
# ---------------------------------------------------------------------------

_CODE_MAP: dict[int, OpenApiResponse] = {
    400: RESPONSE_400,
    401: RESPONSE_401,
    403: RESPONSE_403,
    404: RESPONSE_404,
    422: RESPONSE_422,
}


def error_responses(*codes: int) -> dict[int, OpenApiResponse]:
    """Return ``{status_code: OpenApiResponse}`` for the requested codes.

    Raises :exc:`ValueError` for any code that has no registered response,
    so a typo is caught at import time rather than silently omitted from
    the schema.

    Example::

        responses={201: MySerializer, **error_responses(401, 403, 422)}
    """
    unknown = set(codes) - _CODE_MAP.keys()
    if unknown:
        raise ValueError(f"No OpenApiResponse defined for status code(s): {sorted(unknown)}")
    return {code: _CODE_MAP[code] for code in codes}


# ---------------------------------------------------------------------------
# Convenience sets — cover the four standard ViewSet action patterns
# ---------------------------------------------------------------------------

READ_ERRORS: dict[int, OpenApiResponse] = error_responses(401, 403)
"""For ``list`` actions. No request body -> no 422, no 404."""

ITEM_ERRORS: dict[int, OpenApiResponse] = error_responses(401, 403, 404)
"""For ``retrieve`` actions. Can 404, but no request body -> no 422."""

WRITE_ERRORS: dict[int, OpenApiResponse] = error_responses(401, 403, 422)
"""For ``create`` (POST) actions. Has a request body -> can 422, but no 404."""

MUTATE_ERRORS: dict[int, OpenApiResponse] = error_responses(401, 403, 404, 422)
"""For ``update`` / ``partial_update`` actions. Can both 404 and 422."""

DELETE_ERRORS: dict[int, OpenApiResponse] = error_responses(401, 403, 404)
"""For ``destroy`` actions. Can 404, but no request body -> no 422."""
