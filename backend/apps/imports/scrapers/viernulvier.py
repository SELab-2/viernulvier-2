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
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Type
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
    """Raised when the scraper cannot fetch or normalize Viernulvier data.

    This exception wraps network errors, response shape validation failures,
    and JSON decoding problems so callers can handle a single error type.
    """


def _get_api_key_or_raise() -> str:
    """Return the API key from the environment or raise a scraper error.

    Returns:
        The value of the VIERNULVIER_API_KEY environment variable.

    Raises:
        ScraperError: If VIERNULVIER_API_KEY is missing or empty.

    Side Effects:
        None. This reads environment variables only.
    """
    api_key = os.getenv("VIERNULVIER_API_KEY")
    if not api_key:
        raise ScraperError("VIERNULVIER_API_KEY is not set")
    return api_key


def _build_request_headers() -> Dict[str, str]:
    """Build request headers required by the Viernulvier API.

    Returns:
        A headers dict containing authentication and JSON-LD accept header.

    Raises:
        ScraperError: If the API key is missing.

    Side Effects:
        None. This only assembles a dict from environment configuration.
    """
    return {
        "X-AUTH-TOKEN": _get_api_key_or_raise(),
        "accept": "application/ld+json",
    }


def _normalize_items(items: Sequence[Any]) -> List[Any]:
    """Normalize items by renaming @id to external_id.

    This function performs a shallow copy for dict items that contain "@id"
    to avoid mutating the original API response payload.

    Args:
        items: Items from the API response (list or other sequence).

    Returns:
        List of items with @id renamed to external_id when possible.

    Side Effects:
        None. Returns a new list and copies only dicts with "@id".
    """
    normalized: List[Any] = []
    for item in items:
        if isinstance(item, dict) and "@id" in item:
            # Create a copy and rename @id to external_id
            normalized_item = {k: v for k, v in item.items() if k != "@id"}
            normalized_item["external_id"] = item["@id"]
            normalized.append(normalized_item)
        else:
            normalized.append(item)
    return normalized


def fetch_viernulvier(endpoint: str = DEFAULT_ENDPOINT) -> List[Any]:
    """Fetch items from the Viernulvier JSON-LD API endpoint.

    The endpoint must be a relative API path. The response is expected to be
    JSON-LD, either a collection with a "member" field or a single item with
    an "@context". JSON-LD error payloads are detected and surfaced.

    Args:
        endpoint: Relative API path (e.g., "/events"). Absolute URLs are rejected.

    Returns:
        A list of items from the endpoint, normalized to include external_id when
        @id is present.

    Raises:
        ScraperError: On missing API key, request failures, invalid JSON, JSON-LD
            error payloads, or unexpected payload shapes.

    Side Effects:
        Performs an HTTP GET request to the Viernulvier API.
    """
    parsed = urlparse(endpoint)
    if parsed.scheme or parsed.netloc:
        raise ScraperError(f"endpoint must be a relative path, got: {endpoint!r}")
    url = urljoin(BASE_URL + "/", endpoint.lstrip("/"))
    logger.debug("Fetching Viernulvier endpoint: %s", url)
    try:
        response = requests.get(url, headers=_build_request_headers(), timeout=DEFAULT_TIMEOUT)
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
            return _normalize_items(data["member"])
        # For other dict responses without 'member', wrap in a list
        if "@context" in data:
            # This is likely a single JSON-LD item, wrap it
            return _normalize_items([data])

    # Handle list responses
    if isinstance(data, list):
        return _normalize_items(data)

    raise ScraperError("Unexpected Viernulvier API payload")


def _snake_case_to_camel(value: str) -> str:
    """Convert snake_case to lowerCamelCase.

    Args:
        value: snake_case string.

    Returns:
        lowerCamelCase string.

    Side Effects:
        None. Pure string transformation.
    """
    parts = value.split("_")
    return parts[0] + "".join(part.title() for part in parts[1:])


def _get_item_value(item: Mapping[str, Any], field_name: str) -> Any:
    """Read a value by snake_case or lowerCamelCase field name.

    This allows compatibility between Django model field names (snake_case)
    and JSON-LD payloads that may use lowerCamelCase.

    Args:
        item: Parsed API item data.
        field_name: Model field name (snake_case).

    Returns:
        The matching value or None if not present.

    Side Effects:
        None. Read-only access to the mapping.
    """
    if field_name in item:
        return item[field_name]
    camel = _snake_case_to_camel(field_name)
    if camel in item:
        return item[camel]
    return None


