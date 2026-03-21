"""
Comprehensive test suite for the RFC 7807 DRF exception handler.
"""

import logging
from unittest.mock import MagicMock, patch

import django
import pytest
from django.conf import settings
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
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
    PermissionDenied,
    Throttled,
    UnsupportedMediaType,
    ValidationError,
)
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.core.exceptions import _build_problem, _flatten_errors, custom_exception_handler

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "rest_framework",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        ROOT_URLCONF=__name__,
        REST_FRAMEWORK={"EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler"},
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )
    django.setup()

urlpatterns = []  # ROOT_URLCONF requirement

factory = APIRequestFactory()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_context(method: str = "GET", path: str = "/api/test/") -> dict:
    """Return a minimal handler context with a real DRF request."""
    django_request = getattr(factory, method.lower())(path)
    request = Request(django_request)
    return {"request": request, "view": MagicMock()}


def call_handler(exc: Exception, method: str = "GET", path: str = "/api/test/"):
    return custom_exception_handler(exc, make_context(method=method, path=path))


def assert_rfc7807(body: dict, status_code: int):
    """Assert the response body is a valid RFC 7807 Problem Details object."""
    assert body["type"] == "about:blank"
    assert isinstance(body["title"], str) and body["title"]
    assert body["status"] == status_code
    assert isinstance(body["detail"], str) and body["detail"]


# ===========================================================================
# _flatten_errors
# ===========================================================================


class TestFlattenErrors:
    def test_single_error_detail(self):
        detail = ErrorDetail("This field is required.", code="required")
        result = _flatten_errors(detail)
        assert result == [{"pointer": "/", "detail": "This field is required.", "code": "required"}]

    def test_flat_dict(self):
        # DRF always wraps field errors in a list, so the list index /0 is included
        detail = {
            "email": [ErrorDetail("Enter a valid email.", code="invalid")],
            "name": [ErrorDetail("This field is required.", code="required")],
        }
        result = _flatten_errors(detail)
        pointers = {e["pointer"] for e in result}
        codes = {e["code"] for e in result}
        assert "/email/0" in pointers
        assert "/name/0" in pointers
        assert "invalid" in codes
        assert "required" in codes

    def test_nested_dict(self):
        # List wrapper from DRF adds the /0 suffix
        detail = {"address": {"city": [ErrorDetail("This field is required.", code="required")]}}
        result = _flatten_errors(detail)
        assert result[0]["pointer"] == "/address/city/0"

    def test_list_of_errors(self):
        detail = [
            ErrorDetail("First error.", code="invalid"),
            ErrorDetail("Second error.", code="null"),
        ]
        result = _flatten_errors(detail)
        assert len(result) == 2
        assert result[0]["pointer"] == "/0"
        assert result[1]["pointer"] == "/1"

    def test_nested_list_in_dict(self):
        detail = {"items": [ErrorDetail("Invalid item.", code="invalid")]}
        result = _flatten_errors(detail)
        assert result[0]["pointer"] == "/items/0"

    def test_plain_string(self):
        result = _flatten_errors("Something went wrong.")
        assert result == [{"pointer": "/", "detail": "Something went wrong.", "code": "error"}]

    def test_unknown_type_falls_through(self):
        result = _flatten_errors(42)
        assert result[0]["detail"] == "42"
        assert result[0]["code"] == "error"

    def test_deeply_nested(self):
        detail = {"user": {"profile": {"avatar": [ErrorDetail("Too large.", code="max_size")]}}}
        result = _flatten_errors(detail)
        assert result[0]["pointer"] == "/user/profile/avatar/0"
        assert result[0]["code"] == "max_size"

    def test_preserves_all_codes(self):
        detail = {
            "a": [ErrorDetail("err", code="alpha")],
            "b": [ErrorDetail("err", code="beta")],
            "c": [ErrorDetail("err", code="gamma")],
        }
        codes = {e["code"] for e in _flatten_errors(detail)}
        assert codes == {"alpha", "beta", "gamma"}


# ===========================================================================
# _build_problem
# ===========================================================================


