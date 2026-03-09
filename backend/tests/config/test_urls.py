import importlib
from django.test import TestCase, Client, override_settings
from django.urls import clear_url_caches, resolve, get_resolver
from django.conf import settings

import config.urls
from config.health import health


class URLTests(TestCase):
    def setUp(self):
        self.client = Client()
        clear_url_caches()
        importlib.reload(config.urls)

    def tearDown(self):
        clear_url_caches()
        importlib.reload(config.urls)

    def test_health_url_resolves(self):
        """Health endpoint resolves to the correct view"""
        resolver = resolve("/health")
        self.assertEqual(resolver.func, health)

    def test_health_endpoint_returns_response(self):
        """Health endpoint returns 200"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_admin_url_exists(self):
        """Admin login page exists"""
        response = self.client.get("/admin/")
        self.assertIn(response.status_code, [200, 302])

    def test_api_urls_included(self):
        """API route exists (basic check)"""
        response = self.client.get("/api/")
        self.assertNotEqual(response.status_code, 404)

    def test_debug_toolbar_urls_not_included_in_production(self):
        """Debug toolbar route should NOT be available when DEBUG is False"""
        importlib.reload(config.urls)
        clear_url_caches()

        response = self.client.get("/__debug__/")
        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=True, INSTALLED_APPS=["debug_toolbar"])
    def test_debug_urls_block_included(self):
        """Check that the debug toolbar block is included in urlpatterns"""
        # Clear cache and reload
        clear_url_caches()
        importlib.reload(config.urls)

        # Check that '__debug__/' is in the string representation
        url_patterns = str(get_resolver().url_patterns)
        self.assertIn("__debug__", url_patterns)

    @override_settings(DEBUG=True, MEDIA_URL="/media/", MEDIA_ROOT="/tmp/media/")
    def test_media_urls_included_in_debug(self):
        """Static media serving should be added to urlpatterns in DEBUG mode"""
        importlib.reload(config.urls)
        clear_url_caches()

        url_patterns = get_resolver().url_patterns

        media_pattern_found = any(hasattr(p, "pattern") and "media/" in str(p.pattern) for p in url_patterns)
        self.assertTrue(media_pattern_found, "Media pattern should be in urlpatterns when DEBUG=True")

    @override_settings(DEBUG=False)
    def test_media_urls_not_included_in_production(self):
        """Static media serving should NOT be in urlpatterns in production"""
        importlib.reload(config.urls)
        clear_url_caches()

        url_patterns = get_resolver().url_patterns
        media_pattern_found = any(hasattr(p, "pattern") and "media/" in str(p.pattern) for p in url_patterns)
        self.assertFalse(media_pattern_found, "Media pattern should NOT be in urlpatterns when DEBUG=False")
