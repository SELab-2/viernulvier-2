"""Caching utilities for Django API views.

Provides TTL constants, API view caching decorators, and API-cache invalidation helpers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

CACHE_TTL_SHORT = 60 * 5  # 5 minutes
CACHE_TTL_MEDIUM = 60 * 15  # 15 minutes
CACHE_TTL_LONG = 60 * 60  # 1 hour

API_CACHE_KEY_PREFIX = "api"
API_CACHE_VARY_HEADERS = ("Accept-Language",)
API_CACHE_DELETE_PATTERN = "*api*"


def cache_get_view(timeout: int = CACHE_TTL_SHORT) -> Callable[[type], type]:
    """Decorator to cache a full class-based view dispatch for a specified duration."""
    return method_decorator(cache_page(timeout), name="dispatch")


def cache_api_view(timeout: int = CACHE_TTL_MEDIUM) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache an API handler while keeping language-aware responses separate.

    Django's ``cache_page`` caches per URL, including query parameters. The
    additional ``Vary: Accept-Language`` ensures endpoints with language-aware
    ordering/search annotations do not reuse a response generated for another
    preferred language.
    """

    def decorator(view_func: Callable[..., Any]) -> Callable[..., Any]:
        return cache_page(timeout, key_prefix=API_CACHE_KEY_PREFIX)(vary_on_headers(*API_CACHE_VARY_HEADERS)(view_func))

    return decorator


def clear_api_cache() -> int | None:
    """Clear cached API responses without flushing unrelated cache entries.

    With django-redis this uses ``delete_pattern`` so only API response cache
    keys are removed. For other cache backends, it falls back to ``cache.clear``.
    """
    delete_pattern = getattr(cache, "delete_pattern", None)

    try:
        if callable(delete_pattern):
            deleted = delete_pattern(API_CACHE_DELETE_PATTERN)
            logger.info("Deleted %s API cache keys", deleted)
            return deleted

        cache.clear()
        return None

    except Exception:
        logger.exception("API cache clear failed; continuing without cache invalidation")
        return None
