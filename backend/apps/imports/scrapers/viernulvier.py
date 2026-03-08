"""Viernulvier / Peppered scraper

Key design decisions
--------------------
- One requests.Session per sync run (connection pooling, shared auth header).
- Retry with exponential backoff + jitter for 429 / 5xx / network errors.
- FK resolution via a warm in-memory cache (one bulk query per model) to
  avoid the classic N+1 problem.
- Concurrent page fetching via ThreadPoolExecutor (page order preserved).
- Translation updates are *batched per language* — all translated fields for
  one parent + one language are merged into a single update_or_create call
  instead of one call per field (13 fields x 3 languages = 3 queries, not 39).
  defined by multiple FK columns (e.g. EventPrice(event, price_rank)).
- Per-item savepoints so one bad record never aborts the whole batch.
- ETag / 304 support to skip completely unchanged endpoints.
- Dry-run mode for safe inspection before writing.
"""

from __future__ import annotations

import logging
import os
import random
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, Tuple, Type
from urllib.parse import urljoin, urlparse

import requests
from django.core.exceptions import FieldDoesNotExist, FieldError, ValidationError
from django.core.validators import URLValidator
from django.db import DatabaseError, IntegrityError, transaction, models
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

logger = logging.getLogger(__name__)

__all__ = [
    "ModelSyncConfig",
    "TranslationConfig",
    "M2MConfig",
    "FKCache",
    "ScraperError",
    "RateLimitError",
    "fetch_viernulvier",
    "sync_viernulvier",
    "normalize_url",
    "normalize_performer_type",
    "nee_ja_to_bool",
    "clean_string",
]

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
# Prevents unbounded memory growth when thousands of records fail (e.g. 11k event prices).
MAX_ERROR_MESSAGES = 50

USER_AGENT_POOL = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:122.0) Gecko/20100101 Firefox/122.0",
]

# String values treated as empty *only* in URL fields.
# Not used for regular CharField / TextField — "0" is valid text.
_EMPTY_URL_VALUES: Set[str] = {"", "0", "none", "null", "undefined", "-", "n/a", "nvt"}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ScraperError(Exception):
    """Raised when the scraper cannot fetch or normalize Viernulvier data."""


class RateLimitError(ScraperError):
    """Raised on HTTP 429 after all retries are exhausted."""

    def __init__(self, retry_after: Optional[int] = None) -> None:
        self.retry_after = retry_after
        msg = (
            f"Rate limited by API (Retry-After: {retry_after}s)"
            if retry_after
            else "Rate limited by API"
        )
        super().__init__(msg)


# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------


@dataclass
class TranslationConfig:
    """Configuration for syncing one translated field to a translation model.

    The Peppered API returns translations as flat dicts:
        "title": {"nl": "De titel", "en": "The title"}

    Each TranslationConfig handles one such field. Multiple configs that share
    the same translation model are *merged per language* by _sync_all_translations
    so only one update_or_create per language is needed — not one per field.

    Args:
        api_key:          Key in the parent API item (e.g. "title").
        model:            Django translation model class.
        parent_fk:        FK field name pointing to the parent on the translation model.
        flat_field:       Field name on the translation model to populate.
        language_fk:      Field name for the language code. Use "language_id" for
                          models where Language has a string primary key.
        value_transforms: Optional per-field callables applied after type coercion.
    """

    api_key: str
    model: Type[models.Model]
    parent_fk: str
    flat_field: str
    language_fk: str = "language_id"
    value_transforms: Dict[str, Callable[[Any], Any]] = field(default_factory=dict)


@dataclass
class M2MConfig:
    """Configuration for a M2M relation expressed via an explicit through table.

    The API returns M2M data as a list of URL strings:
        "genres": ["https://.../genres/1", "https://.../genres/3"]

    Args:
        api_key:              Key in the parent API item.
        related_model:        The related Django model.
        through_model:        The through/junction table model.
        parent_fk:            FK to the parent model in the through table.
        related_fk:           FK to the related model in the through table.
        related_lookup_field: Field used to look up the related object (default: "external_id").
        extra_fields:         Extra fields on the through table: {api_field: model_field}.
                              Use "position" to auto-fill from the list index.
    """

    api_key: str
    related_model: Type[models.Model]
    through_model: Type[models.Model]
    parent_fk: str
    related_fk: str
    related_lookup_field: str = "external_id"
    extra_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class ModelSyncConfig:
    """Complete sync configuration for one Django model.

    Args:
        field_map:        API key → model field name. Set value to None to
                          explicitly skip an API field.
        value_transforms: Callables applied after type coercion, keyed by model
                          field name. E.g. {"is_own_location": nee_ja_to_bool}.
        fk_resolvers:     Custom FK resolvers when the default external_id lookup
                          does not apply. Callable(raw_value) → pk | None.
        translations:     TranslationConfig list for flat-dict translated fields.
        m2m:              M2MConfig list for M2M relations via through tables.
        lookup_field:     Single field for update_or_create lookup (default: "external_id").
        api_id_key:       Primary identifier key in the API object (default: "@id").
        item_filter:      Optional predicate — return False to skip an item.
    """

    field_map: Dict[str, Optional[str]] = field(default_factory=dict)
    value_transforms: Dict[str, Callable[[Any], Any]] = field(default_factory=dict)
    fk_resolvers: Dict[str, Callable[[Any], Optional[Any]]] = field(
        default_factory=dict
    )
    translations: List[TranslationConfig] = field(default_factory=list)
    m2m: List[M2MConfig] = field(default_factory=list)
    lookup_field: str = "external_id"
    api_id_key: str = "@id"
    item_filter: Optional[Callable[[Mapping[str, Any]], bool]] = None


