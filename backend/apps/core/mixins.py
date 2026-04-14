"""Reusable mixins for ViewSets in the core app."""

from django.conf import settings


class LanguageAwareMixin:
    """Mixin that resolves the preferred language code from the current request.

    Reads the language preference from the ``lang`` query parameter first,
    then falls back to the ``Accept-Language`` HTTP header, and finally to
    the project's ``LANGUAGE_CODE`` setting. Only the primary language
    subtag is returned (e.g. ``"nl"`` from ``"nl-BE"``).

    Intended for use with ViewSets that annotate language-dependent fields
    (e.g. title sorting and search annotations) so that ordering and search
    reflect the language the client is currently using.
    """

    def _get_request_language_code(self) -> str:
        """Return the two-letter language code for the current request.

        Resolution order:
        1. ``?lang=`` query parameter.
        2. ``Accept-Language`` HTTP header (first entry, quality values ignored).
        3. ``settings.LANGUAGE_CODE`` (default ``"en"``).
        """
        raw = self.request.query_params.get("lang") or self.request.headers.get("Accept-Language", "")
        candidate = raw.split(",", 1)[0].split(";", 1)[0].strip().lower()
        if candidate:
            return candidate.split("-", 1)[0]
        return (getattr(settings, "LANGUAGE_CODE", "en") or "en").split("-", 1)[0].lower()
