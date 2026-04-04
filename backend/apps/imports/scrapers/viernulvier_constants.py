"""Shared constants, exceptions, and config dataclasses for the Viernulvier scraper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from django.db import models

# ---------------------------------------------------------------------------
# API configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://www.viernulvier.gent/api/v1"
BASE_DOMAIN = "https://www.viernulvier.gent"
DEFAULT_ENDPOINT = "/productions"
DEFAULT_TIMEOUT = 15
ERROR_CONTEXT_PATH = "/api/contexts/Error"

# Retry settings
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 1.5  # seconds
RETRY_BACKOFF_MAX = 60  # hard ceiling in seconds
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

# Concurrent page fetching
MAX_CONCURRENT_PAGES = 4

# Maximum error messages stored per sync run.
# Prevents unbounded memory growth when thousands of records fail.
MAX_ERROR_MESSAGES = 50

USER_AGENT_POOL = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:122.0) Gecko/20100101 Firefox/122.0",
]

# String values treated as empty *only* in URL fields.
_EMPTY_URL_VALUES: set[str] = {"", "0", "none", "null", "undefined", "-", "n/a", "nvt"}


class ScraperError(Exception):
    """Raised when the scraper cannot fetch or normalize Viernulvier data."""


class RateLimitError(ScraperError):
    """Raised on HTTP 429 after all retries are exhausted."""

    def __init__(self, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        msg = f"Rate limited by API (Retry-After: {retry_after}s)" if retry_after else "Rate limited by API"
        super().__init__(msg)


@dataclass
class TranslationConfig:
    """Configuration for syncing one translated field to a translation model."""

    api_key: str
    model: type[models.Model]
    parent_fk: str
    flat_field: str
    language_fk: str = "language_id"
    value_transforms: dict[str, Callable[[Any], Any]] = field(default_factory=dict)


@dataclass
class M2MConfig:
    """Configuration for a M2M relation expressed via an explicit through table."""

    api_key: str
    related_model: type[models.Model]
    through_model: type[models.Model]
    parent_fk: str
    related_fk: str
    related_lookup_field: str = "external_id"
    extra_fields: dict[str, str] = field(default_factory=dict)


@dataclass
class ModelSyncConfig:
    """Complete sync configuration for one Django model."""

    field_map: dict[str, str | None] = field(default_factory=dict)
    value_transforms: dict[str, Callable[[Any], Any]] = field(default_factory=dict)
    fk_resolvers: dict[str, Callable[[Any], Any | None]] = field(default_factory=dict)
    translations: list[TranslationConfig] = field(default_factory=list)
    m2m: list[M2MConfig] = field(default_factory=list)
    lookup_field: str = "external_id"
    api_id_key: str = "@id"
    item_filter: Callable[[Mapping[str, Any]], bool] | None = None
