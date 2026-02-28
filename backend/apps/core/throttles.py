"""
Custom throttling classes for the API.
"""
from rest_framework.throttling import SimpleRateThrottle


class BaseIPThrottle(SimpleRateThrottle):
    """Base class for IP-based throttling."""

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


class IPMinuteThrottle(BaseIPThrottle):
    """Throttle based on client IP address - per minute burst limit."""
    scope = "ip_minute"


class IPHourThrottle(BaseIPThrottle):
    """Throttle based on client IP address - per hour sustained limit."""
    scope = "ip_hour"