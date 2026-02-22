import logging
import os
from urllib.parse import urljoin

import requests
from django.db import IntegrityError


logger = logging.getLogger(__name__)

BASE_URL = "https://viernulvier.gent/api"
DEFAULT_ENDPOINT = "/events"
DEFAULT_TIMEOUT = 10


class ScraperError(Exception):
    pass


def _get_api_key():
    api_key = os.getenv("VIERNULVIER_API_KEY")
    if not api_key:
        raise ScraperError("VIERNULVIER_API_KEY is not set")
    return api_key


def _build_headers():
    return {"X-Api-Key": _get_api_key()}


def fetch_viernulvier(endpoint=DEFAULT_ENDPOINT):
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
    if "id" in item and item.get("id") is not None:
        external_id = item.get("id")
    elif "uuid" in item and item.get("uuid") is not None:
        external_id = item.get("uuid")
    else:
        external_id = item.get("slug")
    return {
        "external_id": str(external_id) if external_id is not None else None,
        "payload": item,
    }


def sync_viernulvier(model, endpoint=DEFAULT_ENDPOINT, transform=default_transform):
    items = fetch_viernulvier(endpoint=endpoint)
    saved = 0
    seen = set()

    for item in items:
        try:
            data = transform(item)
        except Exception as exc:
            logger.exception("Transform error for item: %s", item)
            raise ScraperError("Transform error while syncing item") from exc
        external_id = data.pop("external_id", None)
        if not external_id:
            logger.warning("Skipping item without external_id: %s", item)
            continue
        if external_id in seen:
            logger.warning("Duplicate external_id in batch: %s", external_id)
            continue
        seen.add(external_id)

        try:
            model.objects.update_or_create(external_id=external_id, defaults=data)
        except IntegrityError as exc:
            logger.exception("Database error while syncing item: %s", external_id)
            raise ScraperError("Database error while syncing item") from exc

        saved += 1

    logger.info("Synced %s items from Viernulvier", saved)
    return saved