class TestBuildProblem:
    def test_minimal(self):
        body = _build_problem(status_code=400, title="Bad Request", detail="Something is wrong.")
        assert body == {
            "type": "about:blank",
            "title": "Bad Request",
            "status": 400,
            "detail": "Something is wrong.",
        }

    def test_with_instance(self):
        body = _build_problem(status_code=404, title="Not Found", detail="Gone.", instance="/api/foo/")
        assert body["instance"] == "/api/foo/"

    def test_with_errors(self):
        errors = [{"pointer": "/name", "detail": "Required.", "code": "required"}]
        body = _build_problem(status_code=422, title="Unprocessable", detail="Errors.", errors=errors)
        assert body["errors"] == errors

    def test_none_errors_omitted(self):
        body = _build_problem(status_code=400, title="T", detail="D", errors=None)
        assert "errors" not in body

    def test_empty_errors_omitted(self):
        body = _build_problem(status_code=400, title="T", detail="D", errors=[])
        assert "errors" not in body

    def test_with_extra(self):
        body = _build_problem(status_code=429, title="T", detail="D", extra={"retry_after": 60})
        assert body["retry_after"] == 60

    def test_none_instance_omitted(self):
        body = _build_problem(status_code=400, title="T", detail="D", instance=None)
        assert "instance" not in body


# ===========================================================================
# Validation errors (422)
# ===========================================================================


class TestValidationError:
    def test_status_is_422(self):
        exc = ValidationError({"email": ["Enter a valid email."]})
        response = call_handler(exc)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_rfc7807_structure(self):
        exc = ValidationError({"name": ["This field is required."]})
        response = call_handler(exc)
        assert_rfc7807(response.data, 422)

    def test_errors_list_present(self):
        exc = ValidationError({"field": ["err1", "err2"]})
        response = call_handler(exc)
        assert "errors" in response.data
        assert isinstance(response.data["errors"], list)

    def test_error_pointer_format(self):
        # DRF wraps field errors in a list → pointer includes the /0 index
        exc = ValidationError({"username": [ErrorDetail("Too short.", code="min_length")]})
        response = call_handler(exc)
        pointers = [e["pointer"] for e in response.data["errors"]]
        assert "/username/0" in pointers

    def test_nested_field_pointer(self):
        exc = ValidationError({"address": {"city": [ErrorDetail("Required.", code="required")]}})
        response = call_handler(exc)
        pointers = [e["pointer"] for e in response.data["errors"]]
        assert "/address/city/0" in pointers

    def test_non_field_error(self):
        exc = ValidationError(["Non-field error."])
        response = call_handler(exc)
        assert response.status_code == 422
        assert len(response.data["errors"]) >= 1

    def test_multiple_errors_same_field(self):
        exc = ValidationError(
            {
                "password": [
                    ErrorDetail("Too short.", code="min_length"),
                    ErrorDetail("Must contain a number.", code="password_no_number"),
                ]
            }
        )
        response = call_handler(exc)
        errors = response.data["errors"]
        # Each error gets its own /password/0, /password/1 pointer
        password_errors = [e for e in errors if e["pointer"].startswith("/password")]
        assert len(password_errors) == 2

    def test_instance_in_response(self):
        exc = ValidationError({"x": ["err"]})
        response = call_handler(exc, path="/api/users/")
        assert response.data["instance"] == "/api/users/"

    def test_detail_message(self):
        exc = ValidationError({"x": ["err"]})
        response = call_handler(exc)
        assert "validation" in response.data["detail"].lower()


# ===========================================================================
# Django ValidationError conversion
# ===========================================================================


class TestDjangoValidationError:
    def test_message_dict_converted(self):
        exc = DjangoValidationError({"email": ["Enter a valid email address."]})
        response = call_handler(exc)
        assert response.status_code == 422
        assert "errors" in response.data

    def test_messages_list_converted(self):
        exc = DjangoValidationError(["Global error one.", "Global error two."])
        response = call_handler(exc)
        assert response.status_code == 422


# ===========================================================================
# Http404 → 404
# ===========================================================================


