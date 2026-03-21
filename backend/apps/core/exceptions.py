"""
RFC 7807 (Problem Details for HTTP APIs) compliant exception handler for DRF.
"""

import logging
from typing import Any

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    ErrorDetail,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ParseError,
    Throttled,
    UnsupportedMediaType,
    ValidationError,
)
from rest_framework.exceptions import (
    PermissionDenied as DRFPermissionDenied,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _flatten_errors(detail: Any, field_prefix: str = "") -> list[dict]:
    """
    Recursively walk DRF's nested error structure and return a flat list of
    RFC 7807-style error dicts:
        {"pointer": "/field/subfield", "detail": "error message", "code": "error_code"}
    """
    errors: list[dict] = []

    if isinstance(detail, list):
        for index, item in enumerate(detail):
            prefix = f"{field_prefix}/{index}" if field_prefix else f"/{index}"
            errors.extend(_flatten_errors(item, field_prefix=prefix))

    elif isinstance(detail, dict):
        for key, value in detail.items():
            prefix = f"{field_prefix}/{key}"
            errors.extend(_flatten_errors(value, field_prefix=prefix))

    elif isinstance(detail, ErrorDetail):
        errors.append(
            {
                "pointer": field_prefix or "/",
                "detail": str(detail),
                "code": detail.code,
            }
        )

    elif isinstance(detail, str):
        errors.append(
            {
                "pointer": field_prefix or "/",
                "detail": detail,
                "code": "error",
            }
        )

    else:
        errors.append(
            {
                "pointer": field_prefix or "/",
                "detail": str(detail),
                "code": "error",
            }
        )

    return errors


def _build_problem(
    *,
    status_code: int,
    title: str,
    detail: str,
    errors: list[dict] | None = None,
    instance: str | None = None,
    extra: dict | None = None,
) -> dict:
    """Build the RFC 7807 Problem Details response body."""
    body: dict = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        body["instance"] = instance
    if errors:
        body["errors"] = errors
    if extra:
        body.update(extra)
    return body


# ---------------------------------------------------------------------------
# Exception mapping
# ---------------------------------------------------------------------------

_STATUS_TITLES: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "Bad Request",
    status.HTTP_401_UNAUTHORIZED: "Unauthorized",
    status.HTTP_403_FORBIDDEN: "Forbidden",
    status.HTTP_404_NOT_FOUND: "Not Found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Method Not Allowed",
    status.HTTP_406_NOT_ACCEPTABLE: "Not Acceptable",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "Unsupported Media Type",
    status.HTTP_429_TOO_MANY_REQUESTS: "Too Many Requests",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
}


def _title_for(status_code: int, fallback: str) -> str:
    return _STATUS_TITLES.get(status_code, fallback)


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    RFC 7807-compliant exception handler.

    All HTTP errors are returned as:
        {
            "type":   "about:blank",
            "title":  "Human-readable problem type",
            "status": 422,
            "detail": "One-sentence summary",
            "errors": [                        # only for validation errors
                {"pointer": "/field", "detail": "msg", "code": "code"},
                ...
            ]
        }
    """
    request = context.get("request")
    instance = request.path if request else None

    # Convert Django and DRF exceptions to a common base of DRF APIExceptions.
    if isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = DRFPermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    # Let DRF's default handler convert the exception to a Response
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception - log it, return a generic 500.
        logger.exception(
            "Unhandled exception in %s %s",
            request.method if request else "?",
            instance or "unknown",
            exc_info=exc,
        )
        problem = _build_problem(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail="An unexpected error occurred. Please try again later.",
            instance=instance,
        )
        return Response(problem, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    status_code: int = response.status_code

    # Build the RFC 7807 body based on the specific exception type.

    # 422 Validation errors
    if isinstance(exc, ValidationError):
        flat_errors = _flatten_errors(exc.detail)
        problem = _build_problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Unprocessable Entity",
            detail="One or more validation errors occurred.",
            errors=flat_errors,
            instance=instance,
        )
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        response.data = problem
        return response

    # 429 Throttled
    if isinstance(exc, Throttled):
        extra = {}
        if exc.wait is not None:
            extra["retry_after"] = int(exc.wait)
            response["Retry-After"] = str(int(exc.wait))
        problem = _build_problem(
            status_code=status_code,
            title="Too Many Requests",
            detail=f"Request was throttled. Expected available in {exc.wait:.0f} second(s)."
            if exc.wait
            else "Request was throttled.",
            instance=instance,
            extra=extra or None,
        )
        response.data = problem
        return response

    # 401 Not authenticated
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        response["WWW-Authenticate"] = 'Bearer realm="api"'
        problem = _build_problem(
            status_code=status_code,
            title=_title_for(status_code, "Unauthorized"),
            detail=str(exc.detail) if hasattr(exc, "detail") else "Authentication required.",
            instance=instance,
        )
        response.data = problem
        return response

    # 405 Method not allowed
    if isinstance(exc, MethodNotAllowed):
        if hasattr(exc, "detail") and isinstance(exc.detail, ErrorDetail):
            detail_str = str(exc.detail)
        else:
            detail_str = f'Method "{request.method}" not allowed.' if request else "Method not allowed."
        allowed = response.get("Allow", "")
        extra = {"allowed_methods": [m.strip() for m in allowed.split(",")]} if allowed else None
        problem = _build_problem(
            status_code=status_code,
            title="Method Not Allowed",
            detail=detail_str,
            instance=instance,
            extra=extra,
        )
        response.data = problem
        return response

    # 415 Unsupported media type
    if isinstance(exc, UnsupportedMediaType):
        problem = _build_problem(
            status_code=status_code,
            title="Unsupported Media Type",
            detail=str(exc.detail),
            instance=instance,
        )
        response.data = problem
        return response

    # 400 Parse error (malformed JSON, XML, …)
    if isinstance(exc, ParseError):
        problem = _build_problem(
            status_code=status_code,
            title="Bad Request",
            detail=f"Malformed request body: {exc.detail}",
            instance=instance,
        )
        response.data = problem
        return response

    # All other APIExceptions (403, 404, and custom ones)
    if isinstance(exc, APIException):
        detail = exc.detail
        # Some custom exceptions put a list/dict in detail - flatten those too.
        if isinstance(detail, (list, dict)):
            flat_errors = _flatten_errors(detail)
            problem = _build_problem(
                status_code=status_code,
                title=_title_for(status_code, getattr(exc, "default_code", "Error").replace("_", " ").title()),
                detail="One or more errors occurred.",
                errors=flat_errors,
                instance=instance,
            )
        else:
            problem = _build_problem(
                status_code=status_code,
                title=_title_for(status_code, type(exc).__name__),
                detail=str(detail),
                instance=instance,
            )
        response.data = problem
        return response

    return response
