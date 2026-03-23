"""
Global pytest configuration and shared fixtures.

Fixtures defined here are automatically available to all tests in the project
without explicit imports. The ``autouse=True`` fixtures apply to every test
unless overridden at the module or class level.
"""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
