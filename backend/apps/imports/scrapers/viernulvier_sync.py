"""Core model synchronization loop for Viernulvier data."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

from django.core.exceptions import FieldError, ValidationError
from django.db import DatabaseError, IntegrityError

from apps.import_log.models import ImportLog

from .viernulvier_constants import DEFAULT_ENDPOINT, MAX_ERROR_MESSAGES

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from django.db import models

    from .viernulvier_constants import ModelSyncConfig

logger = logging.getLogger("apps.imports.scrapers.viernulvier")


def _build_import_source(endpoint: str, params: dict[str, str] | None) -> str:
    source = f"viernulvier:{endpoint}"
    if not params:
        return source
    params_str = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
    suffix = f"?{params_str}"
    return source[: 200 - len(suffix)] + suffix


def _record_error(error_messages: list[str], message: str) -> None:
    if len(error_messages) < MAX_ERROR_MESSAGES:
        error_messages.append(message)


def _validate_item(
    item: Any,
    config: ModelSyncConfig,
    extract_lookup_value_fn: Callable[[Mapping[str, Any], ModelSyncConfig], str | None],
    seen: set[str],
) -> tuple[dict[str, Any] | None, str | None, str | None]:
    if not isinstance(item, dict):
        msg = f"Item is not a dict: {item!r}"
        logger.error(msg)
        return None, None, msg

    lookup_value = extract_lookup_value_fn(item, config)
    if config.item_filter and not config.item_filter(item):
        logger.debug("Item filtered out: %s", lookup_value)
        return None, None, None
    if lookup_value is None:
        msg = f"Missing '{config.api_id_key}' in item: {str(item)[:200]}"
        logger.warning(msg)
        return None, None, msg
    if lookup_value in seen:
        logger.warning("Duplicate item skipped: %s", lookup_value)
        return None, None, None
    seen.add(lookup_value)
    return item, lookup_value, None


def _sync_single_item(
    *,
    model: type[models.Model],
    config: ModelSyncConfig,
    item: Mapping[str, Any],
    lookup_value: str,
    fk_cache: Any,
    transaction_module: Any,
    build_defaults_fn: Callable[[type[models.Model], Mapping[str, Any], ModelSyncConfig, Any], dict[str, Any]],
    sync_translations_fn: Callable[[models.Model, Mapping[str, Any], list], None],
    sync_m2m_fn: Callable[[models.Model, Mapping[str, Any], Any, Any], None],
) -> tuple[bool, str | None]:
    sid = transaction_module.savepoint()
    try:
        defaults = build_defaults_fn(model, item, config, fk_cache)
        lookup_kwargs = {config.lookup_field: lookup_value}
        obj, created = model.objects.update_or_create(**lookup_kwargs, defaults=defaults)

        if hasattr(obj, "external_id"):
            fk_cache.set(model, str(obj.external_id), obj.pk)

        sync_translations_fn(obj, item, config.translations)
        for m2m_cfg in config.m2m:
            sync_m2m_fn(obj, item, m2m_cfg, fk_cache)

        transaction_module.savepoint_commit(sid)
        logger.debug("%s %s: %s", "Created" if created else "Updated", model.__name__, lookup_value)
        return True, None
    except ValidationError as exc:
        transaction_module.savepoint_rollback(sid)
        msgs = [f"{f}: {err}" if f != "__all__" else err for f, errs in exc.message_dict.items() for err in errs]
        msg = f"Validation error for {lookup_value}: {'; '.join(msgs)}"
        logger.exception("Validation error for %s: %s", lookup_value, "; ".join(msgs))
        return False, msg
    except (IntegrityError, DatabaseError, FieldError):
        transaction_module.savepoint_rollback(sid)
        exc_type, exc_value, _ = sys.exc_info()
        msg = f"Database error for {lookup_value}: {exc_type.__name__}: {exc_value}"
        logger.exception(msg)
        return False, msg
    except Exception:
        transaction_module.savepoint_rollback(sid)
        exc_type, exc_value, _ = sys.exc_info()
        msg = f"Unexpected error for {lookup_value}: {exc_type.__name__}: {exc_value}"
        logger.exception(msg)
        return False, msg


def _finish_import_log(
    import_log: ImportLog,
    *,
    total: int,
    saved: int,
    errors: int,
    error_messages: list[str],
    timezone_module: Any,
) -> None:
    truncation_note = f" (showing first {MAX_ERROR_MESSAGES} of {errors})" if errors > MAX_ERROR_MESSAGES else ""
    import_log.records_total = total
    import_log.records_imported = saved
    import_log.records_failed = errors
    import_log.finished_at = timezone_module.now()

    if errors == 0:
        import_log.status = ImportLog.Status.SUCCESS
    elif saved > 0:
        import_log.status = ImportLog.Status.PARTIAL_SUCCESS
        import_log.error_message = f"{errors} records failed{truncation_note}: {', '.join(error_messages)}"
    else:
        import_log.status = ImportLog.Status.FAILED
        import_log.error_message = f"All {errors} records failed{truncation_note}: {', '.join(error_messages)}"

    import_log.save()


def _process_items(
    *,
    items: list[Any],
    model: type[models.Model],
    config: ModelSyncConfig,
    extract_lookup_value_fn: Callable[[Mapping[str, Any], ModelSyncConfig], str | None],
    fk_cache: Any,
    dry_run: bool,
    build_defaults_fn: Callable[[type[models.Model], Mapping[str, Any], ModelSyncConfig, Any], dict[str, Any]],
    on_progress: Callable[[int, int], None] | None,
    transaction_module: Any,
    sync_translations_fn: Callable[[models.Model, Mapping[str, Any], list], None],
    sync_m2m_fn: Callable[[models.Model, Mapping[str, Any], Any, Any], None],
) -> tuple[int, int, list[str], int]:
    saved = 0
    errors = 0
    error_messages: list[str] = []
    seen: set[str] = set()
    total = len(items)

    for item in items:
        valid_item, lookup_value, validation_error = _validate_item(item, config, extract_lookup_value_fn, seen)
        if validation_error:
            errors += 1
            _record_error(error_messages, validation_error)
            continue
        if valid_item is None or lookup_value is None:
            continue

        if dry_run:
            defaults = build_defaults_fn(model, valid_item, config, fk_cache)
            logger.info("[DRY RUN] Would save %s (%d fields)", lookup_value, len(defaults))
            saved += 1
            if on_progress:
                on_progress(saved, total)
            continue

        ok, sync_error = _sync_single_item(
            model=model,
            config=config,
            item=valid_item,
            lookup_value=lookup_value,
            fk_cache=fk_cache,
            transaction_module=transaction_module,
            build_defaults_fn=build_defaults_fn,
            sync_translations_fn=sync_translations_fn,
            sync_m2m_fn=sync_m2m_fn,
        )
        if ok:
            saved += 1
            if on_progress:
                on_progress(saved, total)
            continue
        errors += 1
        if sync_error:
            _record_error(error_messages, sync_error)

    return saved, errors, error_messages, total


def sync_viernulvier_impl(
    model: type[models.Model],
    config: ModelSyncConfig,
    *,
    fetch_fn: Callable[..., list[Any]],
    build_defaults_fn: Callable[[type[models.Model], Mapping[str, Any], ModelSyncConfig, Any], dict[str, Any]],
    sync_translations_fn: Callable[[models.Model, Mapping[str, Any], list], None],
    sync_m2m_fn: Callable[[models.Model, Mapping[str, Any], Any, Any], None],
    extract_lookup_value_fn: Callable[[Mapping[str, Any], ModelSyncConfig], str | None],
    fk_cache_cls: Callable[[], Any],
    transaction_module: Any,
    timezone_module: Any,
    endpoint: str = DEFAULT_ENDPOINT,
    params: dict[str, str] | None = None,
    dry_run: bool = False,
    etag_cache: dict[str, str] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> int:
    """Fetch Viernulvier API data and persist it to a Django model."""
    source = _build_import_source(endpoint, params)

    import_log = ImportLog.objects.create(
        source=source,
        status=ImportLog.Status.IN_PROGRESS,
        started_at=timezone_module.now(),
    )

    try:
        items = fetch_fn(endpoint=endpoint, params=params, etag_cache=etag_cache)
    except Exception as exc:
        import_log.status = ImportLog.Status.FAILED
        import_log.finished_at = timezone_module.now()
        import_log.error_message = str(exc)
        import_log.save()
        raise

    if not items:
        import_log.status = ImportLog.Status.SUCCESS
        import_log.records_total = 0
        import_log.records_imported = 0
        import_log.records_failed = 0
        import_log.finished_at = timezone_module.now()
        import_log.save()
        return 0

    fk_cache = fk_cache_cls()
    for m2m_cfg in config.m2m:
        fk_cache.warmup(m2m_cfg.related_model)

    saved, errors, error_messages, total = _process_items(
        items=items,
        model=model,
        config=config,
        extract_lookup_value_fn=extract_lookup_value_fn,
        fk_cache=fk_cache,
        dry_run=dry_run,
        build_defaults_fn=build_defaults_fn,
        on_progress=on_progress,
        transaction_module=transaction_module,
        sync_translations_fn=sync_translations_fn,
        sync_m2m_fn=sync_m2m_fn,
    )

    _finish_import_log(
        import_log,
        total=total,
        saved=saved,
        errors=errors,
        error_messages=error_messages,
        timezone_module=timezone_module,
    )
    logger.info("Sync complete: saved=%d, errors=%d%s", saved, errors, " [DRY RUN]" if dry_run else "")
    return saved