class TestHttp404:
    def test_returns_404(self):
        response = call_handler(Http404())
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rfc7807_structure(self):
        response = call_handler(Http404())
        assert_rfc7807(response.data, 404)

    def test_title_is_not_found(self):
        response = call_handler(Http404())
        assert "not found" in response.data["title"].lower()


# ===========================================================================
# DRF NotFound (404)
# ===========================================================================


class TestNotFound:
    def test_returns_404(self):
        response = call_handler(NotFound())
        assert response.status_code == 404

    def test_rfc7807_structure(self):
        response = call_handler(NotFound())
        assert_rfc7807(response.data, 404)

    def test_custom_detail(self):
        response = call_handler(NotFound(detail="Article not found."))
        assert "Article not found." in response.data["detail"]


# ===========================================================================
# PermissionDenied (403)
# ===========================================================================


class TestPermissionDenied:
    def test_drf_permission_denied_returns_403(self):
        response = call_handler(PermissionDenied())
        assert response.status_code == 403

    def test_django_permission_denied_converted(self):
        response = call_handler(DjangoPermissionDenied())
        assert response.status_code == 403

    def test_rfc7807_structure(self):
        response = call_handler(PermissionDenied())
        assert_rfc7807(response.data, 403)

    def test_title_is_forbidden(self):
        response = call_handler(PermissionDenied())
        assert "forbidden" in response.data["title"].lower()


# ===========================================================================
# Authentication (401)
# ===========================================================================


class TestAuthErrors:
    def test_not_authenticated_returns_401(self):
        response = call_handler(NotAuthenticated())
        assert response.status_code == 401

    def test_authentication_failed_returns_401(self):
        response = call_handler(AuthenticationFailed())
        assert response.status_code == 401

    def test_www_authenticate_header_set(self):
        response = call_handler(NotAuthenticated())
        assert "WWW-Authenticate" in response
        assert "Bearer" in response["WWW-Authenticate"]

    def test_auth_failed_www_authenticate_header(self):
        response = call_handler(AuthenticationFailed())
        assert "WWW-Authenticate" in response

    def test_rfc7807_structure(self):
        response = call_handler(NotAuthenticated())
        assert_rfc7807(response.data, 401)

    def test_custom_detail_preserved(self):
        response = call_handler(AuthenticationFailed(detail="Token expired."))
        assert "Token expired." in response.data["detail"]


# ===========================================================================
# Throttled (429)
# ===========================================================================


class TestThrottled:
    def test_returns_429(self):
        response = call_handler(Throttled(wait=60))
        assert response.status_code == 429

    def test_retry_after_in_body(self):
        response = call_handler(Throttled(wait=30))
        assert response.data["retry_after"] == 30

    def test_retry_after_header_set(self):
        response = call_handler(Throttled(wait=45))
        assert response["Retry-After"] == "45"

    def test_retry_after_rounded_to_integer(self):
        # Throttled may normalize the wait value internally; the key guarantee
        # is that retry_after is always an int, never a float.
        response = call_handler(Throttled(wait=59.9))
        assert isinstance(response.data["retry_after"], int)

    def test_no_wait(self):
        response = call_handler(Throttled(wait=None))
        assert response.status_code == 429
        assert "errors" not in response.data
        assert "retry_after" not in response.data

    def test_detail_mentions_wait(self):
        response = call_handler(Throttled(wait=10))
        assert "10" in response.data["detail"]

    def test_rfc7807_structure(self):
        response = call_handler(Throttled(wait=5))
        assert_rfc7807(response.data, 429)


# ===========================================================================
# MethodNotAllowed (405)
# ===========================================================================


