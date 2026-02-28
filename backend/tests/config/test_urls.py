import importlib
import sys
import types
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from django.urls import clear_url_caches


def _reload_config_urls_module():
	clear_url_caches()
	sys.modules.pop("config.urls", None)
	return importlib.import_module("config.urls")


def _install_fake_debug_toolbar():
	debug_toolbar_module = types.ModuleType("debug_toolbar")
	debug_toolbar_urls_module = types.ModuleType("debug_toolbar.urls")
	setattr(debug_toolbar_urls_module, "urlpatterns", [])
	setattr(debug_toolbar_module, "urls", debug_toolbar_urls_module)
	return patch.dict(
		sys.modules,
		{
			"debug_toolbar": debug_toolbar_module,
			"debug_toolbar.urls": debug_toolbar_urls_module,
		},
	)


class TestConfigUrls(SimpleTestCase):

	@override_settings(DEBUG=False)
	def test_debug_toolbar_url_is_not_present_when_debug_is_false(self):
		urls_module = _reload_config_urls_module()

		routes = [pattern.pattern._route for pattern in urls_module.urlpatterns]
		self.assertNotIn("__debug__/", routes)

	@override_settings(DEBUG=True, MEDIA_URL="/media/", MEDIA_ROOT="/tmp/test-media")
	def test_debug_toolbar_url_is_first_when_debug_is_true(self):
		with _install_fake_debug_toolbar():
			urls_module = _reload_config_urls_module()

		routes = [
			getattr(pattern.pattern, "_route", None)
			for pattern in urls_module.urlpatterns
			if hasattr(pattern.pattern, "_route")
		]

		self.assertGreater(len(routes), 0)
		self.assertEqual(routes[0], "__debug__/")

	@override_settings(DEBUG=True, MEDIA_URL="/media/", MEDIA_ROOT="/tmp/test-media")
	def test_media_static_url_is_added_when_debug_is_true(self):
		with _install_fake_debug_toolbar():
			urls_module = _reload_config_urls_module()

		regex_patterns = [
			pattern.pattern.regex.pattern
			for pattern in urls_module.urlpatterns
			if hasattr(pattern.pattern, "regex")
		]

		self.assertTrue(any("^media/(?P<path>.*)$" == regex for regex in regex_patterns))
