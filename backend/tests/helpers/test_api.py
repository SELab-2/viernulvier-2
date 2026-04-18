"""Tests for shared API test helpers."""

from types import SimpleNamespace

from django.test import TestCase, override_settings
import pytest

from tests.helpers.api import (
    DEFAULT_WRONG_API_KEY,
    BaseViewSetTestCase,
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


@override_settings(PUBLIC_API_KEY="pub-from-settings")
def test_public_headers_uses_settings_value_when_arg_missing():
    assert public_headers() == {"HTTP_X_API_KEY": "pub-from-settings"}


def test_internal_headers_delegates_to_api_key_headers():
    assert internal_headers("int") == {"HTTP_X_API_KEY": "int"}


@override_settings(INTERNAL_API_KEY="int-from-settings")
def test_internal_headers_uses_settings_value_when_arg_missing():
    assert internal_headers() == {"HTTP_X_API_KEY": "int-from-settings"}


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


def test_paginated_results_returns_dict_when_results_key_missing():
    response = SimpleNamespace(data={"detail": "ok"})
    assert paginated_results(response) == {"detail": "ok"}


def test_v1_list_url_builds_named_route():
    assert v1_list_url("language") == "/api/v1/languages/"


def test_v1_detail_url_builds_named_route_with_kwargs():
    assert v1_detail_url("language", code="nl") == "/api/v1/languages/nl/"


class TestBaseViewSetTestCase(TestCase):
    """Tests for BaseViewSetTestCase class."""

    def test_list_url_raises_when_resource_name_not_defined(self):
        """Should raise ValueError when resource_name is not defined."""

        class InvalidViewSet(BaseViewSetTestCase):
            pass

        with pytest.raises(ValueError, match="must define resource_name"):
            InvalidViewSet().list_url()

    def test_detail_url_raises_when_resource_name_not_defined(self):
        """Should raise ValueError when resource_name is not defined."""

        class InvalidViewSet(BaseViewSetTestCase):
            pass

        with pytest.raises(ValueError, match="must define resource_name"):
            InvalidViewSet().detail_url(pk=1)

    def test_list_url_returns_correct_url(self):
        """Should return correct list URL when resource_name is defined."""

        class ValidViewSet(BaseViewSetTestCase):
            resource_name = "language"

        assert ValidViewSet().list_url() == "/api/v1/languages/"

    def test_detail_url_returns_correct_url(self):
        """Should return correct detail URL when resource_name is defined."""

        class ValidViewSet(BaseViewSetTestCase):
            resource_name = "language"

        assert ValidViewSet().detail_url(code="nl") == "/api/v1/languages/nl/"

    @override_settings(PUBLIC_API_KEY="test-pub-key")
    def test_pub_headers_returns_public_headers(self):
        """Should return public API headers."""

        class ValidViewSet(BaseViewSetTestCase):
            resource_name = "language"

        assert ValidViewSet().pub_headers() == {"HTTP_X_API_KEY": "test-pub-key"}

    @override_settings(INTERNAL_API_KEY="test-int-key")
    def test_int_headers_returns_internal_headers(self):
        """Should return internal API headers."""

        class ValidViewSet(BaseViewSetTestCase):
            resource_name = "language"

        assert ValidViewSet().int_headers() == {"HTTP_X_API_KEY": "test-int-key"}

    def test_wrong_headers_returns_invalid_headers(self):
        """Should return invalid API headers."""

        class ValidViewSet(BaseViewSetTestCase):
            resource_name = "language"

        headers = ValidViewSet().wrong_headers()
        assert "HTTP_X_API_KEY" in headers
