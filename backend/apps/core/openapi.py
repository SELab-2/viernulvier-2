"""
Shared OpenAPI building blocks used across all apps.

Import from here instead of redefining error responses and common
parameters in every individual schema file.
"""

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes


# ---------------------------------------------------------------------------
# Reusable error responses
# ---------------------------------------------------------------------------

RESPONSE_400 = OpenApiResponse(
    description=(
        "**Bad Request** — The request body failed validation.\n\n"
        "The response body contains field-level error details under `errors`."
    )
)

RESPONSE_401 = OpenApiResponse(
    description=(
        "**Unauthorized** — No API key was provided or the key is invalid.\n\n"
        "Include your key in every request:\n"
        "```\n"
        "Authorization: Api-Key <your_key>\n"
        "```"
    )
)

RESPONSE_403 = OpenApiResponse(
    description=(
        "**Forbidden** — Your API key does not have sufficient permissions.\n\n"
        "Write operations require an **internal** key. Public keys are read-only."
    )
)

RESPONSE_404 = OpenApiResponse(
    description="**Not Found** — No resource exists with the given identifier."
)

RESPONSE_204_DELETED = OpenApiResponse(
    description="**No Content** — The resource was permanently deleted."
)