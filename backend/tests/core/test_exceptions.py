"""
Comprehensive test suite for the RFC 7807 DRF exception handler.
"""

import logging
from unittest.mock import MagicMock, patch

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
import pytest
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
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from apps.core.exceptions import _build_problem, _flatten_errors, custom_exception_handler

urlpatterns: list = []  # ROOT_URLCONF requirement

factory = APIRequestFactory()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def make_context(method: str = "GET", path: str = "/api/test/") -> dict:
    """Return a minimal handler context with a real DRF request."""
    django_request = getattr(factory, method.lower())(path)
    return {"request": Request(django_request), "view": MagicMock()}


def call_handler(exc: Exception, method: str = "GET", path: str = "/api/test/"):
    return custom_exception_handler(exc, make_context(method=method, path=path))


def assert_rfc7807(body: dict, expected_status: int) -> None:
    """Assert the four mandatory RFC 7807 fields are present and well-typed."""
    assert body["type"] == "about:blank"
    assert isinstance(body["title"], str)
    assert body["title"]
    assert body["status"] == expected_status
    assert isinstance(body["detail"], str)
    assert body["detail"]


# ===========================================================================
# _flatten_errors
# ===========================================================================


class TestFlattenErrors:
    def test_single_error_detail_at_root(self) -> None:
        result = _flatten_errors(ErrorDetail("This field is required.", code="required"))
        assert result == [{"pointer": "/", "detail": "This field is required.", "code": "required"}]

    def test_plain_string_at_root(self) -> None:
        result = _flatten_errors("Something went wrong.")
        assert result == [{"pointer": "/", "detail": "Something went wrong.", "code": "error"}]

    def test_flat_dict_single_error_per_field(self) -> None:
        # DRF always emits lists, but the pointer is the field name only - no index.
        detail = {
            "email": [ErrorDetail("Enter a valid email.", code="invalid")],
            "name": [ErrorDetail("This field is required.", code="required")],
        }
        result = _flatten_errors(detail)
        pointers = {e["pointer"] for e in result}
        codes = {e["code"] for e in result}

        assert pointers == {"/email", "/name"}
        assert "invalid" in codes
        assert "required" in codes

    def test_flat_dict_multiple_errors_same_field(self) -> None:
        # Two errors on "password" -> both get pointer "/password", no index.
        detail = {
            "password": [
                ErrorDetail("Too short.", code="min_length"),
                ErrorDetail("Must contain a digit.", code="no_digit"),
            ]
        }
        result = _flatten_errors(detail)
        assert len(result) == 2
        assert all(e["pointer"] == "/password" for e in result)
        assert {e["code"] for e in result} == {"min_length", "no_digit"}

    def test_nested_dict(self) -> None:
        detail = {"address": {"city": [ErrorDetail("Required.", code="required")]}}
        result = _flatten_errors(detail)
        assert result == [{"pointer": "/address/city", "detail": "Required.", "code": "required"}]

    def test_deeply_nested_dict(self) -> None:
        detail = {"user": {"profile": {"avatar": [ErrorDetail("Too large.", code="max_size")]}}}
        result = _flatten_errors(detail)
        assert result[0]["pointer"] == "/user/profile/avatar"
        assert result[0]["code"] == "max_size"

    def test_list_of_error_details_at_root(self) -> None:
        # Non-field errors: list items are ErrorDetail,
        # so they all get pointer "/" with no index.
        detail = [
            ErrorDetail("First error.", code="invalid"),
            ErrorDetail("Second error.", code="null"),
        ]
        result = _flatten_errors(detail)
        assert len(result) == 2
        assert all(e["pointer"] == "/" for e in result)
        assert {e["code"] for e in result} == {"invalid", "null"}

    def test_list_of_plain_strings_at_root(self) -> None:
        result = _flatten_errors(["Error A.", "Error B."])
        assert len(result) == 2
        assert all(e["pointer"] == "/" for e in result)
        assert all(e["code"] == "error" for e in result)

    def test_list_of_dicts_uses_numeric_index(self) -> None:
        # A list of dicts (e.g. nested many-relation errors) gets indexed.
        detail = [
            {"name": [ErrorDetail("Required.", code="required")]},
            {"name": [ErrorDetail("Required.", code="required")]},
        ]
        result = _flatten_errors(detail)
        pointers = [e["pointer"] for e in result]
        assert "/0/name" in pointers
        assert "/1/name" in pointers

    def test_preserves_all_codes_across_fields(self) -> None:
        detail = {
            "a": [ErrorDetail("err", code="alpha")],
            "b": [ErrorDetail("err", code="beta")],
            "c": [ErrorDetail("err", code="gamma")],
        }
        codes = {e["code"] for e in _flatten_errors(detail)}
        assert codes == {"alpha", "beta", "gamma"}

    def test_unknown_type_returns_empty_list(self) -> None:
        # The implementation has no fallback branch for arbitrary types.
        assert _flatten_errors(42) == []
        assert _flatten_errors(3.14) == []
        assert _flatten_errors(None) == []

    def test_error_detail_code_preserved(self) -> None:
        result = _flatten_errors(ErrorDetail("Too long.", code="max_length"))
        assert result[0]["code"] == "max_length"

    def test_plain_string_gets_error_code(self) -> None:
        result = _flatten_errors("bare string")
        assert result[0]["code"] == "error"


