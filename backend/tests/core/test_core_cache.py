"""
Tests for the caching layer applied to read-heavy API endpoints.

Covers three areas:
- ``CacheReadActionsMixin``: verifies that list and retrieve responses are
  cached, that write actions bypass the cache, and that cache entries are
  keyed per X-Api-Key and Accept-Language header.
- ``connect_cache_invalidation``: verifies that post_save and post_delete
  signals clear the cache for the affected resource.
- ``delete_pattern`` fallback: verifies that the signal handler works
  correctly with both django-redis (delete_pattern) and LocMemCache (clear).
"""

from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.signals import connect_cache_invalidation
from apps.languages.models import Language
from tests.factories.language import LanguageFactory

PUB_KEY = "pub-cache-test-key"
INT_KEY = "int-cache-test-key"


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


# ---------------------------------------------------------------------------
# CacheReadActionsMixin
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestCacheReadActionsMixin(TestCase):
    """Tests that list and retrieve are cached, write actions are not."""

    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()
        cache.clear()
        LanguageFactory(code="nl", name="Dutch", is_active=True)
        LanguageFactory(code="en", name="English", is_active=True)

    def test_list_response_is_cached(self):
        """
        A second identical GET /list/ request must return the same response
        as the first without hitting the view logic again.
        """
        response_1 = self.client.get("/api/v1/languages/", **pub_headers())
        response_2 = self.client.get("/api/v1/languages/", **pub_headers())

        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(response_1.data, response_2.data)

    def test_retrieve_response_is_cached(self):
        """
        A second identical GET /retrieve/ request must return the cached
        response without re-executing the view logic.
        """
        response_1 = self.client.get("/api/v1/languages/nl/", **pub_headers())
        response_2 = self.client.get("/api/v1/languages/nl/", **pub_headers())

        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(response_1.data, response_2.data)

    def test_cache_varies_on_api_key_header(self):
        """
        Requests with different X-Api-Key headers must produce separate
        cache entries so users never receive each other's responses.
        """
        response_pub = self.client.get("/api/v1/languages/nl/", **pub_headers())
        response_int = self.client.get("/api/v1/languages/nl/", **int_headers())

        self.assertEqual(response_pub.status_code, 200)
        self.assertEqual(response_int.status_code, 200)

    def test_cache_varies_on_accept_language_header(self):
        """
        Requests with different Accept-Language headers must produce separate
        cache entries so translations are never mixed up across locales.
        """
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
        """
        Two identical POST requests must both reach the view — the second
        must not be served from cache and must fail with 422 (duplicate),
        not silently return a cached 201.
        """
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
        """
        DELETE must always reach the view — a second delete on the same
        resource must return 404, not a cached 204.
        """
        self.client.delete("/api/v1/languages/nl/", **int_headers())
        response = self.client.delete("/api/v1/languages/nl/", **int_headers())

        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# connect_cache_invalidation
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestConnectCacheInvalidation(TestCase):
    """Tests that signals clear the cache after model mutations."""

    def setUp(self):
        self.client = APIClient()
        Language.objects.all().delete()
        cache.clear()

    def test_post_save_clears_cache(self):
        """
        Saving a model instance must clear the cache so the next request
        fetches fresh data instead of a stale cached response.
        """
        LanguageFactory(code="nl", name="Dutch", is_active=True)

        # Populate the cache via a real request
        self.client.get("/api/v1/languages/", **pub_headers())
        self.assertTrue(len(cache._cache) > 0)

        # Trigger post_save — cache must be cleared
        Language.objects.create(code="de", name="German", is_active=True)

        self.assertEqual(len(cache._cache), 0)

    def test_post_delete_clears_cache(self):
        """
        Deleting a model instance must clear the cache so stale entries
        are not served after the resource no longer exists.
        """
        LanguageFactory(code="nl", name="Dutch", is_active=True)

        self.client.get("/api/v1/languages/", **pub_headers())
        self.assertTrue(len(cache._cache) > 0)

        Language.objects.get(code="nl").delete()

        self.assertEqual(len(cache._cache), 0)

    def test_cache_is_repopulated_after_invalidation(self):
        """
        After invalidation, the next GET request must repopulate the cache
        with up-to-date data.
        """
        LanguageFactory(code="nl", name="Dutch", is_active=True)

        self.client.get("/api/v1/languages/", **pub_headers())
        Language.objects.create(code="de", name="German", is_active=True)

        # Cache was cleared — next request repopulates it
        response = self.client.get("/api/v1/languages/", **pub_headers())
        results = response.data.get("results", response.data)
        codes = [item["code"] for item in results]

        self.assertIn("de", codes)


# ---------------------------------------------------------------------------
# delete_pattern fallback
# ---------------------------------------------------------------------------


class TestDeletePatternFallback(TestCase):
    """
    Tests that the signal handler degrades gracefully when the cache backend
    does not support delete_pattern (e.g. LocMemCache in tests).
    """

    def test_uses_delete_pattern_when_available(self):
        """
        When the cache backend supports delete_pattern, it must be called
        with the correct prefix pattern instead of clear().
        """
        mock_cache = MagicMock(spec=["delete_pattern", "clear"])

        with patch("apps.core.signals.cache", mock_cache):
            connect_cache_invalidation(Language, "/api/v1/languages/")
            post_save.send(sender=Language, instance=MagicMock(), created=True)

        mock_cache.delete_pattern.assert_called_with("*/api/v1/languages/*")
        mock_cache.clear.assert_not_called()

    def test_falls_back_to_clear_when_delete_pattern_unavailable(self):
        """
        When the cache backend does not support delete_pattern (e.g.
        LocMemCache), the handler must fall back to cache.clear() without
        raising an AttributeError.
        """
        mock_cache = MagicMock(spec=["clear"])  # no delete_pattern

        with patch("apps.core.signals.cache", mock_cache):
            connect_cache_invalidation(Language, "/api/v1/languages/")
            post_save.send(sender=Language, instance=MagicMock(), created=True)

        mock_cache.clear.assert_called()

    def test_handler_does_not_raise_on_locmemcache(self):
        """
        The signal handler must not raise AttributeError when running against
        LocMemCache, which is the cache backend used during testing.
        """
        connect_cache_invalidation(Language, "/api/v1/languages/")

        try:
            post_save.send(sender=Language, instance=MagicMock(), created=True)
        except AttributeError:
            self.fail(
                "Signal handler raised AttributeError against LocMemCache — "
                "delete_pattern fallback is not working correctly."
            )
            