# ---------------------------------------------------------------------------
# HTTP session with retry + exponential backoff
# ---------------------------------------------------------------------------


def _get_api_key_or_raise() -> str:
    api_key = os.getenv("VIERNULVIER_API_KEY")
    if not api_key:
        raise ScraperError("VIERNULVIER_API_KEY environment variable is not set")
    return api_key


def _build_session() -> requests.Session:
    """Create a requests.Session with connection pooling and shared auth headers."""
    session = requests.Session()
    session.headers.update(
        {
            "X-AUTH-TOKEN": _get_api_key_or_raise(),
            "accept": "application/ld+json",
            "User-Agent": random.choice(USER_AGENT_POOL),
        }
    )
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=MAX_CONCURRENT_PAGES,
        pool_maxsize=MAX_CONCURRENT_PAGES * 2,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _backoff_seconds(attempt: int) -> float:
    """Exponential backoff with full jitter, capped at RETRY_BACKOFF_MAX."""
    return min(
        RETRY_BACKOFF_BASE * (2**attempt) + random.uniform(0, 1),
        RETRY_BACKOFF_MAX,
    )


def _parse_retry_after(response: requests.Response) -> Optional[int]:
    """Parse the Retry-After response header as an integer number of seconds."""
    header = response.headers.get("Retry-After")
    if header:
        try:
            return int(header)
        except ValueError:
            pass
    return None


def _fetch_with_retry(
    session: requests.Session,
    url: str,
    params: Optional[Dict[str, str]] = None,
    etag: Optional[str] = None,
) -> Tuple[Optional[Any], Optional[str]]:
    """Fetch one URL with retry + exponential backoff + jitter.

    Handles:
    - HTTP 304 Not Modified  → returns (None, cached_etag)
    - HTTP 429 Too Many Requests → respects Retry-After header
    - HTTP 5xx server errors → retries with backoff
    - ConnectionError / Timeout → retries with backoff
    - Other transport errors → raises immediately (not retryable)

    Returns:
        (data, new_etag). data is None when the server returns 304.
    """
    headers: Dict[str, str] = {}
    if etag:
        headers["If-None-Match"] = etag

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = session.get(
                url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT
            )
        except requests.ConnectionError as exc:
            if attempt == MAX_RETRIES:
                raise ScraperError(
                    f"Connection failed after {MAX_RETRIES} attempts: {url}"
                ) from exc
            wait = _backoff_seconds(attempt)
            logger.warning(
                "ConnectionError — retry %d in %.1fs: %s", attempt + 1, wait, url
            )
            time.sleep(wait)
            continue
        except requests.Timeout as exc:
            if attempt == MAX_RETRIES:
                raise ScraperError(
                    f"Request timed out after {MAX_RETRIES} attempts: {url}"
                ) from exc
            wait = _backoff_seconds(attempt)
            logger.warning("Timeout — retry %d in %.1fs: %s", attempt + 1, wait, url)
            time.sleep(wait)
            continue
        except requests.RequestException as exc:
            # SSL errors, invalid URL, etc. — not worth retrying
            raise ScraperError(f"Request failed: {url}") from exc

        if response.status_code == 304:
            logger.debug("304 Not Modified — page unchanged: %s", url)
            return None, etag

        if response.status_code == 429:
            retry_after = _parse_retry_after(response)
            if attempt == MAX_RETRIES:
                raise RateLimitError(retry_after)
            wait = float(retry_after) if retry_after else _backoff_seconds(attempt)
            logger.warning(
                "HTTP 429 — waiting %.1fs before retry %d: %s", wait, attempt + 1, url
            )
            time.sleep(wait)
            continue

        if response.status_code in RETRY_STATUS_CODES:
            if attempt == MAX_RETRIES:
                raise ScraperError(
                    f"HTTP {response.status_code} after {MAX_RETRIES} attempts: {url}"
                )
            wait = _backoff_seconds(attempt)
            logger.warning(
                "HTTP %d — retry %d in %.1fs: %s",
                response.status_code,
                attempt + 1,
                wait,
                url,
            )
            time.sleep(wait)
            continue

        if not response.ok:
            raise ScraperError(f"API error: {response.status_code} — {url}")

        try:
            data = response.json()
        except ValueError as exc:
            raise ScraperError(f"Invalid JSON from API: {url}") from exc

        if data is None:
            raise ScraperError(f"API returned null payload: {url}")

        if isinstance(data, dict) and data.get("@context") == ERROR_CONTEXT_PATH:
            status = data.get("status", "unknown")
            detail = data.get("detail", "no detail provided")
            raise ScraperError(f"API error response: status={status}, detail={detail}")

        new_etag = response.headers.get("ETag")
        return data, new_etag

    raise ScraperError(f"Retries exhausted for: {url}")  # unreachable


