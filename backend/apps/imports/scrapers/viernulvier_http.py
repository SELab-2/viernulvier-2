"""HTTP session, retry, and pagination helpers for Viernulvier endpoints."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
import random
import re
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter

from .viernulvier_constants import (
    BASE_DOMAIN,
    BASE_URL,
    DEFAULT_ENDPOINT,
    DEFAULT_TIMEOUT,
    ERROR_CONTEXT_PATH,
    MAX_CONCURRENT_PAGES,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    RETRY_BACKOFF_MAX,
    RETRY_STATUS_CODES,
    USER_AGENT_POOL,
    RateLimitError,
    ScraperError,
)

logger = logging.getLogger("apps.imports.scrapers.viernulvier")

if TYPE_CHECKING:
    from collections.abc import Callable


def get_api_key_or_raise() -> str:
    """Return the configured API key used to authenticate scraper requests."""
    api_key = os.getenv("VIERNULVIER_API_KEY")
    if not api_key:
        raise ScraperError("VIERNULVIER_API_KEY environment variable is not set")
    return api_key


def build_session() -> requests.Session:
    """Create a requests.Session with connection pooling and shared auth headers."""
    session = requests.Session()
    session.headers.update(
        {
            "X-AUTH-TOKEN": get_api_key_or_raise(),
            "accept": "application/ld+json",
            "User-Agent": random.choice(USER_AGENT_POOL),
        }
    )
    adapter = HTTPAdapter(
        pool_connections=MAX_CONCURRENT_PAGES,
        pool_maxsize=MAX_CONCURRENT_PAGES * 2,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def backoff_seconds(
    attempt: int,
    backoff_base: float = RETRY_BACKOFF_BASE,
    backoff_max: float = RETRY_BACKOFF_MAX,
) -> float:
    """Exponential backoff with full jitter."""
    return min(backoff_base * (2**attempt) + random.uniform(0, 1), backoff_max)


def parse_retry_after(response: requests.Response) -> int | None:
    """Parse the Retry-After header as an integer number of seconds."""
    header = response.headers.get("Retry-After")
    if header:
        try:
            return int(header)
        except ValueError:
            pass
    return None


def fetch_with_retry(  # noqa: C901, PLR0912, PLR0915
    session: requests.Session,
    url: str,
    params: dict[str, str] | None = None,
    etag: str | None = None,
    *,
    max_retries: int = MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT,
    retry_status_codes: set[int] = RETRY_STATUS_CODES,
    sleep_fn: Callable[[float], None] = time.sleep,
    backoff_fn: Callable[[int], float] = backoff_seconds,
    parse_retry_after_fn: Callable[[requests.Response], int | None] = parse_retry_after,
) -> tuple[Any | None, str | None]:
    """Fetch one URL with retry + exponential backoff + jitter."""
    headers: dict[str, str] = {}
    if etag:
        headers["If-None-Match"] = etag

    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, params=params, headers=headers, timeout=timeout)
        except requests.ConnectionError as exc:
            if attempt == max_retries:
                raise ScraperError(f"Connection failed after {max_retries} attempts: {url}") from exc
            wait = backoff_fn(attempt)
            logger.warning("ConnectionError - retry %d in %.1fs: %s", attempt + 1, wait, url)
            sleep_fn(wait)
            continue
        except requests.Timeout as exc:
            if attempt == max_retries:
                raise ScraperError(f"Request timed out after {max_retries} attempts: {url}") from exc
            wait = backoff_fn(attempt)
            logger.warning("Timeout - retry %d in %.1fs: %s", attempt + 1, wait, url)
            sleep_fn(wait)
            continue
        except requests.RequestException as exc:
            raise ScraperError(f"Request failed: {url}") from exc

        if response.status_code == 304:
            logger.debug("304 Not Modified - page unchanged: %s", url)
            return None, etag

        if response.status_code == 429:
            retry_after = parse_retry_after_fn(response)
            if attempt == max_retries:
                raise RateLimitError(retry_after)
            wait = float(retry_after) if retry_after else backoff_fn(attempt)
            logger.warning("HTTP 429 - waiting %.1fs before retry %d: %s", wait, attempt + 1, url)
            sleep_fn(wait)
            continue

        if response.status_code in retry_status_codes:
            if attempt == max_retries:
                raise ScraperError(f"HTTP {response.status_code} after {max_retries} attempts: {url}")
            wait = backoff_fn(attempt)
            logger.warning("HTTP %d - retry %d in %.1fs: %s", response.status_code, attempt + 1, wait, url)
            sleep_fn(wait)
            continue

        if not response.ok:
            raise ScraperError(f"API error: {response.status_code} - {url}")

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

    raise ScraperError(f"Retries exhausted for: {url}")


def discover_extra_pages(data: dict, *, base_domain: str = BASE_DOMAIN) -> list[str]:
    """Discover page URLs beyond page 1 from hydra:view metadata."""
    view = data.get("view") or {}
    last_url = view.get("last", "")

    match = re.search(r"[?&]page=(\d+)", last_url)
    if not match:
        return []

    total_pages = int(match.group(1))
    pages = []
    for page_num in range(2, total_pages + 1):
        page_url = re.sub(r"([?&])page=\d+", rf"\g<1>page={page_num}", last_url)
        if not page_url.startswith("http"):
            page_url = urljoin(base_domain, page_url)
        pages.append(page_url)
    return pages


def fetch_viernulvier_impl(  # noqa: C901, PLR0912, PLR0915
    endpoint: str = DEFAULT_ENDPOINT,
    params: dict[str, str] | None = None,
    etag_cache: dict[str, str] | None = None,
    *,
    base_url: str = BASE_URL,
    base_domain: str = BASE_DOMAIN,
    build_session_fn: Callable[[], requests.Session] = build_session,
    fetch_with_retry_fn: Callable[..., tuple[Any | None, str | None]] = fetch_with_retry,
    discover_extra_pages_fn: Callable[[dict], list[str]] = discover_extra_pages,
) -> list[Any]:
    """Fetch all items from an API endpoint, following pagination automatically."""
    parsed = urlparse(endpoint)
    if parsed.scheme or parsed.netloc:
        raise ScraperError(f"endpoint must be a relative path, got: {endpoint!r}")

    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    etag_cache = etag_cache if etag_cache is not None else {}
    session = build_session_fn()

    logger.info("Fetching: %s", url)
    data, new_etag = fetch_with_retry_fn(session, url, params=params, etag=etag_cache.get(url))
    if new_etag:
        etag_cache[url] = new_etag

    if data is None:
        logger.info("304 Not Modified for %s - nothing to sync.", url)
        return []

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        raise ScraperError(f"Unexpected payload type: {type(data)}")

    members = data.get("member", [])
    if not members and "@context" in data:
        members = [data]
    all_items: list[Any] = list(members)

    total_items = data.get("totalItems") or data.get("hydra:totalItems")
    extra_pages = discover_extra_pages_fn(data)

    if total_items:
        logger.info("API reports %d total items - %d additional pages to fetch", total_items, len(extra_pages))

    if extra_pages:
        page_results: dict[str, list[Any]] = {}

        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PAGES) as executor:
            future_to_url = {
                executor.submit(fetch_with_retry_fn, session, page_url, None, etag_cache.get(page_url)): page_url
                for page_url in extra_pages
            }
            for future in as_completed(future_to_url):
                page_url = future_to_url[future]
                try:
                    page_data, page_etag = future.result()
                    if page_etag:
                        etag_cache[page_url] = page_etag
                    if page_data is None:
                        continue
                    page_results[page_url] = page_data.get("member", []) if isinstance(page_data, dict) else page_data
                except ScraperError:
                    logger.exception("Page fetch failed for %s", page_url)

        for page_url in extra_pages:
            all_items.extend(page_results.get(page_url, []))
    else:
        view = data.get("view") or {}
        next_raw = view.get("next")
        current_url: str | None = (
            (next_raw if next_raw.startswith("http") else urljoin(base_domain, next_raw)) if next_raw else None
        )
        while current_url:
            page_data, page_etag = fetch_with_retry_fn(session, current_url, etag=etag_cache.get(current_url))
            if page_etag:
                etag_cache[current_url] = page_etag
            if page_data is None:
                break
            if isinstance(page_data, dict):
                all_items.extend(page_data.get("member", []))
                next_view = page_data.get("view") or {}
                next_raw = next_view.get("next")
                current_url = (
                    (next_raw if next_raw.startswith("http") else urljoin(base_domain, next_raw)) if next_raw else None
                )
            else:
                all_items.extend(page_data if isinstance(page_data, list) else [])
                break

    logger.info("Fetched %d items from %s", len(all_items), endpoint)
    return all_items
