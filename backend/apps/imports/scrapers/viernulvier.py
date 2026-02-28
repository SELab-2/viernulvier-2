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
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type
from urllib.parse import urljoin, urlparse

import requests
from django.core.exceptions import FieldDoesNotExist, FieldError, ValidationError
from django.db import DatabaseError, IntegrityError, transaction, models
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date

logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "https://www.viernulvier.gent/api/v1"
BASE_DOMAIN = "https://www.viernulvier.gent"
DEFAULT_ENDPOINT = "/productions"
DEFAULT_TIMEOUT = 10
MAX_RELATION_DEPTH = 2

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

def _camel_to_snake_case(value: str) -> str:
    """Convert lowerCamelCase or UpperCamelCase to snake_case.

    Args:
        value: camelCase string.

    Returns:
        snake_case string.

    Side Effects:
        None. Pure string transformation.
    """
    # Insert underscore before uppercase letters and convert to lowercase
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    return snake


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


def _convert_field_value(field: models.Field, value: Any, depth: int) -> Optional[Any]:
    """Convert an API value to the appropriate type for a Django model field.

    Args:
        field: Django model field.
        value: Raw API field value.
        depth: Current traversal depth for FK resolution.

    Returns:
        Converted value suitable for the field type, or None if conversion fails.

    Raises:
        ValueError: If a datetime string cannot be parsed.

    Side Effects:
        May perform database reads and writes for related objects.
    """
    if value is None:
        return None

    # Handle foreign key fields
    if field.is_relation and field.many_to_one:
        return _resolve_fk_value(field, value, depth)

    # Handle datetime fields
    if isinstance(field, models.DateTimeField):
        if isinstance(value, str):
            try:
                return parse_datetime(value)
            except ValueError as e:
                logger.warning("Failed to parse datetime value '%s' for field '%s'", value, field.name)
                raise ScraperError(e) # TODO: should not throw error
        return value

    # Handle date fields
    if isinstance(field, models.DateField):
        if isinstance(value, str):
            return parse_date(value)
        return value

    # Handle all other field types - return as-is
    return value


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
        for field_name in JSON_LD_ID_FIELDS:
            if field_value := value.get(field_name):
                return _extract_api_id(field_value)
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
        extracted_id = raw_id.get("external_id") or raw_id.get("@id") or raw_id.get("id")
        if extracted_id is None:
            raw_id = _get_item_value(raw_id, model._meta.pk.name)
        else:
            raw_id = extracted_id
    if raw_id in (None, ""):
        return None
    pk_field = model._meta.pk
    if _is_integer_field(pk_field):
        return _extract_api_id(raw_id)
    return str(raw_id)


def _build_model_defaults(
    model: Type[models.Model], item: Mapping[str, Any], depth: int = 0
) -> Dict[str, Any]:
    """Build a defaults dict for update_or_create from an API item.

    This function attempts to map every field from the API response to the model,
    automatically handling type conversions for date/time fields and resolving
    foreign keys using bounded recursion. Fields present in the API but not in
    the model are silently skipped.

    Args:
        model: Django model class to map the item onto.
        item: Parsed API item.
        depth: Current relation traversal depth to prevent deep recursion.

    Returns:
        A dict suitable for update_or_create(..., defaults=...).

    Raises:
        ScraperError: If required model fields are missing from the API data.

    Side Effects:
        May trigger database lookups and writes for related objects.
    """
    defaults: Dict[str, Any] = {}

    # Try to map every field from the API response
    for key, value in item.items():
        # Skip JSON-LD metadata fields
        if key.startswith("@") or key in JSON_LD_METADATA_FIELDS:
            continue

        if value is None:
            continue

        # Try to find the corresponding model field
        # First try snake_case (direct match)
        try:
            field = model._meta.get_field(key)
        except FieldDoesNotExist:
            # Try converting from camelCase to snake_case
            snake_key = _camel_to_snake_case(key)
            try:
                field = model._meta.get_field(snake_key)
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
        converted_value = _convert_field_value(field, value, depth)
        if converted_value is not None:
            if field.is_relation and field.many_to_one:
                defaults[f"{field.name}_id"] = converted_value
            else:
                defaults[field.name] = converted_value

    # Validate that all required fields are present
    missing = _missing_required_fields(model, defaults)
    if missing:
        raise ScraperError(f"Missing required fields for {model.__name__}: {', '.join(missing)}")

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
        if _is_integer_field(pk_field):
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


def sync_viernulvier(
    model: Type[models.Model],
    endpoint: str = DEFAULT_ENDPOINT,
    params: Optional[Dict[str, str]] = None,
) -> int:
    """Fetch and persist Viernulvier data into a Django model.

    Items are fetched via `fetch_viernulvier`, validated, and then persisted
    with per-item savepoints to isolate errors without aborting the batch.

    An ImportLog entry is created to track the import operation.

    Args:
        model: Django model class receiving the API data.
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

        # Update import log with final status
        import_log.records_total = len(items)
        import_log.records_imported = saved
        import_log.records_failed = errors
        import_log.finished_at = timezone.now()

        if errors == 0:
            import_log.status = ImportLog.Status.SUCCESS
        elif saved > 0:
            import_log.status = ImportLog.Status.PARTIAL_SUCCESS
        else:
            import_log.status = ImportLog.Status.FAILED
            import_log.error_message = f"All {errors} records failed to import"

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
