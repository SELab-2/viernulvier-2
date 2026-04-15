"""Tests for shared API test helpers."""

from types import SimpleNamespace

from tests.helpers.api import (
    DEFAULT_WRONG_API_KEY,
    api_key_headers,
    internal_headers,
    paginated_results,
    public_headers,
    v1_detail_url,
    v1_list_url,
    wrong_headers,
)


def test_api_key_headers_builds_http_x_api_key_dict():
    assert api_key_headers("abc") == {"HTTP_X_API_KEY": "abc"}


def test_public_headers_delegates_to_api_key_headers():
    assert public_headers("pub") == {"HTTP_X_API_KEY": "pub"}


def test_internal_headers_delegates_to_api_key_headers():
    assert internal_headers("int") == {"HTTP_X_API_KEY": "int"}


def test_wrong_headers_uses_default_wrong_key():
    assert wrong_headers() == {"HTTP_X_API_KEY": DEFAULT_WRONG_API_KEY}


def test_wrong_headers_accepts_custom_value():
    assert wrong_headers("override") == {"HTTP_X_API_KEY": "override"}


def test_paginated_results_returns_results_list_when_present():
    response = SimpleNamespace(data={"count": 2, "results": [{"id": 1}, {"id": 2}]})
    assert paginated_results(response) == [{"id": 1}, {"id": 2}]


def test_paginated_results_returns_data_for_non_paginated_payload():
    response = SimpleNamespace(data=[{"id": 1}])
    assert paginated_results(response) == [{"id": 1}]


def test_v1_list_url_builds_named_route():
    assert v1_list_url("language") == "/api/v1/languages/"


def test_v1_detail_url_builds_named_route_with_kwargs():
    assert v1_detail_url("language", code="nl") == "/api/v1/languages/nl/"

