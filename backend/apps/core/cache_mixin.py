"""Provides a mixin to apply HTTP response caching to list and retrieve actions of Django REST Framework viewsets."""

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

CACHE_TTL = 60 * 5  # 5 minutes (how long to cache responses for)


def cache_read_actions(ttl=CACHE_TTL):
    """
    Class decorator that applies HTTP response caching to list and retrieve.
    Cache varies on Authorization and Accept-Language so users never receive
    each other's data and translations stay correct.
    """
    decorators = [
        method_decorator(cache_page(ttl)),
        method_decorator(vary_on_headers("Authorization", "Accept-Language")),
    ]

    def decorator(cls):
        for action in ("list", "retrieve"):
            for deco in reversed(decorators):
                setattr(cls, action, deco(getattr(cls, action)))
        return cls

    return decorator