def _extract_api_id(value: Any) -> Optional[int]:
    """Extract a numeric ID from an API value.

    Supports raw integers, numeric strings, JSON-LD @id URLs, or nested dicts.
    This is used for models with integer primary keys.

    Args:
        value: Raw id value from the API.

    Returns:
        Parsed integer ID or None when not extractable.

    Side Effects:
        None. Pure parsing logic.
    """
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
        return _extract_api_id(value.get("external_id") or value.get("@id") or value.get("id"))
    return None


def _extract_item_pk_value(model: Type[models.Model], item: Mapping[str, Any]) -> Optional[Any]:
    """Extract the primary key value for a model from an API item.

    The function tries several common JSON-LD fields (external_id, @id, id)
    and falls back to the model's primary key field name in both snake_case
    and lowerCamelCase forms.

    Args:
        model: Django model class to map the item onto.
        item: Parsed API item.

    Returns:
        Parsed primary key value or None when it cannot be determined.

    Side Effects:
        None. This is pure extraction and normalization.
    """
    raw_id = item.get("external_id") or item.get("@id") or item.get("id")
    if raw_id is None:
        raw_id = _get_item_value(item, model._meta.pk.name)
    if isinstance(raw_id, dict):
        raw_id = raw_id.get("external_id") or raw_id.get("@id") or raw_id.get("id")
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


def _build_model_defaults(model: Type[models.Model], item: Mapping[str, Any], depth: int = 0) -> Dict[str, Any]:
    """Build a defaults dict for update_or_create from an API item.

    This function maps model fields to their JSON-LD equivalents, performs
    type conversions for date/time fields, and resolves foreign keys using
    bounded recursion to avoid deep object graphs.

    Args:
        model: Django model class to map the item onto.
        item: Parsed API item.
        depth: Current relation traversal depth to prevent deep recursion.

    Returns:
        A dict suitable for update_or_create(..., defaults=...).

    Side Effects:
        None directly. It may trigger related object lookups via helpers.
    """
    defaults: Dict[str, Any] = {}
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


def _resolve_fk_value(field: models.Field, raw_value: Any, depth: int) -> Optional[Any]:
    """Resolve a foreign-key value from raw API data.

    If raw_value is a dict, this will optionally materialize the related object
    (bounded by MAX_RELATION_DEPTH). If raw_value is a primitive, this verifies
    existence before returning the primary key.

    Args:
        field: Django model field representing the relation.
        raw_value: Raw API field value.
        depth: Current traversal depth.

    Returns:
        Primary key value for the related object or None when unresolved.

    Side Effects:
        May perform database reads and writes for related objects.
    """
    related_model = field.remote_field.model
    if isinstance(raw_value, dict):
        rel_id = _extract_item_pk_value(related_model, raw_value)
        if depth >= MAX_RELATION_DEPTH:
            return rel_id
        defaults = _build_model_defaults(related_model, raw_value, depth=depth + 1)
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


def _missing_required_fields(model: Type[models.Model], defaults: Mapping[str, Any]) -> List[str]:
    """Return a list of missing required fields based on model metadata.

    Required fields are those that are not auto-created, not nullable, and
    have no default value (including required foreign keys).

    Args:
        model: Django model class.
        defaults: Defaults dict built from the API item.

    Returns:
        List of required field names not present in defaults.

    Side Effects:
        None. Uses model metadata only.
    """
    missing: List[str] = []
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


def sync_viernulvier(model: Type[models.Model], endpoint: str = DEFAULT_ENDPOINT) -> int:
    """Fetch and persist Viernulvier data into a Django model.

    Items are fetched via `fetch_viernulvier`, validated, and then persisted
    with per-item savepoints to isolate errors without aborting the batch.

    Args:
        model: Django model class receiving the API data.
        endpoint: Relative API endpoint (e.g., "/events").

    Returns:
        Number of records created or updated.

    Raises:
        ScraperError: When fetch_viernulvier fails.

    Side Effects:
        Performs database writes, logs summary and error details.
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
                defaults = _build_model_defaults(model, item)
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