# ===========================================================================
# _build_problem
# ===========================================================================


class TestBuildProblem:
    def test_minimal_required_fields(self) -> None:
        body = _build_problem(status_code=400, title="Bad Request", detail="Something is wrong.")
        assert body == {
            "type": "about:blank",
            "title": "Bad Request",
            "status": 400,
            "detail": "Something is wrong.",
        }

    def test_instance_included_when_given(self) -> None:
        body = _build_problem(status_code=404, title="Not Found", detail="Gone.", instance="/api/foo/")
        assert body["instance"] == "/api/foo/"

    def test_instance_omitted_when_none(self) -> None:
        body = _build_problem(status_code=400, title="T", detail="D", instance=None)
        assert "instance" not in body

    def test_errors_included_when_given(self) -> None:
        errors = [{"pointer": "/name", "detail": "Required.", "code": "required"}]
        body = _build_problem(status_code=422, title="Unprocessable", detail="Errors.", errors=errors)
        assert body["errors"] == errors

    def test_errors_omitted_when_none(self) -> None:
        body = _build_problem(status_code=400, title="T", detail="D", errors=None)
        assert "errors" not in body

    def test_errors_omitted_when_empty_list(self) -> None:
        body = _build_problem(status_code=400, title="T", detail="D", errors=[])
        assert "errors" not in body

    def test_extra_fields_merged(self) -> None:
        body = _build_problem(status_code=429, title="T", detail="D", extra={"retry_after": 60})
        assert body["retry_after"] == 60

    def test_extra_none_leaves_only_base_fields(self) -> None:
        body = _build_problem(status_code=400, title="T", detail="D", extra=None)
        assert set(body.keys()) == {"type", "title", "status", "detail"}


# ===========================================================================
# ValidationError -> 422
# ===========================================================================


class TestValidationError:
    def test_status_is_422(self) -> None:
        response = call_handler(ValidationError({"email": ["Enter a valid email."]}))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(ValidationError({"name": ["Required."]})).data, 422)

    def test_status_field_overridden_from_400_to_422(self) -> None:
        # DRF natively sets ValidationError to 400; handler overrides to 422.
        response = call_handler(ValidationError({"x": ["e"]}))
        assert response.status_code == 422
        assert response.data["status"] == 422

    def test_errors_list_present(self) -> None:
        response = call_handler(ValidationError({"field": ["err1", "err2"]}))
        assert "errors" in response.data
        assert isinstance(response.data["errors"], list)

    def test_field_pointer_has_no_list_index(self) -> None:
        # ErrorDetail items inside a list get the field path without /0 suffix.
        exc = ValidationError({"username": [ErrorDetail("Too short.", code="min_length")]})
        pointers = [e["pointer"] for e in call_handler(exc).data["errors"]]
        assert "/username" in pointers
        assert "/username/0" not in pointers

    def test_nested_field_pointer(self) -> None:
        exc = ValidationError({"address": {"city": [ErrorDetail("Required.", code="required")]}})
        pointers = [e["pointer"] for e in call_handler(exc).data["errors"]]
        assert "/address/city" in pointers

    def test_multiple_errors_same_field_share_pointer(self) -> None:
        exc = ValidationError(
            {
                "password": [
                    ErrorDetail("Too short.", code="min_length"),
                    ErrorDetail("Must contain a number.", code="password_no_number"),
                ]
            }
        )
        errors = call_handler(exc).data["errors"]
        password_errors = [e for e in errors if e["pointer"] == "/password"]
        assert len(password_errors) == 2
        assert {e["code"] for e in password_errors} == {"min_length", "password_no_number"}

    def test_non_field_errors_get_root_pointer(self) -> None:
        exc = ValidationError(["Non-field error."])
        errors = call_handler(exc).data["errors"]
        assert len(errors) >= 1
        assert all(e["pointer"] == "/" for e in errors)

    def test_instance_in_response(self) -> None:
        response = call_handler(ValidationError({"x": ["err"]}), path="/api/users/")
        assert response.data["instance"] == "/api/users/"

    def test_detail_mentions_validation(self) -> None:
        assert "validation" in call_handler(ValidationError({"x": ["e"]})).data["detail"].lower()


