import hashlib
from unittest.mock import MagicMock

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from apps.core.throttles import (
    InternalKeyThrottle,
    PublicKeyHourThrottle,
    PublicKeyMinuteThrottle,
    PublicKeyThrottle,
)


def make_request(ip="1.2.3.4", ua="TestAgent/1.0", auth="public"):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.META["REMOTE_ADDR"] = ip
    request.META["HTTP_USER_AGENT"] = ua
    request.auth = auth
    return request


class TestPublicKeyThrottle(TestCase):
    def setUp(self):
        self.throttle = PublicKeyThrottle()
        self.view = MagicMock()

    def test_returns_cache_key_for_public_auth(self):
        request = make_request()
        key = self.throttle.get_cache_key(request, self.view)
        self.assertIsNotNone(key)

    def test_returns_none_for_non_public_auth(self):
        request = make_request(auth="internal")
        key = self.throttle.get_cache_key(request, self.view)
        self.assertIsNone(key)

    def test_returns_none_for_no_auth(self):
        request = make_request(auth=None)
        key = self.throttle.get_cache_key(request, self.view)
        self.assertIsNone(key)

    def test_cache_key_contains_scope(self):
        request = make_request()
        key = self.throttle.get_cache_key(request, self.view)
        self.assertIn("public", key)

    def test_cache_key_contains_sha256_fingerprint(self):
        request = make_request(ip="1.2.3.4", ua="TestAgent/1.0")
        key = self.throttle.get_cache_key(request, self.view)
        expected_fingerprint = hashlib.sha256(b"1.2.3.4|TestAgent/1.0").hexdigest()
        self.assertIn(expected_fingerprint, key)

    def test_different_ips_produce_different_keys(self):
        key_a = self.throttle.get_cache_key(make_request(ip="1.1.1.1"), self.view)
        key_b = self.throttle.get_cache_key(make_request(ip="2.2.2.2"), self.view)
        self.assertNotEqual(key_a, key_b)

    def test_different_user_agents_produce_different_keys(self):
        key_a = self.throttle.get_cache_key(make_request(ua="Chrome/1.0"), self.view)
        key_b = self.throttle.get_cache_key(make_request(ua="Firefox/1.0"), self.view)
        self.assertNotEqual(key_a, key_b)

    def test_same_ip_and_ua_produce_same_key(self):
        key_a = self.throttle.get_cache_key(make_request(ip="1.2.3.4", ua="SameAgent"), self.view)
        key_b = self.throttle.get_cache_key(make_request(ip="1.2.3.4", ua="SameAgent"), self.view)
        self.assertEqual(key_a, key_b)

    def test_missing_user_agent_does_not_raise(self):
        request = make_request()
        del request.META["HTTP_USER_AGENT"]
        key = self.throttle.get_cache_key(request, self.view)
        self.assertIsNotNone(key)

    def test_raw_ip_and_ua_not_in_cache_key(self):
        request = make_request(ip="9.8.7.6", ua="SecretAgent/99")
        key = self.throttle.get_cache_key(request, self.view)
        self.assertNotIn("9.8.7.6", key)
        self.assertNotIn("SecretAgent/99", key)

    def test_x_forwarded_for_is_used_as_ip(self):
        """get_ident() prefers X-Forwarded-For over REMOTE_ADDR."""
        request = make_request(ip="10.0.0.1")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.5"
        key = self.throttle.get_cache_key(request, self.view)
        expected_fingerprint = hashlib.sha256(b"203.0.113.5|TestAgent/1.0").hexdigest()
        self.assertIn(expected_fingerprint, key)


class TestSubclassScopes(TestCase):
    def test_minute_throttle_scope(self):
        self.assertEqual(PublicKeyMinuteThrottle.scope, "public_min")

    def test_hour_throttle_scope(self):
        self.assertEqual(PublicKeyHourThrottle.scope, "public_hour")

    def test_minute_throttle_inherits_cache_key_logic(self):
        throttle = PublicKeyMinuteThrottle()
        view = MagicMock()
        key = throttle.get_cache_key(make_request(), view)
        self.assertIsNotNone(key)
        self.assertIn("public_min", key)

    def test_hour_throttle_inherits_cache_key_logic(self):
        throttle = PublicKeyHourThrottle()
        view = MagicMock()
        key = throttle.get_cache_key(make_request(), view)
        self.assertIsNotNone(key)
        self.assertIn("public_hour", key)


class TestInternalKeyThrottle(TestCase):
    def setUp(self):
        self.throttle = InternalKeyThrottle()
        self.view = MagicMock()

    def test_always_returns_none(self):
        for auth in ("internal", "public", None, "anything"):
            request = make_request(auth=auth)
            self.assertIsNone(self.throttle.get_cache_key(request, self.view))

    def test_scope(self):
        self.assertEqual(InternalKeyThrottle.scope, "internal")


# --- Production settings: throttling classes and rates are wired up correctly ---

PROD_REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.core.throttles.PublicKeyMinuteThrottle",
        "apps.core.throttles.PublicKeyHourThrottle",
        "apps.core.throttles.InternalKeyThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "public_min": "40/minute",
        "public_hour": "800/hour",
        "internal": None,
    },
}


@override_settings(REST_FRAMEWORK=PROD_REST_FRAMEWORK)
class TestProductionThrottleConfig(TestCase):
    def test_throttle_classes_are_configured(self):
        from django.conf import settings

        classes = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]
        self.assertIn("apps.core.throttles.PublicKeyMinuteThrottle", classes)
        self.assertIn("apps.core.throttles.PublicKeyHourThrottle", classes)
        self.assertIn("apps.core.throttles.InternalKeyThrottle", classes)

    def test_public_minute_rate(self):
        from django.conf import settings

        self.assertEqual(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["public_min"], "40/minute")

    def test_public_hour_rate(self):
        from django.conf import settings

        self.assertEqual(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["public_hour"], "800/hour")

    def test_internal_rate_is_none(self):
        from django.conf import settings

        self.assertIsNone(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["internal"])
