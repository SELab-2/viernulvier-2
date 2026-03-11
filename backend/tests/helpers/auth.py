"""
Shared authentication helpers for view tests.

Provides module-level pytest fixtures that patch ``ApiKeyAuthentication``
so view tests run without a real API key in the database.

Usage - import the fixtures you need at the top of a test file::

    from tests.helpers.auth import internal_client, public_client, anon_client
"""

from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIClient

_AUTH_PATH = "apps.core.authentications.ApiKeyAuthentication.authenticate"


@pytest.fixture
def internal_client():
    with patch(_AUTH_PATH, return_value=(AnonymousUser(), "internal")):
        yield APIClient()


@pytest.fixture
def public_client():
    with patch(_AUTH_PATH, return_value=(AnonymousUser(), "public")):
        yield APIClient()


@pytest.fixture
def anon_client():
    with patch(_AUTH_PATH, return_value=None):
        yield APIClient()
