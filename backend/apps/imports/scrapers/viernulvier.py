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

BASE_URL = "https://viernulvier.gent/api/v1"
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

    if isinstance(data, dict) and "items" in data:
        return data["items"]
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    if isinstance(data, list):
        return data

    raise ScraperError("Unexpected Viernulvier API payload")


def default_transform(item):
    """Transform a raw API item into a standard payload dict.

    Expects a dict and returns {"external_id": str|None, "payload": item}.
    Raises ScraperError for non-dict inputs.
    """
    if not isinstance(item, dict):
        raise ScraperError("Invalid item type for default_transform")

    external_id = next((item.get(key) for key in ("id", "uuid", "slug") if item.get(key) is not None), None)

    return {
        "external_id": str(external_id) if external_id is not None else None,
        "payload": item,
    }


def _validate_transformed_data(data, item):
    """Validate that transformed data has the correct structure.

    Returns: (external_id, is_valid, error_message)
    """
    if not isinstance(data, dict) or "payload" not in data:
        return None, False, f"Invalid transform output for item: {item}"

    external_id = data.pop("external_id", None)
    if external_id is None or str(external_id).strip() == "":
        return None, False, f"Skipping item without external_id: {item}"

    return str(external_id), True, None


def sync_viernulvier(model, endpoint=DEFAULT_ENDPOINT, transform=default_transform):
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
            # Transform item
            try:
                data = transform(item)
            except Exception:
                logger.exception(
                    "Unexpected error while transforming item %s",
                    item.get("id") if isinstance(item, dict) else item,
                )
                errors += 1
                continue

            # Validate transformed data
            external_id, is_valid, error_msg = _validate_transformed_data(data, item)

            if not is_valid:
                if "without external_id" in error_msg:
                    logger.warning(error_msg)
                else:
                    logger.error(error_msg)
                errors += 1
                continue

            # Check for duplicates in current batch
            if external_id in seen:
                logger.warning("Duplicate external_id in batch: %s", external_id)
                continue

            seen.add(external_id)

            # Persist item with savepoint isolation
            sid = transaction.savepoint()
            try:
                model.objects.update_or_create(
                    external_id=external_id,
                    defaults=data,
                )
                transaction.savepoint_commit(sid)
                saved += 1
            except (IntegrityError, DatabaseError, FieldError):
                transaction.savepoint_rollback(sid)
                logger.error(
                    "Database error while syncing item with external_id=%s. Continuing.",
                    external_id,
                    exc_info=True,
                )
                errors += 1

    logger.info(
        "Viernulvier sync finished: Saved=%s, Errors=%s",
        saved,
        errors,
    )
    return saved
