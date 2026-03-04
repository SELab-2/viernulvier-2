"""Viernulvier / Peppered scraper module.

Usage:
    from apps.imports.scrapers.viernulvier import sync_viernulvier, ModelSyncConfig
    sync_viernulvier(MyModel, config, endpoint="/productions")
"""

import logging
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Type
from urllib.parse import urljoin, urlparse

import requests
from django.core.exceptions import FieldDoesNotExist, FieldError, ValidationError
from django.db import DatabaseError, IntegrityError, transaction, models
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://www.viernulvier.gent/api/v1"
BASE_DOMAIN = "https://www.viernulvier.gent"
DEFAULT_ENDPOINT = "/productions"
DEFAULT_TIMEOUT = 10
ERROR_CONTEXT_PATH = "/api/contexts/Error"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ScraperError(Exception):
    """Raised when the scraper cannot fetch or normalize Viernulvier data."""


# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TranslationConfig:
    """Configuration for syncing translations to a separate model.

    The Peppered API ALWAYS returns translations as a flat dict:
        "title": {"nl": "De titel", "en": "The title", "fr": "Le titre"}

    Each translated field has its own flat dict on the parent object.
    Each TranslationConfig processes one such field. Multiple TranslationConfigs
    for the same model are merged per language code via update_or_create.

    Args:
        api_key:      Key in the parent API item (e.g. "title", "description").
        model:        Django model for the translations.
        parent_fk:    FK field name to the parent model on the translation model.
        flat_field:   Field name on the translation model to populate.
        language_fk:  Field name for the language code on the translation model.
                      Use "language_id" when Language has a string PK.
        value_transforms: Optional callables per model field name.

    Example:
        TranslationConfig(
            api_key="title",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="title",
            language_fk="language_id",
        )
    """
    api_key: str
    model: Type[models.Model]
    parent_fk: str
    flat_field: str
    language_fk: str = "language_id"
    value_transforms: Dict[str, Callable[[Any], Any]] = field(default_factory=dict)


@dataclass
class M2MConfig:
    """Configuration for M2M relations via a through table.

    The API returns M2M relations as a list of URLs:
        "genres": ["https://example.com/api/v1/genres/1", ...]

    Args:
        api_key:              Key in the parent API item (e.g. "genres").
        related_model:        The related Django model.
        through_model:        The through table.
        parent_fk:            FK to the parent model in the through table.
        related_fk:           FK to the related model in the through table.
        related_lookup_field: Field used to look up the related model.
        extra_fields:         Extra fields on the through table: {api_field: model_field}.
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
        field_map:        API field name -> model field name.
                          Set to None to explicitly skip a field.
        value_transforms: Callables per model field name for value transformation.
                          E.g. {"is_own_location": nee_ja_to_bool}
        fk_resolvers:     Custom FK resolution per model field name when the
                          default external_id lookup does not work.
                          Callable(raw_value) -> pk | None
                          E.g. {"use_as": lambda v: GenreUseAs.objects.get_or_create(name=v)[0].pk}
        translations:     List of TranslationConfig for flat-dict translations.
        m2m:              List of M2MConfig for M2M relations.
        lookup_field:     Field for update_or_create lookup (default "external_id").
        api_id_key:       Key for the primary identifier in the API object (default "@id").
    """
    field_map: Dict[str, Optional[str]] = field(default_factory=dict)
    value_transforms: Dict[str, Callable[[Any], Any]] = field(default_factory=dict)
    fk_resolvers: Dict[str, Callable[[Any], Optional[Any]]] = field(default_factory=dict)
    translations: List[TranslationConfig] = field(default_factory=list)
    m2m: List[M2MConfig] = field(default_factory=list)
    lookup_field: str = "external_id"
    api_id_key: str = "@id"


# ---------------------------------------------------------------------------
# HTTP fetch layer
# ---------------------------------------------------------------------------

def _get_api_key_or_raise() -> str:
    api_key = os.getenv("VIERNULVIER_API_KEY")
    if not api_key:
        raise ScraperError("VIERNULVIER_API_KEY is not set")
    return api_key


def _build_request_headers() -> Dict[str, str]:
    return {
        "X-AUTH-TOKEN": _get_api_key_or_raise(),
        "accept": "application/ld+json",
    }


