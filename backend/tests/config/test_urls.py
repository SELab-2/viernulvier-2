from django.test import TestCase, Client, override_settings
from django.urls import clear_url_caches, resolve
import importlib
import config.urls
from config.health import health


class URLTests(TestCase):
    def setUp(self):
        self.client = Client()

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
        self.assertIn(response.status_code, [200, 302])  # redirect to login is fine

    def test_api_urls_included(self):
        """API route exists (basic check)"""
        response = self.client.get("/api/")
        # We don't know exact behavior, but it should not be 404 if urls are included
        self.assertNotEqual(response.status_code, 404)