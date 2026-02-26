"""Viernulvier scraper module.

Architecture: centralized scrapers live in apps/imports/scrapers/.
This allows multiple apps to reuse scraping logic without duplication.

Usage:
    from apps.imports.scrapers.viernulvier import sync_viernulvier
    from apps.events.models import Event

    sync_viernulvier(Event, endpoint="/events")
"""

import logging
import os
from urllib.parse import urljoin, urlparse

import requests
from django.core.exceptions import FieldError
from django.db import DatabaseError, IntegrityError, transaction

logger = logging.getLogger(__name__)

BASE_URL = "https://www.viernulvier.gent/api/v1"
DEFAULT_ENDPOINT = "/productions"
DEFAULT_TIMEOUT = 10


class ScraperError(Exception):
    pass


def _get_api_key():
    api_key = os.getenv("VIERNULVIER_API_KEY")
    if not api_key:
        raise ScraperError("VIERNULVIER_API_KEY is not set")
    return api_key


def _build_headers():
    return {
        "X-AUTH-TOKEN":  _get_api_key(),
        "accept": "application/ld+json"
    }


def fetch_viernulvier(endpoint=DEFAULT_ENDPOINT):
    parsed = urlparse(endpoint)
    if parsed.scheme or parsed.netloc:
        raise ScraperError(f"endpoint must be a relative path, got: {endpoint!r}")
    url = urljoin(BASE_URL + "/", endpoint.lstrip("/"))
    logger.debug("Fetching Viernulvier endpoint: %s", url)
    try:
        response = requests.get(url, headers=_build_headers(), timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        logger.exception("Viernulvier API request failed")
        raise ScraperError("Request to Viernulvier API failed") from exc

    if not response.ok:
        logger.error("Viernulvier API error: %s %s", response.status_code, response.text)
        raise ScraperError(f"Viernulvier API error: {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        logger.exception("Invalid JSON from Viernulvier API")
        raise ScraperError("Invalid JSON from Viernulvier API") from exc

    if data is None:
        raise ScraperError("Unexpected Viernulvier API payload")

    # Handle JSON-LD error responses
    if isinstance(data, dict):
        if data.get("@context") == "/api/contexts/Error":
            status = data.get("status", "unknown")
            detail = data.get("detail", "no detail provided")
            error_msg = f"Viernulvier API error: status={status}, detail={detail}"
            logger.error(error_msg)
            raise ScraperError(error_msg)

    # Handle JSON-LD @graph member extraction
    if isinstance(data, dict):
        if "member" in data:
            return data["member"]
        # For other dict responses without 'member', wrap in a list
        if "@context" in data:
            # This is likely a single JSON-LD item, wrap it
            return [data]

    # Handle list responses
    if isinstance(data, list):
        return data

    raise ScraperError("Unexpected Viernulvier API payload")


def sync_viernulvier(model, endpoint=DEFAULT_ENDPOINT):
    """Fetch and persist Viernulvier data into a Django model.

    Example:
        from apps.events.models import ViernulvierItem
        sync_viernulvier(ViernulvierItem, endpoint="/events")
    """
    items = fetch_viernulvier(endpoint=endpoint)

    saved = 0
    errors = 0
    seen = set()

    with transaction.atomic():
        for item in items:
            # Validate item is a dict
            if not isinstance(item, dict):
                logger.error(
                    "Unexpected error while processing item: item is not a dict: %s",
                    item,
                )
                errors += 1
                continue

            # Extract @id
            item_id = item.get("@id")

            # Validate item_id is not empty
            if item_id is None or str(item_id).strip() == "":
                logger.warning("Skipping item without @id: %s", item)
                errors += 1
                continue

            item_id = str(item_id)

            # Check for duplicates in current batch
            if item_id in seen:
                logger.warning("Duplicate @id in batch: %s", item_id)
                continue

            seen.add(item_id)

            # Persist item with savepoint isolation
            sid = transaction.savepoint()
            try:
                # Prepare defaults without @id since it's used as the lookup key
                defaults = {k: v for k, v in item.items() if k != "@id"}
                model.objects.update_or_create(
                    id=item_id,
                    defaults=defaults,
                )
                transaction.savepoint_commit(sid)
                saved += 1
            except (IntegrityError, DatabaseError, FieldError):
                transaction.savepoint_rollback(sid)
                logger.error(
                    "Database error while syncing item with @id=%s. Continuing.",
                    item_id,
                    exc_info=True,
                )
                errors += 1

    logger.info(
        "Viernulvier sync finished: Saved=%s, Errors=%s",
        saved,
        errors,
    )
    return saved