# ---------------------------------------------------------------------------
# Pagination discovery
# ---------------------------------------------------------------------------


def _discover_extra_pages(data: dict) -> List[str]:
    """Discover page URLs beyond page 1 from the hydra:view metadata.

    Primary strategy: parse the "last" URL for the total page count and
    generate all intermediate page URLs by substituting the page number.
    This allows full concurrent fetching.

    Falls back to an empty list if the "last" URL does not contain ?page=N,
    which signals the caller to fall back to sequential "next" link following.

    Returns a list of page URLs for pages 2..N in order.
    """
    view = data.get("view") or {}
    last_url = view.get("last", "")

    match = re.search(r"[?&]page=(\d+)", last_url)
    if not match:
        return []  # Caller will use sequential fallback

    total_pages = int(match.group(1))
    pages = []
    for page_num in range(2, total_pages + 1):
        page_url = re.sub(r"([?&])page=\d+", rf"\g<1>page={page_num}", last_url)
        if not page_url.startswith("http"):
            page_url = urljoin(BASE_DOMAIN, page_url)
        pages.append(page_url)
    return pages


# ---------------------------------------------------------------------------
# Main fetch function
# ---------------------------------------------------------------------------


def fetch_viernulvier(
    endpoint: str = DEFAULT_ENDPOINT,
    params: Optional[Dict[str, str]] = None,
    etag_cache: Optional[Dict[str, str]] = None,
) -> List[Any]:
    """Fetch all items from an API endpoint, following pagination automatically.

    Two pagination strategies:
    1. Concurrent (preferred): if the "last" URL has a ?page=N pattern, derive
       all page URLs upfront and fetch them in parallel.
    2. Sequential fallback: follow "next" links one by one (slower but handles
       non-standard pagination).

    Args:
        endpoint:    Relative API path (e.g. "/productions").
        params:      Optional query parameters, applied only to page 1.
        etag_cache:  Optional dict of url → ETag. Pass the same instance across
                     calls to benefit from 304 Not Modified responses.

    Returns:
        All items across all pages in original order.
    """
    parsed = urlparse(endpoint)
    if parsed.scheme or parsed.netloc:
        raise ScraperError(f"endpoint must be a relative path, got: {endpoint!r}")

    url = urljoin(BASE_URL + "/", endpoint.lstrip("/"))
    etag_cache = etag_cache if etag_cache is not None else {}
    session = _build_session()

    logger.info("Fetching: %s", url)
    data, new_etag = _fetch_with_retry(
        session, url, params=params, etag=etag_cache.get(url)
    )
    if new_etag:
        etag_cache[url] = new_etag

    if data is None:
        logger.info("304 Not Modified for %s — nothing to sync.", url)
        return []

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        raise ScraperError(f"Unexpected payload type: {type(data)}")

    members = data.get("member", [])
    if not members and "@context" in data:
        members = [data]  # Single-object response wrapped in hydra context
    all_items: List[Any] = list(members)

    total_items = data.get("totalItems") or data.get("hydra:totalItems")
    extra_pages = _discover_extra_pages(data)

    if total_items:
        logger.info(
            "API reports %d total items — %d additional pages to fetch",
            total_items,
            len(extra_pages),
        )

    # --- Strategy 1: concurrent page fetch (all URLs known upfront) ---
    if extra_pages:
        page_results: Dict[str, List[Any]] = {}

        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PAGES) as executor:
            future_to_url = {
                executor.submit(
                    _fetch_with_retry,
                    session,
                    page_url,
                    None,  # query params only on page 1
                    etag_cache.get(page_url),
                ): page_url
                for page_url in extra_pages
            }
            for future in as_completed(future_to_url):
                page_url = future_to_url[future]
                try:
                    page_data, page_etag = future.result()
                    if page_etag:
                        etag_cache[page_url] = page_etag
                    if page_data is None:
                        continue  # 304
                    page_results[page_url] = (
                        page_data.get("member", [])
                        if isinstance(page_data, dict)
                        else page_data
                    )
                except ScraperError as exc:
                    logger.error("Page fetch failed for %s: %s", page_url, exc)

        # Merge in original page order (as_completed is unordered)
        for page_url in extra_pages:
            all_items.extend(page_results.get(page_url, []))

    # --- Strategy 2: sequential "next" link fallback ---
    else:
        view = data.get("view") or {}
        next_raw = view.get("next")
        current_url: Optional[str] = (
            (
                next_raw
                if next_raw.startswith("http")
                else urljoin(BASE_DOMAIN, next_raw)
            )
            if next_raw
            else None
        )
        while current_url:
            page_data, page_etag = _fetch_with_retry(
                session, current_url, etag=etag_cache.get(current_url)
            )
            if page_etag:
                etag_cache[current_url] = page_etag
            if page_data is None:
                break
            if isinstance(page_data, dict):
                all_items.extend(page_data.get("member", []))
                next_view = page_data.get("view") or {}
                next_raw = next_view.get("next")
                current_url = (
                    (
                        next_raw
                        if next_raw.startswith("http")
                        else urljoin(BASE_DOMAIN, next_raw)
                    )
                    if next_raw
                    else None
                )
            else:
                all_items.extend(page_data if isinstance(page_data, list) else [])
                break

    logger.info("Fetched %d items from %s", len(all_items), endpoint)
    return all_items