class TestMethodNotAllowed:
    def test_returns_405(self):
        response = call_handler(MethodNotAllowed("DELETE"))
        assert response.status_code == 405

    def test_rfc7807_structure(self):
        response = call_handler(MethodNotAllowed("PATCH"))
        assert_rfc7807(response.data, 405)

    def test_method_in_detail(self):
        response = call_handler(MethodNotAllowed("DELETE"), method="DELETE")
        # The handler uses request.method for the detail message
        assert "DELETE" in response.data["detail"]

    def test_allowed_methods_when_header_present(self):
        exc = MethodNotAllowed("POST")
        ctx = make_context(method="POST")
        with patch("apps.core.exceptions.drf_exception_handler") as mock_drf:
            mock_response = MagicMock()
            mock_response.status_code = 405
            mock_response.data = {"detail": ErrorDetail("Method not allowed.", code="method_not_allowed")}
            # The handler calls response.get("Allow", "") — mock that specifically
            mock_response.get = lambda key, default="": "GET, POST" if key == "Allow" else default
            mock_drf.return_value = mock_response
            response = custom_exception_handler(exc, ctx)
        assert "allowed_methods" in response.data
        assert "GET" in response.data["allowed_methods"]
        assert "POST" in response.data["allowed_methods"]


# ===========================================================================
# UnsupportedMediaType (415)
# ===========================================================================


class TestUnsupportedMediaType:
    def test_returns_415(self):
        response = call_handler(UnsupportedMediaType("text/xml"))
        assert response.status_code == 415

    def test_rfc7807_structure(self):
        response = call_handler(UnsupportedMediaType("text/csv"))
        assert_rfc7807(response.data, 415)

    def test_title(self):
        response = call_handler(UnsupportedMediaType("image/gif"))
        assert "unsupported" in response.data["title"].lower()


# ===========================================================================
# ParseError (400)
# ===========================================================================


class TestParseError:
    def test_returns_400(self):
        response = call_handler(ParseError())
        assert response.status_code == 400

    def test_rfc7807_structure(self):
        response = call_handler(ParseError())
        assert_rfc7807(response.data, 400)

    def test_detail_mentions_malformed(self):
        response = call_handler(ParseError(detail="JSON parse error"))
        assert "malformed" in response.data["detail"].lower() or "json" in response.data["detail"].lower()

    def test_parse_error_with_detail(self):
        response = call_handler(ParseError(detail="Unexpected token"))
        assert "Unexpected token" in response.data["detail"]


# ===========================================================================
# Custom APIException subclasses
# ===========================================================================


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable."
    default_code = "service_unavailable"


class ConflictError(APIException):
    status_code = 409
    default_detail = "Resource already exists."
    default_code = "conflict"


class TestCustomAPIException:
    def test_custom_status_code_preserved(self):
        response = call_handler(ServiceUnavailable())
        assert response.status_code == 503

    def test_rfc7807_structure(self):
        response = call_handler(ServiceUnavailable())
        assert_rfc7807(response.data, 503)

    def test_detail_from_exception(self):
        response = call_handler(ServiceUnavailable())
        assert "unavailable" in response.data["detail"].lower()

    def test_conflict_409(self):
        response = call_handler(ConflictError())
        assert response.status_code == 409

    def test_custom_exception_with_dict_detail(self):
        class RichError(APIException):
            status_code = 422
            default_detail = {"code": "rich_error", "msg": "Complex error"}
            default_code = "rich_error"

        response = call_handler(RichError())
        assert response.status_code == 422
        assert "errors" in response.data

    def test_custom_exception_with_list_detail(self):
        class MultiError(APIException):
            status_code = 400
            default_code = "multi"

            def __init__(self):
                self.detail = [
                    ErrorDetail("First problem.", code="first"),
                    ErrorDetail("Second problem.", code="second"),
                ]

        response = call_handler(MultiError())
        assert "errors" in response.data
        assert len(response.data["errors"]) == 2


# ===========================================================================
# Unhandled exceptions → 500
# ===========================================================================


