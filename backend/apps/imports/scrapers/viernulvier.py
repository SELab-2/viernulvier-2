"""Viernulvier scraper module.

Architecture: centralized scrapers live in apps/imports/scrapers/.
This allows multiple apps to reuse scraping logic without duplication.

Usage:
    from apps.imports.scrapers.viernulvier import sync_viernulvier
    from apps.events.models import Event
    from apps.imports.transformers.events import EventTransformer

    sync_viernulvier(Event, EventTransformer(), endpoint="/events")
"""

import logging
import os
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type
from urllib.parse import urljoin, urlparse

import requests
from django.core.exceptions import FieldDoesNotExist, FieldError, ValidationError
from django.db import DatabaseError, IntegrityError, transaction, models
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date

from apps.imports.transformers.base import BaseTransformer

logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "https://www.viernulvier.gent/api/v1"
BASE_DOMAIN = "https://www.viernulvier.gent"
DEFAULT_ENDPOINT = "/productions"
DEFAULT_TIMEOUT = 10

# JSON-LD Constants
ERROR_CONTEXT_PATH = "/api/contexts/Error"
JSON_LD_ID_FIELDS = ("external_id", "@id", "id")
JSON_LD_METADATA_FIELDS = ("external_id",)

# Django Integer Field Types
INTEGER_FIELD_TYPES = (
    models.AutoField,
    models.BigAutoField,
    models.IntegerField,
    models.BigIntegerField,
    models.SmallIntegerField,
    models.PositiveIntegerField,
    models.PositiveSmallIntegerField,
)


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