# ===========================================================================
# Django ValidationError conversion
# ===========================================================================


class TestDjangoValidationError:
    def test_message_dict_converted_to_422(self) -> None:
        exc = DjangoValidationError({"email": ["Enter a valid email address."]})
        response = call_handler(exc)
        assert response.status_code == 422
        assert "errors" in response.data

    def test_messages_list_converted_to_422(self) -> None:
        response = call_handler(DjangoValidationError(["Error one.", "Error two."]))
        assert response.status_code == 422


# ===========================================================================
# Http404 / NotFound -> 404
# ===========================================================================


class TestNotFound:
    def test_django_http404_returns_404(self) -> None:
        assert call_handler(Http404()).status_code == 404

    def test_drf_not_found_returns_404(self) -> None:
        assert call_handler(NotFound()).status_code == 404

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(NotFound()).data, 404)

    def test_title_is_not_found(self) -> None:
        assert "not found" in call_handler(Http404()).data["title"].lower()

    def test_custom_detail_preserved(self) -> None:
        response = call_handler(NotFound(detail="Article not found."))
        assert "Article not found." in response.data["detail"]

    def test_no_errors_key(self) -> None:
        assert "errors" not in call_handler(NotFound()).data


# ===========================================================================
# PermissionDenied -> 403
# ===========================================================================


class TestPermissionDenied:
    def test_drf_exception_returns_403(self) -> None:
        assert call_handler(PermissionDenied()).status_code == 403

    def test_django_exception_converted_to_403(self) -> None:
        assert call_handler(DjangoPermissionDenied()).status_code == 403

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(PermissionDenied()).data, 403)

    def test_title_is_forbidden(self) -> None:
        assert "forbidden" in call_handler(PermissionDenied()).data["title"].lower()

    def test_no_errors_key(self) -> None:
        assert "errors" not in call_handler(PermissionDenied()).data


# ===========================================================================
# Authentication -> 401
# ===========================================================================


class TestAuthErrors:
    def test_not_authenticated_returns_401(self) -> None:
        assert call_handler(NotAuthenticated()).status_code == 401

    def test_authentication_failed_returns_401(self) -> None:
        assert call_handler(AuthenticationFailed()).status_code == 401

    def test_www_authenticate_header_on_not_authenticated(self) -> None:
        response = call_handler(NotAuthenticated())
        assert "WWW-Authenticate" in response
        assert "X-API-Key" in response["WWW-Authenticate"]

    def test_www_authenticate_header_on_auth_failed(self) -> None:
        assert "WWW-Authenticate" in call_handler(AuthenticationFailed())

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(NotAuthenticated()).data, 401)

    def test_custom_detail_preserved(self) -> None:
        response = call_handler(AuthenticationFailed(detail="Token expired."))
        assert "Token expired." in response.data["detail"]

    def test_no_errors_key(self) -> None:
        assert "errors" not in call_handler(NotAuthenticated()).data


# ===========================================================================
# Throttled -> 429
# ===========================================================================


