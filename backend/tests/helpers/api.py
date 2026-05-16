"""Reusable API test helpers to reduce repetitive test plumbing.

This module provides:
- Centralized API key configuration for testing
- Header helper functions for API authentication
- URL generation utilities for viewset testing
- BaseViewSetTestCase class for consistent viewset test structure
"""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

# Centralized API keys for all tests
PUBLIC_API_KEY = "public-test-api-key"
INTERNAL_API_KEY = "internal-test-api-key"


# ============================================================================
# API Test Helpers
# ============================================================================

DEFAULT_WRONG_API_KEY = "completely-wrong-key"


def api_key_headers(api_key: str) -> dict[str, str]:
    """Build Django test-client headers for X-API-Key authentication."""
    return {"HTTP_X_API_KEY": api_key}


def public_headers(public_api_key: str | None = None) -> dict[str, str]:
    """Build headers for the configured or provided public API key."""
    return api_key_headers(public_api_key or settings.PUBLIC_API_KEY)


def internal_headers(internal_api_key: str | None = None) -> dict[str, str]:
    """Build headers for the configured or provided internal API key."""
    return api_key_headers(internal_api_key or settings.INTERNAL_API_KEY)


def wrong_headers(value: str = DEFAULT_WRONG_API_KEY) -> dict[str, str]:
    """Build headers with an intentionally invalid API key."""
    return api_key_headers(value)


def paginated_results(response):
    """Return list payload for both paginated and non-paginated responses."""
    if isinstance(response.data, dict):
        return response.data.get("results", response.data)
    return response.data


def v1_list_url(resource: str) -> str:
    """Return the named v1 list URL for a registered viewset resource."""
    return reverse(f"v1:{resource}-list")


def v1_detail_url(resource: str, **kwargs) -> str:
    """Return the named v1 detail URL for a registered viewset resource."""
    return reverse(f"v1:{resource}-detail", kwargs=kwargs)


class BaseViewSetTestCase(TestCase):
    """Base test case for ViewSet API tests.

    Provides:
    - APIClient instance
    - Resource-specific URL methods (list_url, detail_url)
    - Header helper methods (pub_headers, int_headers, wrong_headers)

    Subclasses must define `resource_name` attribute for URL generation.
    """

    resource_name: str = None

    def setUp(self) -> None:
        self.client = APIClient()

    def list_url(self) -> str:
        """Get the list URL for this resource."""
        if not self.resource_name:
            raise ValueError(f"{self.__class__.__name__} must define resource_name")
        return v1_list_url(self.resource_name)

    def detail_url(self, **kwargs) -> str:
        """Get the detail URL for this resource."""
        if not self.resource_name:
            raise ValueError(f"{self.__class__.__name__} must define resource_name")
        return v1_detail_url(self.resource_name, **kwargs)

    def pub_headers(self) -> dict[str, str]:
        """Get public API headers."""
        return public_headers()

    def int_headers(self) -> dict[str, str]:
        """Get internal API headers."""
        return internal_headers()

    def wrong_headers(self) -> dict[str, str]:
        """Get invalid API headers."""
        return wrong_headers()
