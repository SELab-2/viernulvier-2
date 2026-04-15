"""Reusable API test helpers to reduce repetitive test plumbing."""

from django.urls import reverse

DEFAULT_WRONG_API_KEY = "completely-wrong-key"


def api_key_headers(api_key: str) -> dict[str, str]:
    return {"HTTP_X_API_KEY": api_key}


def public_headers(public_api_key: str) -> dict[str, str]:
    return api_key_headers(public_api_key)


def internal_headers(internal_api_key: str) -> dict[str, str]:
    return api_key_headers(internal_api_key)


def wrong_headers(value: str = DEFAULT_WRONG_API_KEY) -> dict[str, str]:
    return api_key_headers(value)


def paginated_results(response):
    """Return list payload for both paginated and non-paginated responses."""
    if isinstance(response.data, dict):
        return response.data.get("results", response.data)
    return response.data


def v1_list_url(resource: str) -> str:
    return reverse(f"v1:{resource}-list")


def v1_detail_url(resource: str, **kwargs) -> str:
    return reverse(f"v1:{resource}-detail", kwargs=kwargs)


