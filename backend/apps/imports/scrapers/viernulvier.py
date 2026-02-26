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
from django.core.exceptions import FieldError, ValidationError
from django.db import DatabaseError, IntegrityError, transaction, models
from django.utils.dateparse import parse_datetime, parse_date

logger = logging.getLogger(__name__)

BASE_URL = "https://www.viernulvier.gent/api/v1"
DEFAULT_ENDPOINT = "/productions"
DEFAULT_TIMEOUT = 10
MAX_RELATION_DEPTH = 2


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


def _snake_to_camel(value):
    parts = value.split("_")
    return parts[0] + "".join(part.title() for part in parts[1:])


def _get_item_value(item, field_name):
    if field_name in item:
        return item[field_name]
    camel = _snake_to_camel(field_name)
    if camel in item:
        return item[camel]
    return None


def _extract_api_id(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
        parsed = urlparse(text)
        path = parsed.path if parsed.scheme or parsed.netloc else text
        tail = path.rstrip("/").split("/")[-1]
        return int(tail) if tail.isdigit() else None
    if isinstance(value, dict):
        return _extract_api_id(value.get("@id") or value.get("id"))
    return None


def _extract_item_id(model, item):
    raw_id = item.get("@id") or item.get("id")
    if isinstance(raw_id, dict):
        raw_id = raw_id.get("@id") or raw_id.get("id")
    if raw_id in (None, ""):
        return None
    pk_field = model._meta.pk
    if isinstance(
        pk_field,
        (
            models.AutoField,
            models.BigAutoField,
            models.IntegerField,
            models.BigIntegerField,
            models.SmallIntegerField,
            models.PositiveIntegerField,
            models.PositiveSmallIntegerField,
        ),
    ):
        return _extract_api_id(raw_id)
    return str(raw_id)


def _extract_item_pk_value(model, item):
    raw_id = item.get("@id") or item.get("id")
    if raw_id is None:
        raw_id = _get_item_value(item, model._meta.pk.name)
    if isinstance(raw_id, dict):
        raw_id = raw_id.get("@id") or raw_id.get("id")
        if raw_id is None:
            raw_id = _get_item_value(raw_id, model._meta.pk.name)
    if raw_id in (None, ""):
        return None
    pk_field = model._meta.pk
    if isinstance(
        pk_field,
        (
            models.AutoField,
            models.BigAutoField,
            models.IntegerField,
            models.BigIntegerField,
            models.SmallIntegerField,
            models.PositiveIntegerField,
            models.PositiveSmallIntegerField,
        ),
    ):
        return _extract_api_id(raw_id)
    return str(raw_id)


def _build_defaults(model, item, depth=0):
    defaults = {}
    for field in model._meta.fields:
        if field.primary_key:
            continue
        raw_value = _get_item_value(item, field.name)
        if raw_value is None:
            continue
        if field.is_relation and field.many_to_one:
            rel_id = _resolve_fk_value(field, raw_value, depth)
            if rel_id is None:
                continue
            defaults[f"{field.name}_id"] = rel_id
            continue
        if isinstance(field, models.DateTimeField):
            if isinstance(raw_value, str):
                defaults[field.name] = parse_datetime(raw_value)
            else:
                defaults[field.name] = raw_value
            continue
        if isinstance(field, models.DateField):
            if isinstance(raw_value, str):
                defaults[field.name] = parse_date(raw_value)
            else:
                defaults[field.name] = raw_value
            continue
        defaults[field.name] = raw_value
    return defaults


def _resolve_fk_value(field, raw_value, depth):
    related_model = field.remote_field.model
    if isinstance(raw_value, dict):
        rel_id = _extract_item_pk_value(related_model, raw_value)
        if depth >= MAX_RELATION_DEPTH:
            return rel_id
        defaults = _build_defaults(related_model, raw_value, depth=depth + 1)
        missing = _missing_required_fields(related_model, defaults)
        if missing:
            return None
        try:
            if rel_id is None:
                obj = related_model.objects.create(**defaults)
            else:
                obj, _ = related_model.objects.update_or_create(
                    **{related_model._meta.pk.name: rel_id},
                    defaults=defaults,
                )
            return obj.pk
        except (IntegrityError, DatabaseError, FieldError, ValidationError):
            logger.debug(
                "Skipping related %s due to validation/db error",
                related_model.__name__,
                exc_info=True,
            )
            return None

    if isinstance(raw_value, (str, int)):
        pk_field = related_model._meta.pk
        if isinstance(
            pk_field,
            (
                models.AutoField,
                models.BigAutoField,
                models.IntegerField,
                models.BigIntegerField,
                models.SmallIntegerField,
                models.PositiveIntegerField,
                models.PositiveSmallIntegerField,
            ),
        ):
            rel_id = _extract_api_id(raw_value)
        else:
            rel_id = str(raw_value)
        if rel_id is None:
            return None
        if related_model.objects.filter(pk=rel_id).exists():
            return rel_id
    return None


def _missing_required_fields(model, defaults):
    missing = []
    for field in model._meta.fields:
        if field.primary_key or field.auto_created:
            continue
        if field.has_default() or field.null or getattr(field, "blank", False):
            continue
        if field.is_relation and field.many_to_one:
            if f"{field.name}_id" not in defaults:
                missing.append(field.name)
            continue
        if field.name not in defaults:
            missing.append(field.name)
    return missing


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
            item_id = _extract_item_pk_value(model, item)

            # Validate item_id is not empty
            if item_id is None:
                logger.warning("Skipping item without @id: %s", item)
                errors += 1
                continue

            # Check for duplicates in current batch
            if item_id in seen:
                logger.warning("Duplicate @id in batch: %s", item_id)
                continue

            seen.add(item_id)

            # Persist item with savepoint isolation
            sid = transaction.savepoint()
            try:
                defaults = _build_defaults(model, item)
                missing = _missing_required_fields(model, defaults)
                if missing:
                    logger.warning(
                        "Skipping item @id=%s due to missing fields: %s",
                        item_id,
                        ", ".join(missing),
                    )
                    transaction.savepoint_rollback(sid)
                    errors += 1
                    continue

                model.objects.update_or_create(
                    **{model._meta.pk.name: item_id},
                    defaults=defaults,
                )
                transaction.savepoint_commit(sid)
                saved += 1
            except (IntegrityError, DatabaseError, FieldError, ValidationError):
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
