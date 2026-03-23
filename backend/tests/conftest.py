"""
Global pytest configuration and shared fixtures.

Fixtures defined here are automatically available to all tests in the project
without explicit imports. The ``autouse=True`` fixtures apply to every test
unless overridden at the module or class level.
"""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache(request):
    if "redis" in request.keywords:
        try:
            cache.set("pytest-redis-check", "ok", timeout=5)
            assert cache.get("pytest-redis-check") == "ok"
        except Exception:
            pytest.skip("Redis is not running for redis-marked tests.")

    cache.clear()
