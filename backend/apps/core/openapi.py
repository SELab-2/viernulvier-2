"""
Shared OpenAPI building blocks for the core app.

This module defines reusable :class:`~drf_spectacular.utils.OpenApiResponse`
objects for the HTTP status codes that appear across multiple apps. Importing
from here instead of re-declaring them per-app ensures that response
descriptions stay consistent throughout the generated schema.

Usage
-----
Import the constants you need at the top of any ``schemas.py`` file::

    from apps.core.openapi import (
        RESPONSE_400,
        RESPONSE_401,
        RESPONSE_403,
        RESPONSE_404,
        RESPONSE_204_DELETED,
    )

Then reference them in ``extend_schema`` decorators::

    _MY_ACTION = extend_schema(
        responses={
            200: MySerializer,
            400: RESPONSE_400,
            401: RESPONSE_401,
        }
    )
"""

from drf_spectacular.utils import OpenApiResponse


# ---------------------------------------------------------------------------
# 400 Bad Request
# ---------------------------------------------------------------------------

RESPONSE_400 = OpenApiResponse(
    description=(
        "**Bad Request** — The request body failed validation.\n\n"
        "The response body contains field-level error details under `errors`."
    )
)
"""
Returned when the request payload does not pass serializer validation.
Field-level messages are nested under the relevant field name.
"""

# ---------------------------------------------------------------------------
# 401 Unauthorized
# ---------------------------------------------------------------------------

RESPONSE_401 = OpenApiResponse(
    description=(
        "**Unauthorized** — No API key was provided or the key is invalid.\n\n"
        "Include your key in every request:\n"
        "```\n"
        "Authorization: Api-Key <your_key>\n"
        "```"
    )
)
"""
Returned when the ``Authorization`` header is absent, malformed, or contains
an unrecognised key. The ``WWW-Authenticate: Api-Key`` header is included
in the response so clients know which scheme to use.
"""

# ---------------------------------------------------------------------------
# 403 Forbidden
# ---------------------------------------------------------------------------

RESPONSE_403 = OpenApiResponse(
    description=(
        "**Forbidden** — Your API key does not have sufficient permissions.\n\n"
        "Write operations require an **internal** key. Public keys are read-only."
    )
)
"""
Returned when the key is valid but the caller's scope does not permit the
requested action (e.g. a public key attempting a POST, PUT, PATCH, or DELETE).
"""

# ---------------------------------------------------------------------------
# 404 Not Found
# ---------------------------------------------------------------------------

RESPONSE_404 = OpenApiResponse(
    description="**Not Found** — No resource exists with the given identifier."
)
"""
Returned when the requested primary key does not match any record in the
database.
"""

# ---------------------------------------------------------------------------
# 204 No Content (successful deletion)
# ---------------------------------------------------------------------------

RESPONSE_204_DELETED = OpenApiResponse(
    description="**No Content** — The resource was permanently deleted."
)
"""
Returned on successful ``DELETE`` requests. The response body is empty.
"""