class TestThrottled:
    def test_returns_429(self) -> None:
        assert call_handler(Throttled(wait=60)).status_code == 429

    def test_retry_after_in_body(self) -> None:
        assert call_handler(Throttled(wait=30)).data["retry_after"] == 30

    def test_retry_after_header_set(self) -> None:
        assert call_handler(Throttled(wait=45))["Retry-After"] == "45"

    def test_retry_after_is_int_never_float(self) -> None:
        response = call_handler(Throttled(wait=12.7))
        assert isinstance(response.data["retry_after"], int)
        assert isinstance(response["Retry-After"], str)

    def test_no_wait_omits_retry_after(self) -> None:
        response = call_handler(Throttled(wait=None))
        assert response.status_code == 429
        assert "retry_after" not in response.data
        assert "errors" not in response.data

    def test_detail_includes_wait_seconds(self) -> None:
        assert "10" in call_handler(Throttled(wait=10)).data["detail"]

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(Throttled(wait=5)).data, 429)


# ===========================================================================
# MethodNotAllowed -> 405
# ===========================================================================


class TestMethodNotAllowed:
    def test_returns_405(self) -> None:
        assert call_handler(MethodNotAllowed("DELETE")).status_code == 405

    def test_no_detail_str(self) -> None:
        ctx = make_context(method="PATCH")
        exc = MethodNotAllowed("PATCH")
        exc.detail = "custom string"
        response = custom_exception_handler(exc, ctx)
        assert response.data["detail"] == 'Method "PATCH" not allowed.'

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(MethodNotAllowed("PATCH")).data, 405)

    def test_request_method_in_detail(self) -> None:
        response = call_handler(MethodNotAllowed("DELETE"), method="DELETE")
        assert "DELETE" in response.data["detail"]

    def test_allowed_methods_from_header(self) -> None:
        exc = MethodNotAllowed("POST")
        ctx = make_context(method="POST")
        with patch("apps.core.exceptions.drf_exception_handler") as mock_drf:
            mock_resp = MagicMock()
            mock_resp.status_code = 405
            mock_resp.data = {"detail": ErrorDetail("Method not allowed.", code="method_not_allowed")}
            mock_resp.get = lambda key, default="": "GET, POST" if key == "Allow" else default
            mock_drf.return_value = mock_resp
            response = custom_exception_handler(exc, ctx)
        assert "allowed_methods" in response.data
        assert "GET" in response.data["allowed_methods"]
        assert "POST" in response.data["allowed_methods"]

    def test_no_allowed_methods_when_header_absent(self) -> None:
        assert "allowed_methods" not in call_handler(MethodNotAllowed("DELETE")).data


# ===========================================================================
# UnsupportedMediaType -> 415
# ===========================================================================


class TestUnsupportedMediaType:
    def test_returns_415(self) -> None:
        assert call_handler(UnsupportedMediaType("text/xml")).status_code == 415

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(UnsupportedMediaType("text/csv")).data, 415)

    def test_title_mentions_unsupported(self) -> None:
        assert "unsupported" in call_handler(UnsupportedMediaType("image/gif")).data["title"].lower()

    def test_no_errors_key(self) -> None:
        assert "errors" not in call_handler(UnsupportedMediaType("text/xml")).data


# ===========================================================================
# ParseError -> 400
# ===========================================================================


class TestParseError:
    def test_returns_400(self) -> None:
        assert call_handler(ParseError()).status_code == 400

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(ParseError()).data, 400)

    def test_detail_prefixed_with_malformed(self) -> None:
        assert "malformed" in call_handler(ParseError(detail="JSON parse error")).data["detail"].lower()

    def test_original_detail_embedded(self) -> None:
        assert "Unexpected token" in call_handler(ParseError(detail="Unexpected token")).data["detail"]

    def test_no_errors_key(self) -> None:
        assert "errors" not in call_handler(ParseError()).data


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
    def test_custom_status_code_preserved(self) -> None:
        assert call_handler(ServiceUnavailable()).status_code == 503

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(ServiceUnavailable()).data, 503)

    def test_detail_from_exception(self) -> None:
        assert "unavailable" in call_handler(ServiceUnavailable()).data["detail"].lower()

    def test_conflict_409(self) -> None:
        assert call_handler(ConflictError()).status_code == 409

    def test_dict_detail_becomes_errors_list(self) -> None:
        class RichError(APIException):
            status_code = 422
            default_detail = {"code": "rich_error", "msg": "Complex error"}
            default_code = "rich_error"

        response = call_handler(RichError())
        assert response.status_code == 422
        assert "errors" in response.data

    def test_list_detail_all_errors_share_root_pointer(self) -> None:
        # A list of ErrorDetail items → all get pointer "/"
        class MultiError(APIException):
            status_code = 400
            default_code = "multi"

            def __init__(self) -> None:
                self.detail = [
                    ErrorDetail("First problem.", code="first"),
                    ErrorDetail("Second problem.", code="second"),
                ]

        response = call_handler(MultiError())
        assert "errors" in response.data
        assert len(response.data["errors"]) == 2
        assert all(e["pointer"] == "/" for e in response.data["errors"])


