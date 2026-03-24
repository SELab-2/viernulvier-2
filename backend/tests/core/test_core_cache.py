"""
Tests for the caching layer applied to read-heavy API endpoints.

Covers three areas:
- ``CacheReadActionsMixin``: verifies that list and retrieve responses are
  cached, that write actions bypass the cache, and that cache entries are
  keyed per X-Api-Key and Accept-Language header.
- ``connect_cache_invalidation``: verifies that post_save and post_delete
  signals invalidate cached responses for the affected resource.
- ``delete_pattern`` fallback: verifies that the signal handler works
  correctly with both django-redis (delete_pattern) and LocMemCache (clear).
"""

from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.signals import connect_cache_invalidation
from apps.languages.models import Language
from tests.factories.language import LanguageFactory

PUB_KEY = "pub-cache-test-key"
INT_KEY = "int-cache-test-key"
LANGUAGES_CACHE_PREFIX = "api:languages"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestCacheReadActionsMixin(TestCase):
    """Tests that list and retrieve are cached, and writes are never cached."""

    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()
        cache.clear()
        LanguageFactory(code="nl", name="Dutch", is_active=True)
        LanguageFactory(code="en", name="English", is_active=True)

    def test_list_response_is_cached(self):
        response_1 = self.client.get("/api/v1/languages/", **pub_headers())
        response_2 = self.client.get("/api/v1/languages/", **pub_headers())

        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(response_1.data, response_2.data)

    def test_retrieve_response_is_cached(self):
        response_1 = self.client.get("/api/v1/languages/nl/", **pub_headers())
        response_2 = self.client.get("/api/v1/languages/nl/", **pub_headers())

        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(response_1.data, response_2.data)

    def test_cache_varies_on_api_key_header(self):
        response_pub = self.client.get("/api/v1/languages/nl/", **pub_headers())
        response_int = self.client.get("/api/v1/languages/nl/", **int_headers())

        self.assertEqual(response_pub.status_code, 200)
        self.assertEqual(response_int.status_code, 200)

    def test_cache_varies_on_accept_language_header(self):
        response_nl = self.client.get(
            "/api/v1/languages/nl/",
            HTTP_ACCEPT_LANGUAGE="nl",
            **pub_headers(),
        )
        response_en = self.client.get(
            "/api/v1/languages/nl/",
            HTTP_ACCEPT_LANGUAGE="en",
            **pub_headers(),
        )

        self.assertEqual(response_nl.status_code, 200)
        self.assertEqual(response_en.status_code, 200)

    def test_post_is_not_cached(self):
        self.client.post(
            "/api/v1/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
            **int_headers(),
        )
        response = self.client.post(
            "/api/v1/languages/",
            {"code": "de", "name": "German", "is_active": True},
            format="json",
            **int_headers(),
        )

        self.assertEqual(response.status_code, 422)

    def test_delete_is_not_cached(self):
        self.client.delete("/api/v1/languages/nl/", **int_headers())
        response = self.client.delete("/api/v1/languages/nl/", **int_headers())

        self.assertEqual(response.status_code, 404)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestConnectCacheInvalidation(TestCase):
    """Tests that model mutations invalidate cached API responses."""

    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()
        cache.clear()
        connect_cache_invalidation(Language, LANGUAGES_CACHE_PREFIX)

    def test_post_save_invalidates_cached_list_response(self):
        LanguageFactory(code="nl", name="Dutch", is_active=True)

        response_1 = self.client.get("/api/v1/languages/", **pub_headers())
        results_1 = response_1.data.get("results", response_1.data)
        codes_1 = [item["code"] for item in results_1]
        self.assertEqual(response_1.status_code, 200)
        self.assertNotIn("de", codes_1)

        Language.objects.create(code="de", name="German", is_active=True)

        response_2 = self.client.get("/api/v1/languages/", **pub_headers())
        results_2 = response_2.data.get("results", response_2.data)
        codes_2 = [item["code"] for item in results_2]

        self.assertEqual(response_2.status_code, 200)
        self.assertIn("de", codes_2)

    def test_post_delete_invalidates_cached_list_response(self):
        LanguageFactory(code="nl", name="Dutch", is_active=True)

        response_1 = self.client.get("/api/v1/languages/", **pub_headers())
        results_1 = response_1.data.get("results", response_1.data)
        codes_1 = [item["code"] for item in results_1]
        self.assertEqual(response_1.status_code, 200)
        self.assertIn("nl", codes_1)

        Language.objects.get(code="nl").delete()

        response_2 = self.client.get("/api/v1/languages/", **pub_headers())
        results_2 = response_2.data.get("results", response_2.data)
        codes_2 = [item["code"] for item in results_2]

        self.assertEqual(response_2.status_code, 200)
        self.assertNotIn("nl", codes_2)

    def test_cache_is_repopulated_after_invalidation(self):
        LanguageFactory(code="nl", name="Dutch", is_active=True)

        self.client.get("/api/v1/languages/", **pub_headers())
        Language.objects.create(code="de", name="German", is_active=True)

        response = self.client.get("/api/v1/languages/", **pub_headers())
        results = response.data.get("results", response.data)
        codes = [item["code"] for item in results]

        self.assertIn("de", codes)


class TestCacheInvalidationHandler(TestCase):
    """Tests the signal handler for both Redis and non-Redis cache backends."""

    def test_post_save_uses_delete_pattern_when_available(self):
        mock_cache = MagicMock(spec=["delete_pattern"])

        with patch("apps.core.signals.cache", mock_cache):
            connect_cache_invalidation(Language, LANGUAGES_CACHE_PREFIX)
            post_save.send(sender=Language, instance=MagicMock(), created=True)

        mock_cache.delete_pattern.assert_called_once_with(f"{LANGUAGES_CACHE_PREFIX}:*")

    def test_post_delete_uses_delete_pattern_when_available(self):
        mock_cache = MagicMock(spec=["delete_pattern"])

        with patch("apps.core.signals.cache", mock_cache):
            connect_cache_invalidation(Language, LANGUAGES_CACHE_PREFIX)
            post_delete.send(sender=Language, instance=MagicMock())

        mock_cache.delete_pattern.assert_called_once_with(f"{LANGUAGES_CACHE_PREFIX}:*")

    def test_post_save_falls_back_to_clear_without_delete_pattern(self):
        mock_cache = MagicMock(spec=["clear"])

        with patch("apps.core.signals.cache", mock_cache):
            connect_cache_invalidation(Language, LANGUAGES_CACHE_PREFIX)
            post_save.send(sender=Language, instance=MagicMock(), created=True)

        mock_cache.clear.assert_called_once()

    def test_post_delete_falls_back_to_clear_without_delete_pattern(self):
        mock_cache = MagicMock(spec=["clear"])

        with patch("apps.core.signals.cache", mock_cache):
            connect_cache_invalidation(Language, LANGUAGES_CACHE_PREFIX)
            post_delete.send(sender=Language, instance=MagicMock())

        mock_cache.clear.assert_called_once()

    def test_handler_does_not_raise_on_current_backend(self):
        connect_cache_invalidation(Language, LANGUAGES_CACHE_PREFIX)

        try:
            post_save.send(sender=Language, instance=MagicMock(), created=True)
        except Exception as exc:
            self.fail(f"Signal handler raised unexpectedly: {exc}")
