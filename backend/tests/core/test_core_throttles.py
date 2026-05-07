import hashlib
from unittest.mock import MagicMock

from django.conf import settings
from django.core.cache import caches
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from apps.core.throttles import (
    InternalKeyThrottle,
    PublicKeyHourThrottle,
    PublicKeyMinuteThrottle,
)


def make_request(ip="1.2.3.4", ua="TestAgent/1.0", auth="public"):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.META["REMOTE_ADDR"] = ip
    request.META["HTTP_USER_AGENT"] = ua
    request.auth = auth
    return request


class TestPublicKeyThrottle(TestCase):
    def setUp(self) -> None:
        self.throttle = PublicKeyMinuteThrottle()
        self.view = MagicMock()

    def test_returns_cache_key_for_public_auth(self) -> None:
        request = make_request()
        key = self.throttle.get_cache_key(request, self.view)
        assert key is not None

    def test_returns_none_for_non_public_auth(self) -> None:
        request = make_request(auth="internal")
        key = self.throttle.get_cache_key(request, self.view)
        assert key is None

    def test_returns_none_for_no_auth(self) -> None:
        request = make_request(auth=None)
        key = self.throttle.get_cache_key(request, self.view)
        assert key is None

    def test_cache_key_contains_scope(self) -> None:
        request = make_request()
        key = self.throttle.get_cache_key(request, self.view)
        assert "public_min" in key

    def test_cache_key_contains_sha256_fingerprint(self) -> None:
        request = make_request(ip="1.2.3.4", ua="TestAgent/1.0")
        key = self.throttle.get_cache_key(request, self.view)
        expected_fingerprint = hashlib.sha256(b"1.2.3.4|TestAgent/1.0").hexdigest()
        assert expected_fingerprint in key

    def test_different_ips_produce_different_keys(self) -> None:
        key_a = self.throttle.get_cache_key(make_request(ip="1.1.1.1"), self.view)
        key_b = self.throttle.get_cache_key(make_request(ip="2.2.2.2"), self.view)
        assert key_a != key_b

    def test_different_user_agents_produce_different_keys(self) -> None:
        key_a = self.throttle.get_cache_key(make_request(ua="Chrome/1.0"), self.view)
        key_b = self.throttle.get_cache_key(make_request(ua="Firefox/1.0"), self.view)
        assert key_a != key_b

    def test_same_ip_and_ua_produce_same_key(self) -> None:
        key_a = self.throttle.get_cache_key(make_request(ip="1.2.3.4", ua="SameAgent"), self.view)
        key_b = self.throttle.get_cache_key(make_request(ip="1.2.3.4", ua="SameAgent"), self.view)
        assert key_a == key_b

    def test_missing_user_agent_does_not_raise(self) -> None:
        request = make_request()
        del request.META["HTTP_USER_AGENT"]
        key = self.throttle.get_cache_key(request, self.view)
        assert key is not None

    def test_raw_ip_and_ua_not_in_cache_key(self) -> None:
        request = make_request(ip="9.8.7.6", ua="SecretAgent/99")
        key = self.throttle.get_cache_key(request, self.view)
        assert "9.8.7.6" not in key
        assert "SecretAgent/99" not in key

    def test_x_forwarded_for_is_used_as_ip(self) -> None:
        """get_ident() prefers X-Forwarded-For over REMOTE_ADDR."""
        request = make_request(ip="10.0.0.1")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.5"
        key = self.throttle.get_cache_key(request, self.view)
        expected_fingerprint = hashlib.sha256(b"203.0.113.5|TestAgent/1.0").hexdigest()
        assert expected_fingerprint in key


class TestSubclassScopes(TestCase):
    def test_minute_throttle_scope(self) -> None:
        assert PublicKeyMinuteThrottle.scope == "public_min"

    def test_hour_throttle_scope(self) -> None:
        assert PublicKeyHourThrottle.scope == "public_hour"

    def test_minute_throttle_inherits_cache_key_logic(self) -> None:
        throttle = PublicKeyMinuteThrottle()
        view = MagicMock()
        key = throttle.get_cache_key(make_request(), view)
        assert key is not None
        assert "public_min" in key

    def test_hour_throttle_inherits_cache_key_logic(self) -> None:
        throttle = PublicKeyHourThrottle()
        view = MagicMock()
        key = throttle.get_cache_key(make_request(), view)
        assert key is not None
        assert "public_hour" in key

    def test_throttles_use_throttling_cache(self) -> None:
        assert PublicKeyMinuteThrottle.cache is caches["throttling"]
        assert PublicKeyHourThrottle.cache is caches["throttling"]


class TestInternalKeyThrottle(TestCase):
    def setUp(self) -> None:
        self.throttle = InternalKeyThrottle()
        self.view = MagicMock()

    def test_always_returns_none(self) -> None:
        for auth in ("internal", "public", None, "anything"):
            request = make_request(auth=auth)
            assert self.throttle.get_cache_key(request, self.view) is None

    def test_scope(self) -> None:
        assert InternalKeyThrottle.scope == "internal"


# --- Production settings: throttling classes and rates are wired up correctly ---

PROD_REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.core.throttles.PublicKeyMinuteThrottle",
        "apps.core.throttles.PublicKeyHourThrottle",
        # fallback for unauthenticated requests, should be blocked by permissions but just in case
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "public_min": "40/minute",
        "public_hour": "800/hour",
        # fallback for unauthenticated requests, should be blocked by permissions but just in case
        "anon": "10/minute",
    },
}


@override_settings(REST_FRAMEWORK=PROD_REST_FRAMEWORK)
class TestProductionThrottleConfig(TestCase):
    def test_throttle_classes_are_configured(self) -> None:
        classes = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]
        assert "apps.core.throttles.PublicKeyMinuteThrottle" in classes
        assert "apps.core.throttles.PublicKeyHourThrottle" in classes

    def test_public_minute_rate(self) -> None:
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["public_min"] == "40/minute"

    def test_public_hour_rate(self) -> None:
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["public_hour"] == "800/hour"

    def test_anon_rate(self) -> None:
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"] == "10/minute"
