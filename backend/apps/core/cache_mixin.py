"""Provides explicit cache-key based response caching for DRF viewsets."""

import hashlib
import json

from django.conf import settings
from django.core.cache import cache
from django.utils.cache import patch_vary_headers
from rest_framework.response import Response

CACHE_TTL = getattr(settings, "CACHE_TTL", 60 * 5)


def _jsonable(value):
    """Convert values to a stable JSON-serializable representation."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _stable_hash(data):
    raw = json.dumps(_jsonable(data), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _build_cache_key(prefix, action, request, kwargs):
    query_params = {}
    for key in sorted(request.query_params.keys()):
        values = request.query_params.getlist(key)
        query_params[key] = values if len(values) > 1 else request.query_params.get(key)

    key_data = {
        "action": action,
        "api_key": request.headers.get("X-Api-Key", ""),
        "accept_language": request.headers.get("Accept-Language", ""),
        "query_params": query_params,
        "kwargs": kwargs,
    }
    digest = _stable_hash(key_data)
    return f"{prefix}:{action}:{digest}"


def cache_read_actions(prefix, ttl=CACHE_TTL):
    """
    Class decorator that caches DRF list/retrieve responses using explicit,
    predictable cache keys.

    Example prefix: "api:languages"
    """
    if not prefix:
        raise ValueError("cache_read_actions requires a non-empty prefix")

    def decorator(cls):
        for action in ("list", "retrieve"):
            original = getattr(cls, action)

            def wrapped(self, request, *args, __original=original, __action=action, **kwargs):
                cache_key = _build_cache_key(prefix, __action, request, kwargs)
                cached = cache.get(cache_key)
                if cached is not None:
                    response = Response(cached["data"], status=cached["status"])
                    for header, value in cached.get("headers", {}).items():
                        response[header] = value
                    patch_vary_headers(response, ["X-Api-Key", "Accept-Language"])
                    return response

                response = __original(self, request, *args, **kwargs)
                patch_vary_headers(response, ["X-Api-Key", "Accept-Language"])

                if 200 <= response.status_code < 300:
                    cache.set(
                        cache_key,
                        {
                            "data": response.data,
                            "status": response.status_code,
                            "headers": {},
                        },
                        timeout=ttl,
                    )

                return response

            setattr(cls, action, wrapped)

        return cls

    return decorator
