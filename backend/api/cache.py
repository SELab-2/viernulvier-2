"""Caching utilities for Django API views.

Provides TTL constants, API view caching decorators, and API-cache invalidation helpers.
"""

from __future__ import annotations

from functools import wraps
import logging
from typing import TYPE_CHECKING, Any

from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

CACHE_TTL_SHORT = 60 * 5  # 5 minutes
CACHE_TTL_MEDIUM = 60 * 15  # 15 minutes
CACHE_TTL_LONG = 60 * 60  # 1 hour

API_CACHE_KEY_PREFIX = "api"
API_CACHE_VARY_HEADERS = ("Accept-Language",)
API_CACHE_DELETE_PATTERN = "api:*"


def cache_get_view(timeout: int = CACHE_TTL_SHORT) -> Callable[[type], type]:
    """Decorator to cache a full class-based view dispatch for a specified duration."""
    return method_decorator(cache_page(timeout), name="dispatch")


def cache_api_view(timeout: int = CACHE_TTL_MEDIUM) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache an API handler while falling back safely if cache is unavailable."""

    def decorator(view_func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = args[1] if len(args) > 1 else kwargs.get("request")

            # Build a simple cache key from method + path + language
            lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
            cache_key = f"{API_CACHE_KEY_PREFIX}:{request.method}:{request.get_full_path()}:{lang}"

            try:
                cached = cache.get(cache_key)
                if cached is not None:
                    return cached
            except Exception:
                logger.exception("API cache read failed; bypassing cache")
                return view_func(*args, **kwargs)

            response = view_func(*args, **kwargs)

            try:
                cache.set(cache_key, response, timeout)
            except Exception:
                logger.exception("API cache write failed; returning uncached response")

            return response

        return wrapper

    return decorator


def clear_api_cache() -> int | None:
    """Clear cached API responses without flushing unrelated cache entries.

    With django-redis this uses ``delete_pattern`` so only API response cache
    keys are removed. For other cache backends, it falls back to ``cache.clear``.
    """
    delete_pattern = getattr(cache, "delete_pattern", None)

    if callable(delete_pattern):
        return delete_pattern(API_CACHE_DELETE_PATTERN)

    cache.clear()
    return None