def _fetch_single_page(url: str, params: Optional[Dict[str, str]] = None) -> Any:
    logger.debug("Fetching page: %s", url)
    try:
        response = requests.get(
            url,
            headers=_build_request_headers(),
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ScraperError("Request to Viernulvier API failed") from exc

    if not response.ok:
        raise ScraperError(f"Viernulvier API error: {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise ScraperError("Invalid JSON from Viernulvier API") from exc

    if data is None:
        raise ScraperError("Unexpected Viernulvier API payload: null")

    if isinstance(data, dict) and data.get("@context") == ERROR_CONTEXT_PATH:
        status = data.get("status", "unknown")
        detail = data.get("detail", "no detail provided")
        raise ScraperError(f"Viernulvier API error: status={status}, detail={detail}")

    return data


def fetch_viernulvier(
    endpoint: str = DEFAULT_ENDPOINT,
    params: Optional[Dict[str, str]] = None,
) -> List[Any]:
    """Fetch all items from an endpoint (follows pagination automatically).

    Args:
        endpoint: Relative API path (e.g. "/productions").
        params:   Optional query parameters (e.g. {"created_at[after]": "2024-01-01"}).

    Returns:
        List of all items across all pages.
    """
    parsed = urlparse(endpoint)
    if parsed.scheme or parsed.netloc:
        raise ScraperError(f"endpoint must be a relative path, got: {endpoint!r}")

    url = urljoin(BASE_URL + "/", endpoint.lstrip("/"))
    all_items: List[Any] = []
    current_url: Optional[str] = url
    first_page = True

    while current_url:
        data = _fetch_single_page(current_url, params=params if first_page else None)
        first_page = False

        if isinstance(data, dict):
            if "member" in data:
                all_items.extend(data["member"])
            elif "@context" in data:
                # Single-item response
                all_items.append(data)
            else:
                raise ScraperError("Unexpected payload shape: dict without 'member' or '@context'")

            view = data.get("view")
            if isinstance(view, dict) and "next" in view:
                next_url = view["next"]
                current_url = (
                    next_url if next_url.startswith("http")
                    else urljoin(BASE_DOMAIN, next_url)
                )
            else:
                current_url = None

        elif isinstance(data, list):
            all_items.extend(data)
            current_url = None
        else:
            raise ScraperError(f"Unexpected payload type: {type(data)}")

    return all_items


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _camel_to_snake(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def _parse_field_value(model_field: models.Field, value: Any) -> Any:
    """Convert an API value to the correct Python type for a model field."""
    if value is None:
        return None
    if isinstance(model_field, models.DateTimeField) and isinstance(value, str):
        # Repair invalid date strings
        if value.startswith("-"):
            value = value[1:]
        if value[:4] == "0000":
            value = "1970" + value[4:]
        return parse_datetime(value)
    if isinstance(model_field, models.DateField) and isinstance(value, str):
        return parse_date(value)
    return value


def _extract_external_id_from_url(raw: Any) -> Optional[str]:
    """Extract an external ID from a URL string or dict with '@id'.

    The API sends FK values as URL strings:
        "hall": "https://www.viernulvier.gent/api/v1/halls/42"
    or as an embedded object:
        "production": {"@id": "/api/v1/productions/5", ...}
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


def _resolve_fk(model_field: models.Field, raw_value: Any) -> Optional[Any]:
    """Resolve an FK value to a primary key via external_id lookup."""
    related_model = model_field.remote_field.model
    ext_id = _extract_external_id_from_url(raw_value)
    if ext_id is None:
        return None
    try:
        return related_model.objects.values_list("pk", flat=True).get(external_id=ext_id)
    except related_model.DoesNotExist:
        logger.warning(
            "FK not found: %s.external_id=%r — sync related models first.",
            related_model.__name__, ext_id,
        )
        return None
    except Exception:
        logger.exception("Error resolving FK %s external_id=%r", related_model.__name__, ext_id)
        return None


# ---------------------------------------------------------------------------
# Build defaults: API item → Django model defaults dict
# ---------------------------------------------------------------------------

def _build_defaults(
    model: Type[models.Model],
    item: Mapping[str, Any],
    config: ModelSyncConfig,
) -> Dict[str, Any]:
    """Convert an API item to a defaults dict suitable for update_or_create.

    Step 1: Explicit field_map from config (highest priority).
    Step 2: Automatic camelCase→snake_case mapping as fallback.

    Flat-dict fields (translations) and lists (M2M) are NOT processed here —
    those are handled by _sync_translations and _sync_m2m.
    """
    defaults: Dict[str, Any] = {}
    explicitly_mapped = set(config.field_map.keys())

    # ---- Step 1: Explicit field_map ----
    for api_key, model_field_name in config.field_map.items():
        if model_field_name is None:
            continue
        raw_value = item.get(api_key)
        if raw_value is None:
            continue

        try:
            model_field = model._meta.get_field(model_field_name)
        except FieldDoesNotExist:
            logger.warning("Field '%s' doesn't exist in %s", model_field_name, model.__name__)
            continue

        if not isinstance(model_field, models.Field) or model_field.primary_key:
            continue

        # Flat dict = translation, handled by _sync_translations, skip here
        if isinstance(raw_value, dict) and not model_field.is_relation:
            continue

        if model_field.is_relation and model_field.many_to_one:
            custom_resolver = config.fk_resolvers.get(model_field_name)
            pk = custom_resolver(raw_value) if custom_resolver else _resolve_fk(model_field, raw_value)
            if pk is not None:
                defaults[f"{model_field.name}_id"] = pk
        else:
            converted = _parse_field_value(model_field, raw_value)
            transform = config.value_transforms.get(model_field_name)
            if transform:
                converted = transform(converted)
            if converted is not None:
                defaults[model_field.name] = converted

    # ---- Step 2: Auto-mapping for fields not explicitly mapped ----
    for api_key, raw_value in item.items():
        if api_key in explicitly_mapped:
            continue
        if api_key.startswith("@") or raw_value is None:
            continue
        # Lists = M2M, flat dicts = translations — skip both here
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
            logger.debug("Auto-mapping: '%s' not found in %s", api_key, model.__name__)
            continue

        if model_field.is_relation and model_field.many_to_one:
            pk = _resolve_fk(model_field, raw_value)
            if pk is not None:
                defaults[f"{model_field.name}_id"] = pk
        else:
            converted = _parse_field_value(model_field, raw_value)
            transform = config.value_transforms.get(model_field.name)
            if transform:
                converted = transform(converted)
            if converted is not None:
                defaults[model_field.name] = converted

    return defaults


def _extract_lookup_value(item: Mapping[str, Any], config: ModelSyncConfig) -> Optional[str]:
    """Extract the lookup value for update_or_create."""
    raw = item.get(config.api_id_key) or item.get("external_id") or item.get("id")
    if raw is None:
        return None
    if isinstance(raw, dict):
        raw = raw.get("@id") or raw.get("external_id") or raw.get("id")
    return str(raw).strip() if raw is not None else None


# ---------------------------------------------------------------------------
# Translation sync — flat dict format
# ---------------------------------------------------------------------------

def _sync_translations(
    parent_obj: models.Model,
    item: Mapping[str, Any],
    translation_config: TranslationConfig,
) -> None:
    """Sync one flat-dict field to a translation model.

    The Peppered API returns translations as:
        "title": {"nl": "De titel", "en": "The title"}

    For each language code in the dict, we run update_or_create on the
    translation model with the single field managed by this TranslationConfig.
    Multiple TranslationConfigs for the same model then fill all fields
    together per language code.
    """
    raw_dict = item.get(translation_config.api_key)
    if not isinstance(raw_dict, dict):
        return

    model = translation_config.model
    parent_fk = translation_config.parent_fk
    language_fk = translation_config.language_fk
    target_field = translation_config.flat_field

    try:
        model_field = model._meta.get_field(target_field)
    except FieldDoesNotExist:
        logger.warning("Translation veld '%s' niet gevonden op %s", target_field, model.__name__)
        return

    for lang_code, raw_value in raw_dict.items():
        if not lang_code or raw_value is None:
            continue

        transform = translation_config.value_transforms.get(target_field)
        converted = _parse_field_value(model_field, raw_value)
        if transform:
            converted = transform(converted)
        if converted is None:
            continue

        try:
            model.objects.update_or_create(
                **{parent_fk: parent_obj, language_fk: lang_code},
                defaults={target_field: converted},
            )
        except Exception:
            logger.exception(
                "Fout bij translation %s.%s pk=%s taal=%s",
                model.__name__, target_field, parent_obj.pk, lang_code,
            )


# ---------------------------------------------------------------------------
# M2M sync
# ---------------------------------------------------------------------------

def _sync_m2m(
    parent_obj: models.Model,
    item: Mapping[str, Any],
    m2m_config: M2MConfig,
) -> None:
    """Sync an M2M relation via a through table.

    The API returns M2M data as a list of URL strings:
        "genres": ["https://.../genres/1", "https://.../genres/3"]

    Existing through-table rows for this parent object are deleted
    and recreated based on the current API data.
    """
    raw_list = item.get(m2m_config.api_key)
    if not isinstance(raw_list, list):
        return

    through_model = m2m_config.through_model
    related_model = m2m_config.related_model

    # Delete existing relations for this parent
    through_model.objects.filter(**{m2m_config.parent_fk: parent_obj}).delete()

    for position, raw_item in enumerate(raw_list):
        ext_id = _extract_external_id_from_url(raw_item)
        if not ext_id:
            continue

        try:
            related_obj = related_model.objects.get(
                **{m2m_config.related_lookup_field: ext_id}
            )
        except related_model.DoesNotExist:
            logger.warning(
                "%s met %s=%r niet gevonden — sync gerelateerde modellen eerst.",
                related_model.__name__, m2m_config.related_lookup_field, ext_id,
            )
            continue

        through_kwargs: Dict[str, Any] = {
            m2m_config.parent_fk: parent_obj,
            m2m_config.related_fk: related_obj,
        }

        # Extra fields on the through table (e.g. position)
        for api_field, through_field in m2m_config.extra_fields.items():
            value = raw_item.get(api_field) if isinstance(raw_item, dict) else None
            if value is None and api_field == "position":
                value = position
            if value is not None:
                through_kwargs[through_field] = value

        try:
            through_model.objects.create(**through_kwargs)
        except Exception:
            logger.exception(
                "Fout bij aanmaken %s voor %s pk=%s",
                through_model.__name__, parent_obj.__class__.__name__, parent_obj.pk,
            )


# ---------------------------------------------------------------------------
# Main sync function
# ---------------------------------------------------------------------------

def sync_viernulvier(
    model: Type[models.Model],
    config: ModelSyncConfig,
    endpoint: str = DEFAULT_ENDPOINT,
    params: Optional[Dict[str, str]] = None,
) -> int:
    """Fetch Viernulvier data and store it in a Django model.

    A savepoint is used per item so that an error in one item
    does not break the rest of the batch.

    Args:
        model:    Django model class.
        config:   ModelSyncConfig with field mapping, translations and M2M.
        endpoint: Relative API path (e.g. "/productions").
        params:   Optional query parameters.

    Returns:
        Number of saved records (created or updated).
    """
    from apps.import_log.models import ImportLog

    source = f"viernulvier:{endpoint}"
    if params:
        params_str = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
        source = f"{source}?{params_str}"

    import_log = ImportLog.objects.create(
        source=source,
        status=ImportLog.Status.IN_PROGRESS,
        started_at=timezone.now(),
    )

    try:
        items = fetch_viernulvier(endpoint=endpoint, params=params)
    except Exception as exc:
        import_log.status = ImportLog.Status.FAILED
        import_log.finished_at = timezone.now()
        import_log.error_message = str(exc)
        import_log.save()
        raise

    saved = 0
    errors = 0
    error_messages: List[str] = []
    seen: set = set()

    for item in items:
        if not isinstance(item, dict):
            msg = f"Item is not a dict: {item!r}"
            logger.error(msg)
            errors += 1
            error_messages.append(msg)
            continue

        lookup_value = _extract_lookup_value(item, config)
        if lookup_value is None:
            msg = f"Missing '{config.api_id_key}' for item: {str(item)[:200]}"
            logger.warning(msg)
            errors += 1
            error_messages.append(msg)
            continue

        if lookup_value in seen:
            logger.warning("Duplicate in batch skipped: %s", lookup_value)
            continue
        seen.add(lookup_value)

        sid = transaction.savepoint()
        try:
            defaults = _build_defaults(model, item, config)
            obj, created = model.objects.update_or_create(
                **{config.lookup_field: lookup_value},
                defaults=defaults,
            )

            for trans_cfg in config.translations:
                _sync_translations(obj, item, trans_cfg)

            for m2m_cfg in config.m2m:
                _sync_m2m(obj, item, m2m_cfg)

            transaction.savepoint_commit(sid)
            saved += 1
            logger.debug("%s %s: %s", "Created" if created else "Updated", model.__name__, lookup_value)

        except ValidationError as e:
            transaction.savepoint_rollback(sid)
            msgs = [
                f"{f}: {err}" if f != "__all__" else err
                for f, errs in e.message_dict.items()
                for err in errs
            ]
            msg = f"Validation error for {lookup_value}: {'; '.join(msgs)}"
            logger.error(msg)
            errors += 1
            error_messages.append(msg)

        except (IntegrityError, DatabaseError, FieldError):
            transaction.savepoint_rollback(sid)
            exc_type, exc_value, _ = sys.exc_info()
            msg = f"Database error for {lookup_value}: {exc_type.__name__}: {exc_value}"
            logger.error(msg, exc_info=True)
            errors += 1
            error_messages.append(msg)

        except Exception:
            transaction.savepoint_rollback(sid)
            exc_type, exc_value, _ = sys.exc_info()
            msg = f"Unexpected error for {lookup_value}: {exc_type.__name__}: {exc_value}"
            logger.error(msg, exc_info=True)
            errors += 1
            error_messages.append(msg)

    import_log.records_total = len(items)
    import_log.records_imported = saved
    import_log.records_failed = errors
    import_log.finished_at = timezone.now()

    if errors == 0:
        import_log.status = ImportLog.Status.SUCCESS
    elif saved > 0:
        import_log.status = ImportLog.Status.PARTIAL_SUCCESS
        import_log.error_message = f"{errors} records failed: {', '.join(error_messages)}"
    else:
        import_log.status = ImportLog.Status.FAILED
        import_log.error_message = f"All {errors} records failed: {', '.join(error_messages)}"

    import_log.save()
    logger.info("Sync finished: saved=%s, errors=%s", saved, errors)
    return saved