def _fetch_single_page(url: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Fetch a single page from the Viernulvier API.

    Args:
        url: Full URL to fetch (absolute).
        params: Optional query parameters dict to include in the request.

    Returns:
        Parsed JSON response as a dict.

    Raises:
        ScraperError: On request failures, invalid JSON, or JSON-LD error payloads.

    Side Effects:
        Performs an HTTP GET request to the Viernulvier API.
    """
    logger.debug("Fetching Viernulvier page: %s", url)
    try:
        response = requests.get(
            url,
            headers=_build_request_headers(),
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
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
        if data.get("@context") == ERROR_CONTEXT_PATH:
            status = data.get("status", "unknown")
            detail = data.get("detail", "no detail provided")
            error_msg = f"Viernulvier API error: status={status}, detail={detail}"
            logger.error(error_msg)
            raise ScraperError(error_msg)

    return data


def fetch_viernulvier(
    endpoint: str = DEFAULT_ENDPOINT,
    params: Optional[Dict[str, str]] = None,
) -> List[Any]:
    """Fetch items from the Viernulvier JSON-LD API endpoint.

    The endpoint must be a relative API path. The response is expected to be
    JSON-LD, either a collection with a "member" field or a single item with
    an "@context". JSON-LD error payloads are detected and surfaced.

    For paginated endpoints (those with a "view" property), this function
    automatically fetches all pages by following the "next" link.

    Args:
        endpoint: Relative API path (e.g., "/events"). Absolute URLs are rejected.
        params: Optional query parameters dict (e.g., {"created_at[after]": "2024-01-01T00:00:00Z"}).
            Parameters are only applied to the initial request; pagination links from the API
            are followed as-is.

    Returns:
        A list of items from the endpoint (all pages if paginated), normalized
        to include external_id when @id is present.

    Raises:
        ScraperError: On missing API key, request failures, invalid JSON, JSON-LD
            error payloads, or unexpected payload shapes.

    Side Effects:
        Performs HTTP GET requests to the Viernulvier API (possibly multiple for pagination).
    """
    parsed = urlparse(endpoint)
    if parsed.scheme or parsed.netloc:
        raise ScraperError(f"endpoint must be a relative path, got: {endpoint!r}")
    url = urljoin(BASE_URL + "/", endpoint.lstrip("/"))

    all_items: List[Any] = []
    current_url = url
    first_iteration = True

    while current_url:
        data = _fetch_single_page(current_url, params=params if first_iteration else None)
        first_iteration = False

        # Handle JSON-LD @graph member extraction
        if isinstance(data, dict):
            if "member" in data:
                all_items.extend(_normalize_items(data["member"]))
            elif "@context" in data:
                # This is likely a single JSON-LD item, wrap it
                all_items.extend(_normalize_items([data]))
            else:
                # Dict without @context or member is unexpected
                raise ScraperError("Unexpected Viernulvier API payload")

            # Check if there's a "next" page in the view property
            view = data.get("view")
            if isinstance(view, dict) and "next" in view:
                next_url = view["next"]
                # The next_url from the API is an absolute path like /api/v1/events?page=2
                # Construct the full URL correctly
                if next_url.startswith("http"):
                    current_url = next_url
                else:
                    # It's a relative path, join it with the base domain
                    current_url = urljoin(BASE_DOMAIN, next_url)
            else:
                # No more pages
                current_url = None
        elif isinstance(data, list):
            # Handle list responses (non-paginated)
            all_items.extend(_normalize_items(data))
            current_url = None
        else:
            raise ScraperError("Unexpected Viernulvier API payload")

    return all_items



def _is_integer_field(field: models.Field) -> bool:
    """Check if a Django field is an integer type.

    Args:
        field: Django model field to check.

    Returns:
        True if the field is an integer type, False otherwise.

    Side Effects:
        None. Pure type checking.
    """
    return isinstance(field, INTEGER_FIELD_TYPES)


def _convert_field_value(field: models.Field, value: Any) -> Optional[Any]:
    """Convert an API value to the appropriate type for a Django model field.

    Args:
        field: Django model field.
        value: Raw API field value (already transformed by transformer).

    Returns:
        Converted value suitable for the field type, or None if conversion fails.

    Raises:
        ValueError: If a datetime string cannot be parsed.

    Side Effects:
        None. Pure type conversion.
    """
    if value is None:
        return None


    # Handle datetime fields
    if isinstance(field, models.DateTimeField):
        if isinstance(value, str):
            if value.startswith("-"):
                value = value[1:]
            if value[:4] == "0000":
                value = "1970" + value[4:]
            return parse_datetime(value)
        return value

    # Handle date fields
    if isinstance(field, models.DateField):
        if isinstance(value, str):
            return parse_date(value)
        return value

    # Handle all other field types - return as-is
    return value



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
        for field_name in JSON_LD_ID_FIELDS:
            if field_value := value.get(field_name):
                return _extract_api_id(field_value)
    return None


def _extract_item_pk_value(model: Type[models.Model], item: Mapping[str, Any]) -> Optional[Any]:
    """Extract the primary key value for a model from an API item.

    The function tries several common JSON-LD fields (external_id, @id, id)
    and falls back to the model's primary key field name.

    Args:
        model: Django model class to map the item onto.
        item: Parsed API item (already transformed).

    Returns:
        Parsed primary key value or None when it cannot be determined.

    Side Effects:
        None. This is pure extraction and normalization.
    """
    raw_id = item.get("external_id") or item.get("@id") or item.get("id")
    if raw_id is None:
        raw_id = item.get(model._meta.pk.name)
    if isinstance(raw_id, dict):
        extracted_id = raw_id.get("external_id") or raw_id.get("@id") or raw_id.get("id")
        if extracted_id is None:
            raw_id = raw_id.get(model._meta.pk.name)
        else:
            raw_id = extracted_id
    if raw_id in (None, ""):
        return None
    pk_field = model._meta.pk
    if _is_integer_field(pk_field):
        return _extract_api_id(raw_id)
    return str(raw_id)


def _build_model_defaults(
    model: Type[models.Model], item: Mapping[str, Any]
) -> Dict[str, Any]:
    """Build a defaults dict for update_or_create from a transformed API item.

    This function maps transformed fields to model fields, automatically handling
    type conversions for date/time fields. The transformer must have already handled
    field name mapping and foreign key resolution.

    Args:
        model: Django model class to map the item onto.
        item: Transformed API item (output from transformer.transform()).

    Returns:
        A dict suitable for update_or_create(..., defaults=...).

    Raises:
        ScraperError: If required model fields are missing from the transformed data.

    Side Effects:
        None. Type conversion only.
    """
    defaults: Dict[str, Any] = {}

    # Map each field from the transformed item to the model
    for key, value in item.items():
        # Skip JSON-LD metadata fields
        if key.startswith("@") or key in JSON_LD_METADATA_FIELDS:
            continue

        if value is None:
            continue

        # Try to find the corresponding model field
        try:
            field = model._meta.get_field(key)
        except FieldDoesNotExist:
            # Field doesn't exist in model, skip it silently
            logger.debug("Skipping unknown field '%s' for model %s", key, model.__name__)
            continue

        # Skip reverse relations (e.g., ManyToOneRel) that aren't real model fields
        if not isinstance(field, models.Field):
            logger.debug("Skipping reverse relation '%s' for model %s", key, model.__name__)
            continue

        # Skip primary key fields
        if field.primary_key:
            continue

        # Convert the value based on field type
        converted_value = _convert_field_value(field, value)
        if converted_value is not None:
            defaults[field.name] = converted_value

    # Validate that all required fields are present
    missing = _missing_required_fields(model, defaults)
    if missing:
        raise ScraperError(f"Missing required fields for {model.__name__}: {', '.join(missing)}")

    return defaults



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
            if f"{field.name}" not in defaults:
                missing.append(field.name)
            continue
        if field.name not in defaults:
            missing.append(field.name)
    return missing


def sync_viernulvier(
    model: Type[models.Model],
    transformer: BaseTransformer,
    endpoint: str = DEFAULT_ENDPOINT,
    params: Optional[Dict[str, str]] = None,
) -> int:
    """Fetch and persist Viernulvier data into a Django model.

    Items are fetched via `fetch_viernulvier`, transformed using the provided
    transformer, validated, and then persisted with per-item savepoints to
    isolate errors without aborting the batch.

    An ImportLog entry is created to track the import operation.

    Args:
        model: Django model class receiving the API data.
        transformer: BaseTransformer instance to transform API items to model fields.
        endpoint: Relative API endpoint (e.g., "/events").
        params: Optional query parameters dict (e.g., {"created_at[after]": "2024-01-01T00:00:00Z"})
            to filter results at the API level.

    Returns:
        Number of records created or updated.

    Raises:
        ScraperError: When fetch_viernulvier fails.

    Side Effects:
        Performs database writes, logs summary and error details, creates ImportLog entry.
    """
    # Import here to avoid circular dependency
    from apps.import_log.models import ImportLog

    # Build source name from endpoint and params
    source = f"viernulvier:{endpoint}"
    if params:
        params_str = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
        source = f"{source}?{params_str}"

    # Create import log entry
    import_log = ImportLog.objects.create(
        source=source,
        status=ImportLog.Status.IN_PROGRESS,
        started_at=timezone.now(),
    )

    try:
        items = fetch_viernulvier(endpoint=endpoint, params=params)

        saved = 0
        errors = 0
        error_messages = []
        seen = set()

        with transaction.atomic():
            for item in items:
                # Validate item is a dict
                if not isinstance(item, dict):
                    msg = f"Item is not a dict: {item}"
                    logger.error(msg)
                    errors += 1
                    error_messages.append(msg)
                    continue

                # Transform the raw API item using the provided transformer
                try:
                    transformed_item = transformer.transform(item)
                except Exception as e:
                    msg = f"Transformer error for item: {e}"
                    logger.error(msg, exc_info=True)
                    errors += 1
                    error_messages.append(msg)
                    continue

                # Extract @id from the original item (before transformation)
                item_id = _extract_item_pk_value(model, item)

                # Validate item_id is not empty
                if item_id is None:
                    msg = f"Missing @id for item: {item}"
                    logger.warning(msg)
                    errors += 1
                    error_messages.append(msg)
                    continue

                # Check for duplicates in current batch
                if item_id in seen:
                    msg = f"Duplicate @id in batch: {item_id}"
                    logger.warning(msg)
                    error_messages.append(msg)
                    continue

                seen.add(item_id)

                # Persist item with savepoint isolation
                sid = transaction.savepoint()
                try:
                    defaults = _build_model_defaults(model, transformed_item)
                    missing = _missing_required_fields(model, defaults)
                    if missing:
                        msg = f"Missing required fields for @id={item_id}: {', '.join(missing)}"
                        logger.warning(msg)
                        transaction.savepoint_rollback(sid)
                        errors += 1
                        error_messages.append(msg)
                        continue

                    model.objects.update_or_create(
                        **{model._meta.pk.name: item_id},
                        defaults=defaults,
                    )
                    transaction.savepoint_commit(sid)
                    saved += 1
                except ValidationError as e:
                    transaction.savepoint_rollback(sid)
                    # Make ValidationErrors readable
                    messages = []
                    for field, errs in e.message_dict.items():
                        for err in errs:
                            if field == "__all__":
                                messages.append(f"{err}")
                            else:
                                messages.append(f"{field}: {err}")
                    msg = f"Validation error for @id={item_id}: {'; '.join(messages)}"
                    logger.error(msg)
                    errors += 1
                    error_messages.append(msg)

                except (IntegrityError, DatabaseError, FieldError):
                    transaction.savepoint_rollback(sid)
                    exc_type, exc_value, exc_tb = sys.exc_info()
                    msg = f"Database error for @id={item_id}: {exc_type.__name__}: {exc_value}"
                    logger.error(msg, exc_info=True)
                    errors += 1
                    error_messages.append(msg)

        # Update import log with final status
        import_log.records_total = len(items)
        import_log.records_imported = saved
        import_log.records_failed = errors
        import_log.finished_at = timezone.now()

        if errors == 0:
            import_log.status = ImportLog.Status.SUCCESS
        elif saved > 0:
            import_log.status = ImportLog.Status.PARTIAL_SUCCESS
            import_log.error_message = f"{errors} records failed to import: {', '.join(error_messages)}"
        else:
            import_log.status = ImportLog.Status.FAILED
            import_log.error_message = f"All {errors} records failed to import: {', '.join(error_messages)}"

        import_log.save()

        logger.info(
            "Viernulvier sync finished: Saved=%s, Errors=%s",
            saved,
            errors,
        )
        return saved

    except Exception as exc:
        # Update import log with error status
        import_log.status = ImportLog.Status.FAILED
        import_log.finished_at = timezone.now()
        import_log.error_message = str(exc)
        import_log.save()
        raise
