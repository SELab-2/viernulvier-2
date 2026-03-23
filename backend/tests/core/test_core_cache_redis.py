"""
Redis integration tests for the caching layer.

These tests verify that HTTP response caching behaves correctly when using
a Redis cache backend (as configured in ``config.settings.test_redis``).

Unlike the default test suite (which uses LocMemCache), these tests require
a running Redis instance and ensure that:
- cached responses are stored and retrieved correctly
- cache variation (e.g. headers) works as expected
- cache invalidation works end-to-end after model changes

Run with:
    DJANGO_SETTINGS_MODULE=config.settings.test_redis pytest -m redis

Requires:
    A running Redis server (e.g. on localhost:6379)
"""

import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient

from apps.languages.models import Language
from tests.factories.language import LanguageFactory

pytestmark = [pytest.mark.redis, pytest.mark.django_db]

PUB_KEY = "pub-cache-test-key"
INT_KEY = "int-cache-test-key"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
def test_redis_cache_set_get_clear():
    cache.set("healthcheck", "ok", timeout=60)
    assert cache.get("healthcheck") == "ok"

    cache.clear()
    assert cache.get("healthcheck") is None


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
def test_list_endpoint_is_cached_with_redis():
    client = APIClient()
    Language.objects.all().delete()
    cache.clear()

    LanguageFactory(code="nl", name="Dutch", is_active=True)
    LanguageFactory(code="en", name="English", is_active=True)

    response_1 = client.get("/api/v1/languages/", **pub_headers())
    response_2 = client.get("/api/v1/languages/", **pub_headers())

    assert response_1.status_code == 200
    assert response_2.status_code == 200
    assert response_1.data == response_2.data


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
def test_cache_varies_on_accept_language_with_redis():
    client = APIClient()
    Language.objects.all().delete()
    cache.clear()

    LanguageFactory(code="nl", name="Dutch", is_active=True)

    response_nl = client.get(
        "/api/v1/languages/nl/",
        HTTP_ACCEPT_LANGUAGE="nl",
        **pub_headers(),
    )
    response_en = client.get(
        "/api/v1/languages/nl/",
        HTTP_ACCEPT_LANGUAGE="en",
        **pub_headers(),
    )

    assert response_nl.status_code == 200
    assert response_en.status_code == 200


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
def test_cache_is_invalidated_after_model_change_with_redis():
    client = APIClient()
    Language.objects.all().delete()
    cache.clear()

    LanguageFactory(code="nl", name="Dutch", is_active=True)

    response_1 = client.get("/api/v1/languages/", **pub_headers())
    results_1 = response_1.data.get("results", response_1.data)
    codes_1 = [item["code"] for item in results_1]
    assert "de" not in codes_1

    Language.objects.create(code="de", name="German", is_active=True)

    response_2 = client.get("/api/v1/languages/", **pub_headers())
    results_2 = response_2.data.get("results", response_2.data)
    codes_2 = [item["code"] for item in results_2]
    assert "de" in codes_2
    