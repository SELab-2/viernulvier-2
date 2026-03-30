"""Compatibility facade for the Viernulvier scraper.

The implementation is split over focused modules in this package:
- `viernulvier_constants.py`
- `viernulvier_http.py`
- `viernulvier_normalize.py`
- `viernulvier_relations.py`
- `viernulvier_sync.py`
- `viernulvier_media.py`

This file intentionally keeps legacy symbol names and monkeypatch points
used by the test suite and management command integrations.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, Type

import requests
from django.db import models, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from . import viernulvier_constants as _constants
from . import viernulvier_http as _http
from . import viernulvier_media as _media
from . import viernulvier_normalize as _normalize
from . import viernulvier_relations as _relations
from . import viernulvier_sync as _sync
from .viernulvier_constants import M2MConfig, ModelSyncConfig, RateLimitError, ScraperError, TranslationConfig

BASE_DOMAIN = _constants.BASE_DOMAIN
BASE_URL = _constants.BASE_URL
DEFAULT_ENDPOINT = _constants.DEFAULT_ENDPOINT
DEFAULT_TIMEOUT = _constants.DEFAULT_TIMEOUT
ERROR_CONTEXT_PATH = _constants.ERROR_CONTEXT_PATH
MAX_CONCURRENT_PAGES = _constants.MAX_CONCURRENT_PAGES
MAX_ERROR_MESSAGES = _constants.MAX_ERROR_MESSAGES
MAX_RETRIES = _constants.MAX_RETRIES
RETRY_BACKOFF_BASE = _constants.RETRY_BACKOFF_BASE
RETRY_BACKOFF_MAX = _constants.RETRY_BACKOFF_MAX
RETRY_STATUS_CODES = _constants.RETRY_STATUS_CODES
USER_AGENT_POOL = _constants.USER_AGENT_POOL

logger = logging.getLogger(__name__)

__all__ = [
    "ModelSyncConfig",
    "TranslationConfig",
    "M2MConfig",
    "FKCache",
    "ScraperError",
    "RateLimitError",
    "fetch_viernulvier",
    "sync_viernulvier",
    "sync_media_item_gallery_links",
    "sync_media_item_crops",
    "normalize_url",
    "normalize_performer_type",
    "nee_ja_to_bool",
    "clean_string",
]


FKCache = _relations.FKCache

normalize_url = _normalize.normalize_url
normalize_performer_type = _normalize.normalize_performer_type
clean_string = _normalize.clean_string
clean_vendor_id = _normalize.clean_vendor_id
nee_ja_to_bool = _normalize.nee_ja_to_bool


def _get_api_key_or_raise() -> str:
    return _http.get_api_key_or_raise()


def _build_session() -> requests.Session:
    return _http.build_session()


def _backoff_seconds(attempt: int) -> float:
    return _http.backoff_seconds(attempt, backoff_base=RETRY_BACKOFF_BASE, backoff_max=RETRY_BACKOFF_MAX)


def _parse_retry_after(response: requests.Response) -> Optional[int]:
    return _http.parse_retry_after(response)


def _fetch_with_retry(
    session: requests.Session,
    url: str,
    params: Optional[Dict[str, str]] = None,
    etag: Optional[str] = None,
) -> Tuple[Optional[Any], Optional[str]]:
    return _http.fetch_with_retry(
        session,
        url,
        params=params,
        etag=etag,
        max_retries=MAX_RETRIES,
        timeout=DEFAULT_TIMEOUT,
        retry_status_codes=RETRY_STATUS_CODES,
        sleep_fn=time.sleep,
        backoff_fn=_backoff_seconds,
        parse_retry_after_fn=_parse_retry_after,
    )


def _discover_extra_pages(data: dict) -> List[str]:
    return _http.discover_extra_pages(data, base_domain=BASE_DOMAIN)


def fetch_viernulvier(
    endpoint: str = DEFAULT_ENDPOINT,
    params: Optional[Dict[str, str]] = None,
    etag_cache: Optional[Dict[str, str]] = None,
) -> List[Any]:
    return _http.fetch_viernulvier_impl(
        endpoint=endpoint,
        params=params,
        etag_cache=etag_cache,
        base_url=BASE_URL,
        base_domain=BASE_DOMAIN,
        build_session_fn=_build_session,
        fetch_with_retry_fn=_fetch_with_retry,
        discover_extra_pages_fn=_discover_extra_pages,
    )


def _parse_field_value(model_field: models.Field, value: Any) -> Any:
    return _normalize.parse_field_value(model_field, value)


def _extract_external_id_from_url(raw: Any) -> Optional[str]:
    return _relations.extract_external_id_from_url(raw)


def _resolve_fk(model_field: models.Field, raw_value: Any, fk_cache: FKCache) -> Optional[Any]:
    return _relations.resolve_fk(model_field, raw_value, fk_cache)


def _extract_lookup_value(item: Mapping[str, Any], config: ModelSyncConfig) -> Optional[str]:
    return _relations.extract_lookup_value(item, config)


def _build_defaults(
    model: Type[models.Model],
    item: Mapping[str, Any],
    config: ModelSyncConfig,
    fk_cache: FKCache,
) -> Dict[str, Any]:
    return _relations.build_defaults(model, item, config, fk_cache, resolve_fk_fn=_resolve_fk)


def _sync_all_translations(
    parent_obj: models.Model,
    item: Mapping[str, Any],
    translation_configs: List[TranslationConfig],
) -> None:
    _relations.sync_all_translations(parent_obj, item, translation_configs)


def _sync_m2m(parent_obj: models.Model, item: Mapping[str, Any], m2m_config: M2MConfig, fk_cache: FKCache) -> None:
    _relations.sync_m2m(parent_obj, item, m2m_config, fk_cache)


def sync_viernulvier(
    model: Type[models.Model],
    config: ModelSyncConfig,
    endpoint: str = DEFAULT_ENDPOINT,
    params: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    etag_cache: Optional[Dict[str, str]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> int:
    return _sync.sync_viernulvier_impl(
        model,
        config,
        fetch_fn=fetch_viernulvier,
        build_defaults_fn=_build_defaults,
        sync_translations_fn=_sync_all_translations,
        sync_m2m_fn=_sync_m2m,
        extract_lookup_value_fn=_extract_lookup_value,
        fk_cache_cls=FKCache,
        transaction_module=transaction,
        timezone_module=timezone,
        endpoint=endpoint,
        params=params,
        dry_run=dry_run,
        etag_cache=etag_cache,
        on_progress=on_progress,
    )


def _derive_crop_filename(crop_name: str, item_external_id: str, image_url: str) -> str:
    return _media.derive_crop_filename(crop_name, item_external_id, image_url)


def _download_image(session: requests.Session, url: str) -> Optional[bytes]:
    return _media.download_image(
        session,
        url,
        max_retries=MAX_RETRIES,
        sleep_fn=time.sleep,
        backoff_fn=_backoff_seconds,
    )


def sync_media_item_gallery_links(
    dry_run: bool = False,
    etag_cache: Optional[Dict[str, str]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
    params: Optional[Dict[str, str]] = None,
) -> int:
    return _media.sync_media_item_gallery_links_impl(
        fetch_fn=fetch_viernulvier,
        extract_external_id_fn=_extract_external_id_from_url,
        timezone_module=timezone,
        dry_run=dry_run,
        etag_cache=etag_cache,
        on_progress=on_progress,
        params=params,
    )


def sync_media_item_crops(
    dry_run: bool = False,
    on_progress: Optional[Callable[[int, int], None]] = None,
    params: Optional[Dict[str, str]] = None,
) -> int:
    return _media.sync_media_item_crops_impl(
        fetch_fn=fetch_viernulvier,
        build_session_fn=_build_session,
        fetch_with_retry_fn=_fetch_with_retry,
        download_image_fn=_download_image,
        derive_crop_filename_fn=_derive_crop_filename,
        extract_external_id_fn=_extract_external_id_from_url,
        parse_datetime_fn=parse_datetime,
        timezone_module=timezone,
        dry_run=dry_run,
        on_progress=on_progress,
        params=params,
    )
