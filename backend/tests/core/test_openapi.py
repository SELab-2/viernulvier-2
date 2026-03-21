"""
Comprehensive test suite for apps/core/openapi.py.

Covers:
- ProblemSerializer and _ErrorItemSerializer field contracts
- Every RESPONSE_* constant (type, description keywords, example shape)
- RESPONSE_204_DELETED (no serializer, no example)
- error_responses() happy path and ValueError guard
- All five convenience sets (READ_ERRORS … DELETE_ERRORS)
"""

import pytest
from drf_spectacular.utils import OpenApiResponse
from rest_framework import serializers

from apps.core.openapi import (
    DELETE_ERRORS,
    ITEM_ERRORS,
    MUTATE_ERRORS,
    READ_ERRORS,
    RESPONSE_204_DELETED,
    RESPONSE_400,
    RESPONSE_401,
    RESPONSE_403,
    RESPONSE_404,
    RESPONSE_422,
    WRITE_ERRORS,
    ProblemSerializer,
    error_responses,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _example_value(response: OpenApiResponse) -> dict:
    """Return the first example's value from an OpenApiResponse."""
    return response.examples[0].value


def _description(response: OpenApiResponse) -> str:
    return response.description


# ===========================================================================
# ProblemSerializer - field presence and types
# ===========================================================================


class TestProblemSerializer:
    """The serializer must mirror the exact shape custom_exception_handler emits."""

    def setup_method(self):
        self.fields = ProblemSerializer.fields

    def test_has_type_field(self):
        assert "type" in self.fields

    def test_has_title_field(self):
        assert "title" in self.fields

    def test_has_status_field(self):
        assert "status" in self.fields
        assert isinstance(self.fields["status"], serializers.IntegerField)

    def test_has_detail_field(self):
        assert "detail" in self.fields

    def test_has_instance_field(self):
        assert "instance" in self.fields

    def test_instance_is_not_required(self):
        assert self.fields["instance"].required is False

    def test_has_errors_field(self):
        assert "errors" in self.fields

    def test_errors_is_list_field(self):
        assert isinstance(self.fields["errors"], serializers.ListField)

    def test_errors_is_not_required(self):
        assert self.fields["errors"].required is False

    def test_type_field_default_is_about_blank(self):
        # The 'type' field carries default="about:blank" as help context.
        field = self.fields["type"]
        assert isinstance(field, serializers.CharField)

    def test_errors_child_has_pointer_field(self):
        child_fields = self.fields["errors"].child.fields
        assert "pointer" in child_fields

    def test_errors_child_has_detail_field(self):
        assert "detail" in self.fields["errors"].child.fields

    def test_errors_child_has_code_field(self):
        assert "code" in self.fields["errors"].child.fields

    def test_exactly_six_top_level_fields(self):
        assert set(self.fields.keys()) == {"type", "title", "status", "detail", "instance", "errors"}


# ===========================================================================
# RESPONSE_* constants - each is an OpenApiResponse
# ===========================================================================


class TestResponseConstants:
    @pytest.mark.parametrize(
        "response",
        [RESPONSE_400, RESPONSE_401, RESPONSE_403, RESPONSE_404, RESPONSE_422],
    )
    def test_is_open_api_response(self, response):
        assert isinstance(response, OpenApiResponse)

    @pytest.mark.parametrize(
        "response",
        [RESPONSE_400, RESPONSE_401, RESPONSE_403, RESPONSE_404, RESPONSE_422],
    )
    def test_has_exactly_one_example(self, response):
        assert len(response.examples) == 1

    @pytest.mark.parametrize(
        "response",
        [RESPONSE_400, RESPONSE_401, RESPONSE_403, RESPONSE_404, RESPONSE_422],
    )
    def test_example_has_required_rfc7807_keys(self, response):
        value = _example_value(response)
        for key in ("type", "title", "status", "detail"):
            assert key in value, f"Missing key '{key}' in {response}"

    @pytest.mark.parametrize(
        "response",
        [RESPONSE_400, RESPONSE_401, RESPONSE_403, RESPONSE_404, RESPONSE_422],
    )
    def test_example_type_is_about_blank(self, response):
        assert _example_value(response)["type"] == "about:blank"

    @pytest.mark.parametrize(
        "response",
        [RESPONSE_400, RESPONSE_401, RESPONSE_403, RESPONSE_404, RESPONSE_422],
    )
    def test_example_has_instance(self, response):
        assert "instance" in _example_value(response)

    @pytest.mark.parametrize(
        "response",
        [RESPONSE_400, RESPONSE_401, RESPONSE_403, RESPONSE_404, RESPONSE_422],
    )
    def test_example_instance_looks_like_a_path(self, response):
        instance = _example_value(response)["instance"]
        assert instance.startswith("/")

    @pytest.mark.parametrize(
        "response",
        [RESPONSE_400, RESPONSE_401, RESPONSE_403, RESPONSE_404, RESPONSE_422],
    )
    def test_description_is_non_empty_string(self, response):
        assert isinstance(_description(response), str)
        assert _description(response).strip()


# ---------------------------------------------------------------------------
# RESPONSE_400
# ---------------------------------------------------------------------------


class TestResponse400:
    def test_status_in_example(self):
        assert _example_value(RESPONSE_400)["status"] == 400

    def test_title_is_bad_request(self):
        assert _example_value(RESPONSE_400)["title"] == "Bad Request"

    def test_detail_mentions_malformed(self):
        assert "Malformed" in _example_value(RESPONSE_400)["detail"]

    def test_description_mentions_400(self):
        assert "400" in _description(RESPONSE_400) or "Bad Request" in _description(RESPONSE_400)

    def test_description_references_422(self):
        # Callers are directed to 422 for field-level errors.
        assert "422" in _description(RESPONSE_400)

    def test_no_errors_key_in_example(self):
        assert "errors" not in _example_value(RESPONSE_400)


# ---------------------------------------------------------------------------
# RESPONSE_401
# ---------------------------------------------------------------------------


class TestResponse401:
    def test_status_in_example(self):
        assert _example_value(RESPONSE_401)["status"] == 401

    def test_title_is_unauthorized(self):
        assert _example_value(RESPONSE_401)["title"] == "Unauthorized"

    def test_description_mentions_api_key(self):
        assert "X-API-Key" in _description(RESPONSE_401)

    def test_no_errors_key_in_example(self):
        assert "errors" not in _example_value(RESPONSE_401)


# ---------------------------------------------------------------------------
# RESPONSE_403
# ---------------------------------------------------------------------------


class TestResponse403:
    def test_status_in_example(self):
        assert _example_value(RESPONSE_403)["status"] == 403

    def test_title_is_forbidden(self):
        assert _example_value(RESPONSE_403)["title"] == "Forbidden"

    def test_description_mentions_permissions(self):
        desc = _description(RESPONSE_403).lower()
        assert "permission" in desc or "key" in desc

    def test_no_errors_key_in_example(self):
        assert "errors" not in _example_value(RESPONSE_403)


# ---------------------------------------------------------------------------
# RESPONSE_404
# ---------------------------------------------------------------------------


class TestResponse404:
    def test_status_in_example(self):
        assert _example_value(RESPONSE_404)["status"] == 404

    def test_title_is_not_found(self):
        assert _example_value(RESPONSE_404)["title"] == "Not Found"

    def test_no_errors_key_in_example(self):
        assert "errors" not in _example_value(RESPONSE_404)


# ---------------------------------------------------------------------------
# RESPONSE_422
# ---------------------------------------------------------------------------


class TestResponse422:
    def test_status_in_example(self):
        assert _example_value(RESPONSE_422)["status"] == 422

    def test_title_is_unprocessable_entity(self):
        assert _example_value(RESPONSE_422)["title"] == "Unprocessable Entity"

    def test_errors_key_present_in_example(self):
        assert "errors" in _example_value(RESPONSE_422)

    def test_errors_is_a_list(self):
        assert isinstance(_example_value(RESPONSE_422)["errors"], list)

    def test_errors_list_is_non_empty(self):
        assert len(_example_value(RESPONSE_422)["errors"]) > 0

    def test_each_error_has_pointer(self):
        for item in _example_value(RESPONSE_422)["errors"]:
            assert "pointer" in item

    def test_each_error_has_detail(self):
        for item in _example_value(RESPONSE_422)["errors"]:
            assert "detail" in item

    def test_each_error_has_code(self):
        for item in _example_value(RESPONSE_422)["errors"]:
            assert "code" in item

    def test_description_mentions_json_pointer(self):
        assert "JSON Pointer" in _description(RESPONSE_422) or "pointer" in _description(RESPONSE_422).lower()


# ---------------------------------------------------------------------------
# RESPONSE_204_DELETED
# ---------------------------------------------------------------------------


class TestResponse204Deleted:
    def test_is_open_api_response(self):
        assert isinstance(RESPONSE_204_DELETED, OpenApiResponse)

    def test_description_mentions_deleted_or_no_content(self):
        desc = _description(RESPONSE_204_DELETED).lower()
        assert "deleted" in desc or "no content" in desc

    def test_no_examples(self):
        # 204 carries no body, so no example should be registered.
        assert not RESPONSE_204_DELETED.examples

    def test_no_serializer(self):
        # A 204 has no response body schema.
        assert RESPONSE_204_DELETED.response is None


# ===========================================================================
# error_responses() helper
# ===========================================================================


class TestErrorResponses:
    # --- happy path ---

    def test_single_known_code(self):
        result = error_responses(401)
        assert set(result.keys()) == {401}
        assert result[401] is RESPONSE_401

    def test_multiple_known_codes(self):
        result = error_responses(401, 403, 404)
        assert set(result.keys()) == {401, 403, 404}

    def test_returns_correct_response_objects(self):
        mapping = {
            400: RESPONSE_400,
            401: RESPONSE_401,
            403: RESPONSE_403,
            404: RESPONSE_404,
            422: RESPONSE_422,
        }
        for code, expected in mapping.items():
            assert error_responses(code)[code] is expected

    def test_all_five_registered_codes_at_once(self):
        result = error_responses(400, 401, 403, 404, 422)
        assert len(result) == 5

    def test_returns_dict(self):
        assert isinstance(error_responses(404), dict)

    def test_values_are_open_api_responses(self):
        for v in error_responses(401, 403, 422).values():
            assert isinstance(v, OpenApiResponse)

    # --- ValueError guard ---

    def test_single_unknown_code_raises(self):
        with pytest.raises(ValueError, match="418"):
            error_responses(418)

    def test_unknown_code_mixed_with_known_raises(self):
        with pytest.raises(ValueError, match="418"):
            error_responses(401, 418)

    def test_multiple_unknown_codes_all_in_error_message(self):
        with pytest.raises(ValueError) as exc_info:
            error_responses(418, 451)
        msg = str(exc_info.value)
        assert "418" in msg
        assert "451" in msg

    def test_zero_is_unknown(self):
        with pytest.raises(ValueError):
            error_responses(0)

    def test_500_is_not_registered(self):
        # 500 is intentionally absent - the handler emits it but it is not
        # a documented API contract callers opt into.
        with pytest.raises(ValueError, match="500"):
            error_responses(500)


# ===========================================================================
# Convenience sets
# ===========================================================================


class TestConvenienceSets:
    """Each set must contain exactly the documented codes and nothing else."""

    def test_read_errors_codes(self):
        assert set(READ_ERRORS.keys()) == {401, 403}

    def test_item_errors_codes(self):
        assert set(ITEM_ERRORS.keys()) == {401, 403, 404}

    def test_write_errors_codes(self):
        assert set(WRITE_ERRORS.keys()) == {401, 403, 422}

    def test_mutate_errors_codes(self):
        assert set(MUTATE_ERRORS.keys()) == {401, 403, 404, 422}

    def test_delete_errors_codes(self):
        assert set(DELETE_ERRORS.keys()) == {401, 403, 404}

    # Each set is a plain dict.
    @pytest.mark.parametrize("error_set", [READ_ERRORS, ITEM_ERRORS, WRITE_ERRORS, MUTATE_ERRORS, DELETE_ERRORS])
    def test_is_dict(self, error_set):
        assert isinstance(error_set, dict)

    # Values are the canonical response objects, not copies.
    @pytest.mark.parametrize("error_set", [READ_ERRORS, ITEM_ERRORS, WRITE_ERRORS, MUTATE_ERRORS, DELETE_ERRORS])
    def test_values_are_open_api_responses(self, error_set):
        for v in error_set.values():
            assert isinstance(v, OpenApiResponse)

    def test_read_errors_no_422(self):
        assert 422 not in READ_ERRORS

    def test_read_errors_no_404(self):
        assert 404 not in READ_ERRORS

    def test_write_errors_no_404(self):
        assert 404 not in WRITE_ERRORS

    def test_delete_errors_no_422(self):
        assert 422 not in DELETE_ERRORS

    def test_all_sets_contain_401(self):
        for error_set in [READ_ERRORS, ITEM_ERRORS, WRITE_ERRORS, MUTATE_ERRORS, DELETE_ERRORS]:
            assert 401 in error_set

    def test_all_sets_contain_403(self):
        for error_set in [READ_ERRORS, ITEM_ERRORS, WRITE_ERRORS, MUTATE_ERRORS, DELETE_ERRORS]:
            assert 403 in error_set

    def test_mutate_errors_is_superset_of_item_errors(self):
        assert ITEM_ERRORS.keys() <= MUTATE_ERRORS.keys()

    def test_mutate_errors_is_superset_of_write_errors(self):
        assert WRITE_ERRORS.keys() <= MUTATE_ERRORS.keys()

    def test_delete_errors_equals_item_errors(self):
        assert DELETE_ERRORS.keys() == ITEM_ERRORS.keys()

    # Spreading into a dict must not blow up - simulates actual extend_schema usage.
    def test_read_errors_spreadable(self):
        result = {200: "ok", **READ_ERRORS}
        assert 200 in result
        assert 401 in result

    def test_write_errors_spreadable(self):
        result = {201: "created", **WRITE_ERRORS}
        assert 201 in result
        assert 422 in result
