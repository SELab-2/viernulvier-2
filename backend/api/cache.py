"""Caching utilities for Django API views.

Provides TTL constants and a decorator to cache class-based views using Django's cache framework.
"""

from collections.abc import Callable

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

CACHE_TTL_SHORT = 60 * 5  # 5 minutes
CACHE_TTL_MEDIUM = 60 * 15  # 15 minutes
CACHE_TTL_LONG = 60 * 60  # 1 hour


def cache_get_view(timeout: int = CACHE_TTL_SHORT) -> Callable[[type], type]:
    """Decorator to cache a view for a specified duration."""
    return method_decorator(cache_page(timeout), name="dispatch")
