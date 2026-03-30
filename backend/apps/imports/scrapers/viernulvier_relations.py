"""FK resolution, defaults building, translations, and M2M sync helpers."""

from __future__ import annotations

from collections import defaultdict
import logging
from typing import TYPE_CHECKING, Any

from django.core.exceptions import FieldDoesNotExist
from django.db import models

from .viernulvier_normalize import camel_to_snake, parse_field_value

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from .viernulvier_constants import M2MConfig, ModelSyncConfig, TranslationConfig

logger = logging.getLogger("apps.imports.scrapers.viernulvier")


class FKCache:
    """In-memory cache of (model, external_id) -> pk."""

    def __init__(self) -> None:
        self._cache: dict[tuple[type[models.Model], str], Any] = {}
        self._loaded: dict[type[models.Model], bool] = {}

    def warmup(self, model: type[models.Model]) -> None:
        """Populate cache entries for one related model if not loaded yet."""
        if model in self._loaded:
            return
        try:
            count = 0
            for ext_id, pk in model.objects.values_list("external_id", "pk").iterator():
                self._cache[(model, str(ext_id))] = pk
                count += 1
            self._loaded[model] = True
            logger.debug("FK cache warmed: %s (%d entries)", model.__name__, count)
        except Exception:
            self._loaded[model] = False
            logger.warning("FK cache warmup failed for %s (no external_id field?)", model.__name__, exc_info=True)

    def get(self, model: type[models.Model], ext_id: str) -> Any | None:
        """Return a cached PK for a model/external-id pair, warming cache on demand."""
        self.warmup(model)
        return self._cache.get((model, str(ext_id)))

    def set(self, model: type[models.Model], ext_id: str, pk: Any) -> None:
        """Store a model/external-id to PK mapping in the local cache."""
        self._cache[(model, str(ext_id))] = pk


def extract_external_id_from_url(raw: Any) -> str | None:
    """Extract an external ID string from a URL, embedded dict, or integer."""
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


def resolve_fk(
    model_field: models.Field,
    raw_value: Any,
    fk_cache: FKCache,
) -> Any | None:
    """Resolve a FK raw value (URL or embedded dict) to a database primary key."""
    related_model = model_field.remote_field.model
    ext_id = extract_external_id_from_url(raw_value)
    if ext_id is None:
        return None

    pk = fk_cache.get(related_model, ext_id)
    if pk is not None:
        return pk

    try:
        pk = related_model.objects.values_list("pk", flat=True).get(external_id=ext_id)
        fk_cache.set(related_model, ext_id, pk)
        return pk
    except related_model.DoesNotExist:
        logger.warning("FK not found: %s.external_id=%r - sync related models first.", related_model.__name__, ext_id)
        return None
    except Exception:
        logger.exception("Error resolving FK %s external_id=%r", related_model.__name__, ext_id)
        return None


def extract_lookup_value(item: Mapping[str, Any], config: ModelSyncConfig) -> str | None:
    """Extract the primary lookup value (usually the API @id) from an item."""
    raw = item.get(config.api_id_key) or item.get("external_id") or item.get("id")
    if raw is None:
        return None
    if isinstance(raw, dict):
        raw = raw.get("@id") or raw.get("external_id") or raw.get("id")
    return str(raw).strip() if raw is not None else None


def build_defaults(  # noqa: C901, PLR0912
    model: type[models.Model],
    item: Mapping[str, Any],
    config: ModelSyncConfig,
    fk_cache: FKCache,
    resolve_fk_fn: Callable[[models.Field, Any, FKCache], Any | None],
) -> dict[str, Any]:
    """Convert an API item to defaults for update_or_create."""
    defaults: dict[str, Any] = {}
    explicitly_mapped = set(config.field_map.keys())

    def _apply(model_field: models.Field, raw_value: Any, field_name: str) -> None:
        if model_field.is_relation and model_field.many_to_one:
            custom = config.fk_resolvers.get(field_name)
            pk = custom(raw_value) if custom else resolve_fk_fn(model_field, raw_value, fk_cache)
            if pk is not None:
                defaults[f"{model_field.name}_id"] = pk
        else:
            converted = parse_field_value(model_field, raw_value)
            transform = config.value_transforms.get(field_name)
            if transform:
                converted = transform(converted)
            if converted is not None:
                defaults[model_field.name] = converted

    for api_key, model_field_name in config.field_map.items():
        if model_field_name is None:
            continue
        raw_value = item.get(api_key)
        if raw_value is None:
            continue
        try:
            model_field = model._meta.get_field(model_field_name)
        except FieldDoesNotExist:
            logger.warning("Field '%s' does not exist on %s", model_field_name, model.__name__)
            continue
        if not isinstance(model_field, models.Field) or model_field.primary_key:
            continue
        if isinstance(raw_value, dict) and not model_field.is_relation:
            continue
        _apply(model_field, raw_value, model_field_name)

    for api_key, raw_value in item.items():
        if api_key in explicitly_mapped or api_key.startswith("@") or raw_value is None:
            continue
        if isinstance(raw_value, (list, dict)):
            continue

        snake_key = camel_to_snake(api_key)
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
            continue
        _apply(model_field, raw_value, model_field.name)

    return defaults