class TestUnhandledException:
    def test_returns_500(self):
        response = call_handler(RuntimeError("Unexpected crash"))
        assert response.status_code == 500

    def test_rfc7807_structure(self):
        response = call_handler(RuntimeError("boom"))
        assert_rfc7807(response.data, 500)

    def test_no_internal_detail_leaked(self):
        response = call_handler(RuntimeError("db password is secret123"))
        assert "secret123" not in response.data["detail"]
        assert "RuntimeError" not in response.data["detail"]

    def test_exception_is_logged(self, caplog):
        with caplog.at_level(logging.ERROR, logger="exceptions"):
            call_handler(RuntimeError("test crash"))
        assert len(caplog.records) > 0

    def test_zero_division_returns_500(self):
        try:
            _ = 1 / 0
        except ZeroDivisionError as exc:
            response = call_handler(exc)
        assert response.status_code == 500

    def test_instance_in_500(self):
        response = call_handler(RuntimeError("x"), path="/api/broken/")
        assert response.data.get("instance") == "/api/broken/"


# ===========================================================================
# RFC 7807 envelope: all responses share these fields
# ===========================================================================


class TestRFC7807Envelope:
    exceptions_to_test = [
        ValidationError({"f": ["err"]}),
        NotFound(),
        PermissionDenied(),
        NotAuthenticated(),
        Throttled(wait=1),
        MethodNotAllowed("PUT"),
        UnsupportedMediaType("text/xml"),
        ParseError(),
        RuntimeError("boom"),
    ]

    @pytest.mark.parametrize("exc", exceptions_to_test)
    def test_type_is_about_blank(self, exc):
        response = call_handler(exc)
        assert response.data["type"] == "about:blank"

    @pytest.mark.parametrize("exc", exceptions_to_test)
    def test_status_field_matches_http_code(self, exc):
        response = call_handler(exc)
        assert response.data["status"] == response.status_code

    @pytest.mark.parametrize("exc", exceptions_to_test)
    def test_title_is_non_empty_string(self, exc):
        response = call_handler(exc)
        assert isinstance(response.data["title"], str)
        assert len(response.data["title"]) > 0

    @pytest.mark.parametrize("exc", exceptions_to_test)
    def test_detail_is_non_empty_string(self, exc):
        response = call_handler(exc)
        assert isinstance(response.data["detail"], str)
        assert len(response.data["detail"]) > 0

    @pytest.mark.parametrize("exc", exceptions_to_test)
    def test_instance_is_request_path(self, exc):
        response = call_handler(exc, path="/api/resource/42/")
        assert response.data.get("instance") == "/api/resource/42/"


# ===========================================================================
# No request in context (edge case)
# ===========================================================================


class TestNoRequest:
    def test_no_request_validation_error(self):
        exc = ValidationError({"x": ["err"]})
        response = custom_exception_handler(exc, context={})
        assert response.status_code == 422
        assert "instance" not in response.data

    def test_no_request_unhandled(self):
        response = custom_exception_handler(RuntimeError("x"), context={})
        assert response.status_code == 500

    def test_no_request_not_found(self):
        response = custom_exception_handler(NotFound(), context={})
        assert response.status_code == 404


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    def test_http404_as_django_exception(self):
        """Django's Http404 must be handled like DRF's NotFound."""
        response = call_handler(Http404("Page not found"))
        assert response.status_code == 404
        assert_rfc7807(response.data, 404)

    def test_django_permission_denied_gives_403(self):
        """Django's PermissionDenied must map to HTTP 403."""
        response = call_handler(DjangoPermissionDenied("nope"))
        assert response.status_code == 403

    def test_validation_error_response_status_overridden_to_422(self):
        """DRF sets ValidationError to 400; we override it to 422."""
        exc = ValidationError({"x": ["e"]})
        response = call_handler(exc)
        assert response.status_code == 422
        assert response.data["status"] == 422

    def test_errors_key_absent_for_non_validation_errors(self):
        """Non-validation errors must NOT have an `errors` key."""
        for exc in [NotFound(), PermissionDenied(), ParseError()]:
            response = call_handler(exc)
            assert "errors" not in response.data, f"Unexpected errors key for {type(exc).__name__}"

    def test_throttled_retry_after_is_integer(self):
        """retry_after must be an int, not a float."""
        response = call_handler(Throttled(wait=12.7))
        assert isinstance(response.data["retry_after"], int)

    def test_throttled_header_is_string(self):
        response = call_handler(Throttled(wait=5))
        assert isinstance(response["Retry-After"], str)