# ---------------------------------------------------------------------------
# Value normalisation helpers (exported for use in management commands)
# ---------------------------------------------------------------------------

_url_validator = URLValidator()


def normalize_url(value: Any) -> str:
    """Return the value only if it is a valid URL, otherwise return empty string."""
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in _EMPTY_URL_VALUES:
        return ""
    try:
        _url_validator(s)
        return s
    except ValidationError:
        return ""


def normalize_performer_type(value: Any) -> str:
    """Map API performer_type values to internal enum values."""
    _mapping = {"person": "solo"}
    s = str(value).strip().lower() if value else ""
    return _mapping.get(s, s)


def clean_string(value: Any) -> str:
    """Strip surrounding whitespace and remove non-printable control characters.

    Keeps tab (\\t), line feed (\\n), and carriage return (\\r) intact.
    Removes null bytes and other ASCII control characters that would corrupt
    the database or cause JSON serialisation errors.
    """
    if value is None:
        return ""
    s = str(value).strip()
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
    return s


def clean_vendor_id(value: Any) -> Optional[str]:
    """
    Transform vendor_id: return None if empty or HTML-like, else return as string.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.startswith("<i"):
        return None
    return s


def nee_ja_to_bool(value: Any) -> bool:
    """Coerce Dutch/English truthy strings and integers to Python bool.

    Accepts: "ja"/"nee", "true"/"false", "yes"/"no", "1"/"0", bool, int.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"ja", "true", "1", "yes"}:
            return True
        if v in {"nee", "false", "0", "", "no"}:
            return False
    return bool(value)


