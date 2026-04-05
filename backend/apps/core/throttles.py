import hashlib

from django.http import HttpRequest
from rest_framework.throttling import SimpleRateThrottle


class PublicKeyThrottle(SimpleRateThrottle):
    """Rate limiting for the shared public API key, differentiated per client.

    Uses DRF's built-in get_ident() for IP resolution (handles
    X-Forwarded-For and REMOTE_ADDR automatically), combined with the
    User-Agent header to distinguish clients sharing the same IP.
    """

    def get_cache_key(self, request: HttpRequest, _view: any) -> str | None:
        """Generate a cache key based on the client's IP and User-Agent."""
        if request.auth != "public":
            return None

        ip = self.get_ident(request)
        ua = request.META.get("HTTP_USER_AGENT", "")

        # Hash the combination so the cache key has a fixed length (also avoids leaking raw IPs and UAs into the cache).
        fingerprint = hashlib.sha256(f"{ip}|{ua}".encode()).hexdigest()

        return self.cache_format % {
            "scope": self.scope,
            "ident": fingerprint,
        }


class InternalKeyThrottle(SimpleRateThrottle):
    """No-op throttle for the internal API key."""

    scope = "internal"

    def get_cache_key(self, _request: HttpRequest, _view: any) -> None:
        """No caching key - effectively disables throttling for the internal API key."""
        return


class PublicKeyMinuteThrottle(PublicKeyThrottle):
    """Throttling for the public API key, limited to x requests per minute per client."""

    scope = "public_min"


class PublicKeyHourThrottle(PublicKeyThrottle):
    """Throttling for the public API key, limited to x requests per hour per client."""

    scope = "public_hour"