def sync_all_translations(  # noqa: C901, PLR0912
    parent_obj: models.Model,
    item: Mapping[str, Any],
    translation_configs: list[TranslationConfig],
) -> None:
    """Sync all translated fields for one parent object in language batches."""
    if not translation_configs:
        return

    groups = defaultdict(list)
    for cfg in translation_configs:
        groups[(cfg.model, cfg.parent_fk, cfg.language_fk)].append(cfg)

    for (trans_model, parent_fk, language_fk), cfgs in groups.items():
        all_languages: set[str] = set()
        for cfg in cfgs:
            raw_dict = item.get(cfg.api_key)
            if isinstance(raw_dict, dict):
                all_languages.update(raw_dict.keys())

        for lang_code in all_languages:
            if not lang_code:
                continue

            field_updates: dict[str, Any] = {}

            for cfg in cfgs:
                raw_dict = item.get(cfg.api_key)
                if not isinstance(raw_dict, dict):
                    continue
                raw_value = raw_dict.get(lang_code)
                if raw_value is None:
                    continue

                try:
                    model_field = trans_model._meta.get_field(cfg.flat_field)
                except FieldDoesNotExist:
                    logger.warning("Translation field '%s' not found on %s", cfg.flat_field, trans_model.__name__)
                    continue

                if raw_value == "" and not getattr(model_field, "blank", True):
                    continue

                converted = parse_field_value(model_field, raw_value)
                transform = cfg.value_transforms.get(cfg.flat_field)
                if transform:
                    converted = transform(converted)
                if converted is not None:
                    field_updates[cfg.flat_field] = converted

            if not field_updates:
                continue

            try:
                trans_model.objects.update_or_create(
                    **{parent_fk: parent_obj, language_fk: lang_code},
                    defaults=field_updates,
                )
            except Exception:
                logger.exception(
                    "Error syncing %s translations for %s pk=%s lang=%s fields=%s",
                    trans_model.__name__,
                    parent_obj.__class__.__name__,
                    parent_obj.pk,
                    lang_code,
                    list(field_updates.keys()),
                )


def sync_m2m(  # noqa: C901
    parent_obj: models.Model,
    item: Mapping[str, Any],
    m2m_config: M2MConfig,
    fk_cache: FKCache,
) -> None:
    """Sync one M2M relation via through table using bulk_create."""
    raw_list = item.get(m2m_config.api_key)
    if not isinstance(raw_list, list):
        return

    through_model = m2m_config.through_model
    related_model = m2m_config.related_model

    fk_cache.warmup(related_model)
    through_model.objects.filter(**{m2m_config.parent_fk: parent_obj}).delete()

    to_create = []
    for position, raw_item in enumerate(raw_list):
        ext_id = extract_external_id_from_url(raw_item)
        if not ext_id:
            continue

        pk = fk_cache.get(related_model, ext_id)
        if pk is None:
            try:
                obj = related_model.objects.get(**{m2m_config.related_lookup_field: ext_id})
                fk_cache.set(related_model, ext_id, obj.pk)
                pk = obj.pk
            except related_model.DoesNotExist:
                logger.warning(
                    "%s with %s=%r not found - sync related models first.",
                    related_model.__name__,
                    m2m_config.related_lookup_field,
                    ext_id,
                )
                continue

        through_kwargs: dict[str, Any] = {
            m2m_config.parent_fk: parent_obj,
            m2m_config.related_fk: related_model(pk=pk),
        }
        for api_field, through_field in m2m_config.extra_fields.items():
            val = raw_item.get(api_field) if isinstance(raw_item, dict) else None
            if val is None and api_field == "position":
                val = position
            if val is not None:
                through_kwargs[through_field] = val

        to_create.append(through_model(**through_kwargs))

    if not to_create:
        return

    try:
        through_model.objects.bulk_create(to_create, ignore_conflicts=True)
    except Exception:
        logger.warning("bulk_create failed for %s - falling back to individual saves", through_model.__name__)
        for obj in to_create:
            try:
                obj.save()
            except Exception:
                logger.exception(
                    "Error creating %s for %s pk=%s",
                    through_model.__name__,
                    parent_obj.__class__.__name__,
                    parent_obj.pk,
                )