def _camel_to_snake(value: str) -> str:
    """Convert camelCase API key to snake_case model field name."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def _parse_field_value(model_field: models.Field, value: Any) -> Any:
    """Coerce an API value to the correct Python type for the given model field.

    Supported field types:
    - CharField, TextField   → clean_string, respect max_length
    - URLField               → normalize_url
    - BooleanField           → nee_ja_to_bool
    - DecimalField           → Decimal (avoids float rounding errors for prices)
    - IntegerField           → int
    - FloatField             → float
    - DateTimeField          → parse_datetime (with broken-date repair)
    - DateField              → parse_date
    - All other types        → pass through unchanged
    """
    if value is None:
        return None

    if isinstance(model_field, (models.TextField, models.CharField)):
        cleaned = clean_string(value)
        max_len = getattr(model_field, "max_length", None)
        if max_len and len(cleaned) > max_len:
            logger.debug(
                "Field '%s' truncated: %d → %d chars",
                model_field.name,
                len(cleaned),
                max_len,
            )
            cleaned = cleaned[:max_len]
        return cleaned

    if isinstance(model_field, models.URLField):
        return normalize_url(value)

    if isinstance(model_field, models.BooleanField):
        return nee_ja_to_bool(value)

    if isinstance(model_field, models.DecimalField):
        # Use Decimal — never float — for monetary values to avoid rounding errors.
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            logger.warning(
                "Cannot convert '%s' to Decimal for field '%s'", value, model_field.name
            )
            return None

    if isinstance(model_field, models.IntegerField):
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(
                "Cannot convert '%s' to int for field '%s'", value, model_field.name
            )
            return None

    if isinstance(model_field, models.FloatField):
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(
                "Cannot convert '%s' to float for field '%s'", value, model_field.name
            )
            return None

    if isinstance(model_field, models.DateTimeField) and isinstance(value, str):
        v = value
        # Repair two broken date formats observed in this API
        if v.startswith("-"):
            v = v[1:]
        if v[:4] == "0000":
            v = "1970" + v[4:]
        parsed = parse_datetime(v)
        if parsed is None:
            logger.debug(
                "Cannot parse datetime '%s' for field '%s'", value, model_field.name
            )
        return parsed

    if isinstance(model_field, models.DateField) and isinstance(value, str):
        return parse_date(value)

    return value


# ---------------------------------------------------------------------------
# FK cache — eliminates N+1 queries
# ---------------------------------------------------------------------------


class FKCache:
    """In-memory cache of (model, external_id) → pk.

    On first use of a model, loads all known external_id → pk pairs with a
    single bulk queryset (warmup). Subsequent FK resolutions are O(1) dict
    lookups with a single DB query only on a true cache miss.

    Warmup failures are recorded so that the failed model is not re-queried
    on every lookup (avoids repeated broken queries for models without
    external_id).

    Thread-safety: not thread-safe. Intended for use in sync loops only.
    """

    def __init__(self) -> None:
        self._cache: Dict[Tuple[Type[models.Model], str], Any] = {}
        # True = warmed up successfully, False = warmup failed
        self._loaded: Dict[Type[models.Model], bool] = {}

    def warmup(self, model: Type[models.Model]) -> None:
        """Pre-load all external_id → pk mappings for a model in one query."""
        if model in self._loaded:
            return
        try:
            count = 0
            for ext_id, pk in model.objects.values_list("external_id", "pk").iterator():
                self._cache[(model, str(ext_id))] = pk
                count += 1
            self._loaded[model] = True
            logger.debug("FK cache warmed: %s (%d entries)", model.__name__, count)
        except Exception:
            # Mark as attempted (False) so we do not keep retrying this broken query.
            self._loaded[model] = False
            logger.warning(
                "FK cache warmup failed for %s (no external_id field?)",
                model.__name__,
                exc_info=True,
            )

    def get(self, model: Type[models.Model], ext_id: str) -> Optional[Any]:
        self.warmup(model)
        return self._cache.get((model, str(ext_id)))

    def set(self, model: Type[models.Model], ext_id: str, pk: Any) -> None:
        """Insert or update a cache entry after creating a new object."""
        self._cache[(model, str(ext_id))] = pk


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _extract_external_id_from_url(raw: Any) -> Optional[str]:
    """Extract an external ID string from a URL, embedded dict, or integer.

    Examples:
    - "https://www.viernulvier.gent/api/v1/halls/42" → full URL string
    - {"@id": "/api/v1/productions/5", ...}          → "/api/v1/productions/5"
    - 42                                              → "42"
    """
    if raw is None:
        return None
    if isinstance(raw, int):
        return str(raw)
    if isinstance(raw, dict):
        raw = raw.get("@id") or raw.get("external_id") or raw.get("id")
        if raw is None:
            return None
    if isinstance(raw, str):
        return raw.strip() or None
    return None


def _resolve_fk(
    model_field: models.Field,
    raw_value: Any,
    fk_cache: FKCache,
) -> Optional[Any]:
    """Resolve a FK raw value (URL or embedded dict) to a database primary key.

    Uses the FK cache for fast lookups. On cache miss, queries the DB once
    and populates the cache so future calls for the same object are free.
    """
    related_model = model_field.remote_field.model
    ext_id = _extract_external_id_from_url(raw_value)
    if ext_id is None:
        return None

    pk = fk_cache.get(related_model, ext_id)
    if pk is not None:
        return pk

    try:
        pk = related_model.objects.values_list("pk", flat=True).get(external_id=ext_id)
        fk_cache.set(related_model, ext_id, pk)
        return pk
    except related_model.DoesNotExist:
        logger.warning(
            "FK not found: %s.external_id=%r — sync related models first.",
            related_model.__name__,
            ext_id,
        )
        return None
    except Exception:
        logger.exception(
            "Error resolving FK %s external_id=%r", related_model.__name__, ext_id
        )
        return None


def _extract_lookup_value(
    item: Mapping[str, Any],
    config: ModelSyncConfig,
) -> Optional[str]:
    """Extract the primary lookup value (usually the API @id) from an item."""
    raw = item.get(config.api_id_key) or item.get("external_id") or item.get("id")
    if raw is None:
        return None
    if isinstance(raw, dict):
        raw = raw.get("@id") or raw.get("external_id") or raw.get("id")
    return str(raw).strip() if raw is not None else None


# ---------------------------------------------------------------------------
# Build defaults dict: API item → Django model kwargs
# ---------------------------------------------------------------------------


def _build_defaults(
    model: Type[models.Model],
    item: Mapping[str, Any],
    config: ModelSyncConfig,
    fk_cache: FKCache,
) -> Dict[str, Any]:
    """Convert an API item to a defaults dict for update_or_create.

    Pass 1: process explicit field_map entries (highest priority).
    Pass 2: auto-map remaining keys via camelCase → snake_case conversion.

    Flat dicts (translations) and lists (M2M) are skipped here.
    """
    defaults: Dict[str, Any] = {}
    explicitly_mapped = set(config.field_map.keys())

    def _apply(model_field: models.Field, raw_value: Any, field_name: str) -> None:
        if model_field.is_relation and model_field.many_to_one:
            custom = config.fk_resolvers.get(field_name)
            pk = (
                custom(raw_value)
                if custom
                else _resolve_fk(model_field, raw_value, fk_cache)
            )
            if pk is not None:
                defaults[f"{model_field.name}_id"] = pk
        else:
            converted = _parse_field_value(model_field, raw_value)
            transform = config.value_transforms.get(field_name)
            if transform:
                converted = transform(converted)
            if converted is not None:
                defaults[model_field.name] = converted

    # Pass 1: explicit field_map
    for api_key, model_field_name in config.field_map.items():
        if model_field_name is None:
            continue
        raw_value = item.get(api_key)
        if raw_value is None:
            continue
        try:
            model_field = model._meta.get_field(model_field_name)
        except FieldDoesNotExist:
            logger.warning(
                "Field '%s' does not exist on %s", model_field_name, model.__name__
            )
            continue
        if not isinstance(model_field, models.Field) or model_field.primary_key:
            continue
        if isinstance(raw_value, dict) and not model_field.is_relation:
            continue  # flat dict → handled by translation sync
        _apply(model_field, raw_value, model_field_name)

    # Pass 2: auto-map unmapped keys
    for api_key, raw_value in item.items():
        if api_key in explicitly_mapped or api_key.startswith("@") or raw_value is None:
            continue
        if isinstance(raw_value, (list, dict)):
            continue

        snake_key = _camel_to_snake(api_key)
        model_field = None
        for candidate in (api_key, snake_key):
            try:
                f = model._meta.get_field(candidate)
                if isinstance(f, models.Field) and not f.primary_key:
                    model_field = f
                    break
            except FieldDoesNotExist:
                pass

        if model_field is None:
            continue
        _apply(model_field, raw_value, model_field.name)

    return defaults


# ---------------------------------------------------------------------------
# Translation sync — batched per language to minimise query count
# ---------------------------------------------------------------------------


def _sync_all_translations(
    parent_obj: models.Model,
    item: Mapping[str, Any],
    translation_configs: List[TranslationConfig],
) -> None:
    """Sync all translated fields for one parent object.

    Batching: configs that share the same (translation model, parent_fk,
    language_fk) are grouped together. For each language code, all field
    values from every config in the group are merged, then saved with a
    single update_or_create call.

    Without batching: 13 fields x 3 languages = 39 queries per production.
    With batching:                               3 queries per production.

    Configs targeting different translation models are handled independently.
    """
    if not translation_configs:
        return

    groups = defaultdict(list)
    for cfg in translation_configs:
        groups[(cfg.model, cfg.parent_fk, cfg.language_fk)].append(cfg)

    for (trans_model, parent_fk, language_fk), cfgs in groups.items():
        # Collect every language code present across all field dicts
        all_languages: Set[str] = set()
        for cfg in cfgs:
            raw_dict = item.get(cfg.api_key)
            if isinstance(raw_dict, dict):
                all_languages.update(raw_dict.keys())

        for lang_code in all_languages:
            if not lang_code:
                continue

            field_updates: Dict[str, Any] = {}

            for cfg in cfgs:
                raw_dict = item.get(cfg.api_key)
                if not isinstance(raw_dict, dict):
                    continue
                raw_value = raw_dict.get(lang_code)
                if raw_value is None:
                    continue

                try:
                    model_field = trans_model._meta.get_field(cfg.flat_field)
                except FieldDoesNotExist:
                    logger.warning(
                        "Translation field '%s' not found on %s",
                        cfg.flat_field,
                        trans_model.__name__,
                    )
                    continue

                if raw_value == "" and not getattr(model_field, "blank", True):
                    continue

                converted = _parse_field_value(model_field, raw_value)
                transform = cfg.value_transforms.get(cfg.flat_field)
                if transform:
                    converted = transform(converted)
                if converted is not None:
                    field_updates[cfg.flat_field] = converted

            if not field_updates:
                continue

            try:
                trans_model.objects.update_or_create(
                    **{parent_fk: parent_obj, language_fk: lang_code},
                    defaults=field_updates,
                )
            except Exception:
                logger.exception(
                    "Error syncing %s translations for %s pk=%s lang=%s fields=%s",
                    trans_model.__name__,
                    parent_obj.__class__.__name__,
                    parent_obj.pk,
                    lang_code,
                    list(field_updates.keys()),
                )


# ---------------------------------------------------------------------------
# M2M sync via through table
# ---------------------------------------------------------------------------


def _sync_m2m(
    parent_obj: models.Model,
    item: Mapping[str, Any],
    m2m_config: M2MConfig,
    fk_cache: FKCache,
) -> None:
    """Sync one M2M relation via its through table using bulk_create.

    Deletes all existing through-table rows for this parent, then recreates
    them from the current API data. Uses bulk_create for performance with an
    individual-save fallback if bulk_create fails.
    """
    raw_list = item.get(m2m_config.api_key)
    if not isinstance(raw_list, list):
        return

    through_model = m2m_config.through_model
    related_model = m2m_config.related_model

    fk_cache.warmup(related_model)
    through_model.objects.filter(**{m2m_config.parent_fk: parent_obj}).delete()

    to_create = []
    for position, raw_item in enumerate(raw_list):
        ext_id = _extract_external_id_from_url(raw_item)
        if not ext_id:
            continue

        pk = fk_cache.get(related_model, ext_id)
        if pk is None:
            try:
                obj = related_model.objects.get(
                    **{m2m_config.related_lookup_field: ext_id}
                )
                fk_cache.set(related_model, ext_id, obj.pk)
                pk = obj.pk
            except related_model.DoesNotExist:
                logger.warning(
                    "%s with %s=%r not found — sync related models first.",
                    related_model.__name__,
                    m2m_config.related_lookup_field,
                    ext_id,
                )
                continue

        through_kwargs: Dict[str, Any] = {
            m2m_config.parent_fk: parent_obj,
            m2m_config.related_fk: related_model(pk=pk),
        }
        for api_field, through_field in m2m_config.extra_fields.items():
            val = raw_item.get(api_field) if isinstance(raw_item, dict) else None
            if val is None and api_field == "position":
                val = position
            if val is not None:
                through_kwargs[through_field] = val

        to_create.append(through_model(**through_kwargs))

    if not to_create:
        return

    try:
        through_model.objects.bulk_create(to_create, ignore_conflicts=True)
    except Exception:
        logger.warning(
            "bulk_create failed for %s — falling back to individual saves",
            through_model.__name__,
        )
        for obj in to_create:
            try:
                obj.save()
            except Exception:
                logger.exception(
                    "Error creating %s for %s pk=%s",
                    through_model.__name__,
                    parent_obj.__class__.__name__,
                    parent_obj.pk,
                )


# ---------------------------------------------------------------------------
# Main sync function
# ---------------------------------------------------------------------------


def sync_viernulvier(
    model: Type[models.Model],
    config: ModelSyncConfig,
    endpoint: str = DEFAULT_ENDPOINT,
    params: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    etag_cache: Optional[Dict[str, str]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> int:
    """Fetch Viernulvier API data and persist it to a Django model.

    Per-item savepoints ensure one bad record never aborts the full batch.
    The ImportLog is updated with totals and error summaries at the end.

    Args:
        model:        Django model class.
        config:       ModelSyncConfig describing field mapping, translations, M2M.
        endpoint:     Relative API path (e.g. "/productions").
        params:       Optional query parameters forwarded to the API.
        dry_run:      When True, fetch and parse but do not write to the DB.
        etag_cache:   Shared ETag dict; pass the same instance across all sync
                      steps so unchanged endpoints are skipped automatically.
        on_progress:  Callback(saved, total) invoked after each successful save.

    Returns:
        Number of records saved (created + updated). Always 0 in dry_run mode.
    """
    from apps.import_log.models import ImportLog

    source = f"viernulvier:{endpoint}"
    if params:
        params_str = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
        # Guard against max_length violations on ImportLog.source
        suffix = f"?{params_str}"
        source = source[: 200 - len(suffix)] + suffix

    import_log = ImportLog.objects.create(
        source=source,
        status=ImportLog.Status.IN_PROGRESS,
        started_at=timezone.now(),
    )

    try:
        items = fetch_viernulvier(
            endpoint=endpoint, params=params, etag_cache=etag_cache
        )
    except Exception as exc:
        import_log.status = ImportLog.Status.FAILED
        import_log.finished_at = timezone.now()
        import_log.error_message = str(exc)
        import_log.save()
        raise

    if not items:
        import_log.status = ImportLog.Status.SUCCESS
        import_log.records_total = 0
        import_log.records_imported = 0
        import_log.records_failed = 0
        import_log.finished_at = timezone.now()
        import_log.save()
        return 0

    # Pre-warm FK cache for all M2M related models
    fk_cache = FKCache()
    for m2m_cfg in config.m2m:
        fk_cache.warmup(m2m_cfg.related_model)

    saved = 0
    errors = 0
    error_messages: List[str] = []  # capped at MAX_ERROR_MESSAGES
    seen: Set[str] = set()
    total = len(items)

    def _record_error(msg: str) -> None:
        nonlocal errors
        errors += 1
        if len(error_messages) < MAX_ERROR_MESSAGES:
            error_messages.append(msg)

    for item in items:
        if not isinstance(item, dict):
            _record_error(f"Item is not a dict: {item!r}")
            logger.error("Item is not a dict: %r", item)
            continue

        lookup_value = _extract_lookup_value(item, config)

        if config.item_filter and not config.item_filter(item):
            logger.debug("Item filtered out: %s", lookup_value)
            continue

        if lookup_value is None:
            msg = f"Missing '{config.api_id_key}' in item: {str(item)[:200]}"
            logger.warning(msg)
            _record_error(msg)
            continue

        if lookup_value in seen:
            logger.warning("Duplicate item skipped: %s", lookup_value)
            continue
        seen.add(lookup_value)

        if dry_run:
            defaults = _build_defaults(model, item, config, fk_cache)
            logger.info(
                "[DRY RUN] Would save %s (%d fields)", lookup_value, len(defaults)
            )
            saved += 1
            if on_progress:
                on_progress(saved, total)
            continue

        sid = transaction.savepoint()
        try:
            defaults = _build_defaults(model, item, config, fk_cache)

            lookup_kwargs = {config.lookup_field: lookup_value}

            obj, created = model.objects.update_or_create(
                **lookup_kwargs,
                defaults=defaults,
            )

            # Cache the new object so downstream FK lookups within this batch are free
            if hasattr(obj, "external_id"):
                fk_cache.set(model, str(obj.external_id), obj.pk)

            # Batched translation sync: one query per language, not per field
            _sync_all_translations(obj, item, config.translations)

            for m2m_cfg in config.m2m:
                _sync_m2m(obj, item, m2m_cfg, fk_cache)

            transaction.savepoint_commit(sid)
            saved += 1

            if on_progress:
                on_progress(saved, total)

            logger.debug(
                "%s %s: %s",
                "Created" if created else "Updated",
                model.__name__,
                lookup_value,
            )

        except ValidationError as exc:
            transaction.savepoint_rollback(sid)
            msgs = [
                f"{f}: {err}" if f != "__all__" else err
                for f, errs in exc.message_dict.items()
                for err in errs
            ]
            _record_error(f"Validation error for {lookup_value}: {'; '.join(msgs)}")
            logger.error("Validation error for %s: %s", lookup_value, "; ".join(msgs))

        except (IntegrityError, DatabaseError, FieldError):
            transaction.savepoint_rollback(sid)
            exc_type, exc_value, _ = sys.exc_info()
            msg = f"Database error for {lookup_value}: {exc_type.__name__}: {exc_value}"
            _record_error(msg)
            logger.error(msg, exc_info=True)

        except Exception:
            transaction.savepoint_rollback(sid)
            exc_type, exc_value, _ = sys.exc_info()
            msg = (
                f"Unexpected error for {lookup_value}: {exc_type.__name__}: {exc_value}"
            )
            _record_error(msg)
            logger.error(msg, exc_info=True)

    # Finalise import log
    truncation_note = (
        f" (showing first {MAX_ERROR_MESSAGES} of {errors})"
        if errors > MAX_ERROR_MESSAGES
        else ""
    )
    import_log.records_total = total
    import_log.records_imported = saved
    import_log.records_failed = errors
    import_log.finished_at = timezone.now()

    if errors == 0:
        import_log.status = ImportLog.Status.SUCCESS
    elif saved > 0:
        import_log.status = ImportLog.Status.PARTIAL_SUCCESS
        import_log.error_message = (
            f"{errors} records failed{truncation_note}: {', '.join(error_messages)}"
        )
    else:
        import_log.status = ImportLog.Status.FAILED
        import_log.error_message = (
            f"All {errors} records failed{truncation_note}: {', '.join(error_messages)}"
        )

    import_log.save()
    logger.info(
        "Sync complete: saved=%d, errors=%d%s",
        saved,
        errors,
        " [DRY RUN]" if dry_run else "",
    )
    return saved
