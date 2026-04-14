"""Retrieves the user's preferred language from the request and provides it as a mixin."""
from django.conf import settings

class LanguageAwareMixin:
    def _get_request_language_code(self) -> str:
        raw = (
            self.request.query_params.get("lang")
            or self.request.headers.get("Accept-Language", "")
        )
        candidate = raw.split(",", 1)[0].split(";", 1)[0].strip().lower()
        if candidate:
            return candidate.split("-", 1)[0]
        return (getattr(settings, "LANGUAGE_CODE", "en") or "en").split("-", 1)[0].lower()