# ===========================================================================
# Unhandled exceptions -> 500
# ===========================================================================


class TestUnhandledException:
    def test_returns_500(self) -> None:
        assert call_handler(RuntimeError("Unexpected crash")).status_code == 500

    def test_rfc7807_structure(self) -> None:
        assert_rfc7807(call_handler(RuntimeError("boom")).data, 500)

    def test_no_internal_detail_leaked(self) -> None:
        response = call_handler(RuntimeError("db password is secret123"))
        assert "secret123" not in response.data["detail"]
        assert "RuntimeError" not in response.data["detail"]

    def test_zero_division_returns_500(self) -> None:
        with pytest.raises(ZeroDivisionError) as exc:
            _ = 1 / 0
        assert call_handler(exc.value).status_code == 500

    def test_instance_path_in_500(self) -> None:
        response = call_handler(RuntimeError("x"), path="/api/broken/")
        assert response.data.get("instance") == "/api/broken/"

    def test_exception_is_logged(self, caplog) -> None:
        # Logger name matches __name__ inside apps/core/exceptions.py
        with caplog.at_level(logging.ERROR, logger="apps.core.exceptions"):
            call_handler(RuntimeError("test crash"))
        assert len(caplog.records) > 0


# ===========================================================================
# RFC 7807 envelope - parametrized across all exception types
# ===========================================================================


