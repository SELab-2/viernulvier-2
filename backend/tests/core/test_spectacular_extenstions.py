from unittest.mock import MagicMock

import pytest

from apps.core.spectacular_extensions import ApiKeyAuthenticationScheme


def test_api_key_authentication_scheme_security_definition():
    """get_security_definition must describe the X-API-Key header setup."""
    scheme = ApiKeyAuthenticationScheme(target=MagicMock())

    result = scheme.get_security_definition(auto_schema=None)

    assert result == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Use the `X-API-Key` header to authenticate.",
    }


@pytest.mark.parametrize(
    "attribute, expected",
    [
        ("target_class", "apps.core.authentications.ApiKeyAuthentication"),
        ("name", "ApiKey"),
        ("match_subclasses", True),
    ],
)
def test_api_key_authentication_scheme_metadata(attribute, expected):
    """Class-level metadata should remain stable for schema generation."""
    assert getattr(ApiKeyAuthenticationScheme, attribute) == expected