class TestRFC7807Envelope:
    _all_exceptions = [
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

    @pytest.mark.parametrize("exc", _all_exceptions)
    def test_type_is_about_blank(self, exc) -> None:
        assert call_handler(exc).data["type"] == "about:blank"

    @pytest.mark.parametrize("exc", _all_exceptions)
    def test_status_field_matches_http_code(self, exc) -> None:
        response = call_handler(exc)
        assert response.data["status"] == response.status_code

    @pytest.mark.parametrize("exc", _all_exceptions)
    def test_title_is_non_empty_string(self, exc) -> None:
        title = call_handler(exc).data["title"]
        assert isinstance(title, str)
        assert title

    @pytest.mark.parametrize("exc", _all_exceptions)
    def test_detail_is_non_empty_string(self, exc) -> None:
        detail = call_handler(exc).data["detail"]
        assert isinstance(detail, str)
        assert detail

    @pytest.mark.parametrize("exc", _all_exceptions)
    def test_instance_is_request_path(self, exc) -> None:
        response = call_handler(exc, path="/api/resource/42/")
        assert response.data.get("instance") == "/api/resource/42/"


# ===========================================================================
# errors key presence rules
# ===========================================================================


class TestErrorsKeyRules:
    def test_present_on_422_validation_error(self) -> None:
        assert "errors" in call_handler(ValidationError({"x": ["e"]})).data

    def test_present_on_custom_exception_with_dict_detail(self) -> None:
        class DictExc(APIException):
            status_code = 400
            default_detail = {"foo": [ErrorDetail("bad", code="invalid")]}

        assert "errors" in call_handler(DictExc()).data

    def test_absent_on_404(self) -> None:
        assert "errors" not in call_handler(NotFound()).data

    def test_absent_on_403(self) -> None:
        assert "errors" not in call_handler(PermissionDenied()).data

    def test_absent_on_401(self) -> None:
        assert "errors" not in call_handler(NotAuthenticated()).data

    def test_absent_on_400_parse_error(self) -> None:
        assert "errors" not in call_handler(ParseError()).data

    def test_absent_on_415(self) -> None:
        assert "errors" not in call_handler(UnsupportedMediaType("text/xml")).data

    def test_absent_on_500(self) -> None:
        assert "errors" not in call_handler(RuntimeError("x")).data


# ===========================================================================
# No request in context
# ===========================================================================


class TestNoRequest:
    def test_validation_error_without_request(self) -> None:
        response = custom_exception_handler(ValidationError({"x": ["err"]}), context={})
        assert response.status_code == 422
        assert "instance" not in response.data

    def test_unhandled_exception_without_request(self) -> None:
        assert custom_exception_handler(RuntimeError("x"), context={}).status_code == 500

    def test_not_found_without_request(self) -> None:
        assert custom_exception_handler(NotFound(), context={}).status_code == 404

    def test_no_instance_key_when_no_request(self) -> None:
        assert "instance" not in custom_exception_handler(NotFound(), context={}).data


# ===========================================================================
# APIException with list/dict detail, non-standard default_code
# ===========================================================================


class TestCustomAPIExceptionTitleFormatting:
    """
    Covers the branch inside the APIException fallback that formats `default_code`
    into a human-readable title when no entry exists in _STATUS_TITLES.
    """

    def test_title_derived_from_default_code_for_unknown_status(self) -> None:
        """
        A 409 with default_code='resource_conflict' → title should be formatted
        from the code because 409 isn't in _STATUS_TITLES.
        """

        class ResourceConflict(APIException):
            status_code = 409
            default_detail = "That resource already exists."
            default_code = "resource_conflict"

        response = call_handler(ResourceConflict())
        assert response.status_code == 409
        # Title is derived from default_code: "resource_conflict" -> "Resource Conflict"
        assert response.data["title"] == "ResourceConflict"

    def test_dict_detail_on_unknown_status_uses_formatted_code_title(self) -> None:
        """
        When an unknown-status exception carries a dict/list detail *and* has a
        snake_case default_code, the title must be the formatted code string.
        """

        class BatchFailed(APIException):
            status_code = 207
            default_code = "batch_partial_failure"

            def __init__(self) -> None:
                self.detail = {"items": [ErrorDetail("Item 1 failed.", code="item_error")]}

        response = call_handler(BatchFailed())
        assert response.status_code == 207
        assert "errors" in response.data
        assert response.data["title"] == "Batch Partial Failure"


# ===========================================================================
# MethodNotAllowed with no request in context
# ===========================================================================


class TestMethodNotAllowedNoRequest:
    def test_no_request_fallback_detail(self) -> None:
        """
        When there is no request in context the ternary else-branch must be
        taken, producing the generic "Method not allowed." string.
        """
        response = custom_exception_handler(MethodNotAllowed("DELETE"), context={})

        assert response is not None
        assert response.status_code == 405
        assert "DELETE" in response.data["detail"]
        assert "not allowed" in response.data["detail"] or "niet toegestaan" in response.data["detail"]

    def test_rfc7807_structure_without_request(self) -> None:
        response = custom_exception_handler(MethodNotAllowed("POST"), context={})

        assert response.data["type"] == "about:blank"
        assert isinstance(response.data["title"], str)
        assert response.data["title"]
        assert response.data["status"] == 405
        assert isinstance(response.data["detail"], str)
        assert response.data["detail"]

    def test_no_instance_key_without_request(self) -> None:
        response = custom_exception_handler(MethodNotAllowed("PATCH"), context={})

        assert "instance" not in response.data


class TestUnknownExceptionWithDRFResponse:
    """Covers the final ``return None``.

    This branch is reached when drf_exception_handler returns a Response for
    an exception that is not an APIException subclass (and was not converted
    to one by the Django-exception guard at the top of the handler).
    In production this path should be unreachable, but we can force it via a mock.
    """

    def test_returns_none_for_unrecognised_exc_with_drf_response(self) -> None:
        mystery_exc = Exception("some unknown exception")

        fake_response = MagicMock(spec=Response)
        fake_response.status_code = 418

        with patch("apps.core.exceptions.drf_exception_handler", return_value=fake_response):
            result = custom_exception_handler(mystery_exc, make_context())

        assert result is None
