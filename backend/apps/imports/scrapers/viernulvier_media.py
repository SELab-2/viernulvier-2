"""Media gallery-link and crop synchronization helpers."""

from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urljoin

from django.core.exceptions import FieldDoesNotExist
from django.core.files.base import ContentFile
from django.db import transaction
import requests

from apps.import_log.models import ImportLog
from apps.media_library import models as media_models
from apps.media_library.models import MediaGallery, MediaGalleryItem, MediaItem

from .viernulvier_constants import BASE_DOMAIN, MAX_ERROR_MESSAGES, MAX_RETRIES

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db import models

logger = logging.getLogger("apps.imports.scrapers.viernulvier")


def derive_crop_filename(crop_name: str, item_external_id: str, image_url: str) -> str:
    """Build a deterministic local filename for a crop image."""
    slug = item_external_id.strip("/").replace("/", "_")
    path_part = image_url.split("?", maxsplit=1)[0]
    last_segment = path_part.split("/")[-1]
    if "." in last_segment:
        ext = "." + last_segment.rsplit(".", 1)[-1].lower()
        if len(ext) > 5 or not ext[1:].isalpha():
            ext = ".jpg"
    else:
        ext = ".jpg"
    return f"{slug}_{crop_name}{ext}"


def download_image(
    session: requests.Session,
    url: str,
    *,
    max_retries: int = MAX_RETRIES,
    sleep_fn: Callable[[float], None] = time.sleep,
    backoff_fn: Callable[[int], float],
) -> bytes | None:
    """Download image bytes from a CDN URL with retry + backoff."""
    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, timeout=30, stream=True)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == max_retries:
                logger.exception("Image download failed after %d retries: %s", max_retries, url)
                return None
            wait = backoff_fn(attempt)
            logger.warning("Image download error - retry %d in %.1fs: %s", attempt + 1, wait, url)
            sleep_fn(wait)
            continue
        except requests.RequestException:
            logger.exception("Image download request error: %s", url)
            return None

        if response.status_code == 429:
            wait = float(response.headers.get("Retry-After", backoff_fn(attempt)))
            if attempt == max_retries:
                logger.error("Rate limited downloading image (gave up): %s", url)
                return None
            logger.warning("Rate limited downloading image - waiting %.1fs: %s", wait, url)
            sleep_fn(wait)
            continue

        if not response.ok:
            logger.error("HTTP %d downloading image: %s", response.status_code, url)
            return None

        return response.content

    return None


def _append_limited_error(errors: list[str], message: str) -> None:
    if len(errors) < MAX_ERROR_MESSAGES:
        errors.append(message)


def _finalize_empty_import(import_log: ImportLog, timezone_module: Any) -> int:
    import_log.status = ImportLog.Status.SUCCESS
    import_log.records_total = 0
    import_log.records_imported = 0
    import_log.records_failed = 0
    import_log.finished_at = timezone_module.now()
    import_log.save()
    return 0


def _handle_gallery_payload(
    *,
    galleries: list[Any],
    gallery_pk_by_external_id: dict[str, int],
    media_pk_by_external_id: dict[str, int],
    extract_external_id_fn: Callable[[Any], str | None],
    on_progress: Callable[[int, int], None] | None,
) -> tuple[list[MediaGalleryItem], dict[int, int], dict[int, int], set[int], int, list[str], int]:
    total = len(galleries)
    errors = 0
    error_messages: list[str] = []
    gallery_item_links: list[MediaGalleryItem] = []
    primary_item_to_gallery: dict[int, int] = {}
    primary_item_to_position: dict[int, int] = {}
    touched_gallery_ids: set[int] = set()

    for idx, gallery_item in enumerate(galleries, start=1):
        item_errors = _process_gallery_item(
            gallery_item=gallery_item,
            gallery_pk_by_external_id=gallery_pk_by_external_id,
            media_pk_by_external_id=media_pk_by_external_id,
            extract_external_id_fn=extract_external_id_fn,
            gallery_item_links=gallery_item_links,
            primary_item_to_gallery=primary_item_to_gallery,
            primary_item_to_position=primary_item_to_position,
            touched_gallery_ids=touched_gallery_ids,
            error_messages=error_messages,
        )
        errors += item_errors

        if on_progress:
            on_progress(idx, total)

    return (
        gallery_item_links,
        primary_item_to_gallery,
        primary_item_to_position,
        touched_gallery_ids,
        errors,
        error_messages,
        total,
    )


def _estimate_gallery_media_changes(
    touched_gallery_ids: set[int],
    linked_ids: set[int],
    primary_item_to_gallery: dict[int, int],
    primary_item_to_position: dict[int, int],
) -> int:
    media_items_to_clear = 0
    if touched_gallery_ids:
        media_items_to_clear = (
            MediaItem.objects.filter(gallery_id__in=touched_gallery_ids).exclude(pk__in=linked_ids).count()
        )

    media_items_to_update = 0
    if linked_ids:
        for obj in MediaItem.objects.filter(pk__in=linked_ids).only("pk", "gallery_id", "position"):
            new_gallery_id = primary_item_to_gallery[obj.pk]
            new_position = primary_item_to_position[obj.pk]
            if obj.gallery_id != new_gallery_id or obj.position != new_position:
                media_items_to_update += 1
    return media_items_to_clear + media_items_to_update


def _persist_gallery_links(
    *,
    touched_gallery_ids: set[int],
    gallery_item_links: list[MediaGalleryItem],
    linked_ids: set[int],
    primary_item_to_gallery: dict[int, int],
    primary_item_to_position: dict[int, int],
) -> int:
    actual_media_items_changed = 0
    with transaction.atomic():
        if touched_gallery_ids:
            MediaGalleryItem.objects.filter(gallery_id__in=touched_gallery_ids).delete()
            if gallery_item_links:
                MediaGalleryItem.objects.bulk_create(gallery_item_links)

            cleared = (
                MediaItem.objects.filter(gallery_id__in=touched_gallery_ids)
                .exclude(pk__in=linked_ids)
                .update(gallery_id=None)
            )
            actual_media_items_changed += cleared

        to_update = []
        for obj in MediaItem.objects.filter(pk__in=linked_ids).only("pk", "gallery_id", "position"):
            new_gallery_id = primary_item_to_gallery[obj.pk]
            new_position = primary_item_to_position[obj.pk]
            if obj.gallery_id != new_gallery_id or obj.position != new_position:
                obj.gallery_id = new_gallery_id
                obj.position = new_position
                to_update.append(obj)

        if to_update:
            MediaItem.objects.bulk_update(to_update, ["gallery", "position"])
            actual_media_items_changed += len(to_update)
    return actual_media_items_changed


def _finish_gallery_import_log(
    *,
    import_log: ImportLog,
    total: int,
    imported: int,
    errors: int,
    error_messages: list[str],
    timezone_module: Any,
    always_partial_on_errors: bool = False,
) -> None:
    import_log.records_total = total
    import_log.records_imported = imported
    import_log.records_failed = errors
    import_log.finished_at = timezone_module.now()

    if errors == 0:
        import_log.status = ImportLog.Status.SUCCESS
    elif always_partial_on_errors or imported > 0:
        import_log.status = ImportLog.Status.PARTIAL_SUCCESS
        import_log.error_message = f"{errors} link issues: {', '.join(error_messages)}"
    else:
        import_log.status = ImportLog.Status.FAILED
        import_log.error_message = f"All {errors} link resolutions failed: {', '.join(error_messages)}"
    import_log.save()


def _process_gallery_item(
    *,
    gallery_item: Any,
    gallery_pk_by_external_id: dict[str, int],
    media_pk_by_external_id: dict[str, int],
    extract_external_id_fn: Callable[[Any], str | None],
    gallery_item_links: list[MediaGalleryItem],
    primary_item_to_gallery: dict[int, int],
    primary_item_to_position: dict[int, int],
    touched_gallery_ids: set[int],
    error_messages: list[str],
) -> int:
    if not isinstance(gallery_item, dict):
        _append_limited_error(error_messages, f"Gallery item is not a dict: {gallery_item!r}")
        return 1

    gallery_ext_id = extract_external_id_fn(gallery_item.get("@id"))
    if not gallery_ext_id:
        _append_limited_error(error_messages, f"Gallery missing @id: {str(gallery_item)[:200]}")
        return 1

    gallery_pk = gallery_pk_by_external_id.get(gallery_ext_id)
    if gallery_pk is None:
        _append_limited_error(error_messages, f"Gallery not found for external_id={gallery_ext_id}")
        return 1

    touched_gallery_ids.add(gallery_pk)
    raw_items = gallery_item.get("items")
    if not isinstance(raw_items, list):
        return 0

    errors = 0
    for position, raw_media in enumerate(raw_items):
        media_ext_id = extract_external_id_fn(raw_media)
        if not media_ext_id:
            continue
        media_pk = media_pk_by_external_id.get(media_ext_id)
        if media_pk is None:
            errors += 1
            _append_limited_error(error_messages, f"MediaItem not found for external_id={media_ext_id}")
            continue
        gallery_item_links.append(MediaGalleryItem(gallery_id=gallery_pk, media_item_id=media_pk, position=position))
        if media_pk not in primary_item_to_gallery:
            primary_item_to_gallery[media_pk] = gallery_pk
            primary_item_to_position[media_pk] = position
    return errors


def sync_media_item_gallery_links_impl(
    *,
    fetch_fn: Callable[..., list[Any]],
    extract_external_id_fn: Callable[[Any], str | None],
    timezone_module: Any,
    dry_run: bool = False,
    etag_cache: dict[str, str] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
    params: dict[str, str] | None = None,
) -> int:
    """Link MediaItems to MediaGalleries using gallery payload `items` links."""
    source = "viernulvier:media_item_gallery_links"
    import_log = ImportLog.objects.create(
        source=source,
        status=ImportLog.Status.IN_PROGRESS,
        started_at=timezone_module.now(),
    )

    try:
        galleries = fetch_fn(endpoint="/media/galleries", params=params, etag_cache=etag_cache)
    except Exception as exc:
        import_log.status = ImportLog.Status.FAILED
        import_log.finished_at = timezone_module.now()
        import_log.error_message = str(exc)
        import_log.save()
        raise

    if not galleries:
        return _finalize_empty_import(import_log, timezone_module)

    gallery_pk_by_external_id = {str(ext_id): pk for ext_id, pk in MediaGallery.objects.values_list("external_id", "pk")}
    media_pk_by_external_id = {str(ext_id): pk for ext_id, pk in MediaItem.objects.values_list("external_id", "pk")}

    (
        gallery_item_links,
        primary_item_to_gallery,
        primary_item_to_position,
        touched_gallery_ids,
        errors,
        error_messages,
        total,
    ) = _handle_gallery_payload(
        galleries=galleries,
        gallery_pk_by_external_id=gallery_pk_by_external_id,
        media_pk_by_external_id=media_pk_by_external_id,
        extract_external_id_fn=extract_external_id_fn,
        on_progress=on_progress,
    )

    linked_ids = set(primary_item_to_gallery.keys())

    media_items_changed = _estimate_gallery_media_changes(
        touched_gallery_ids,
        linked_ids,
        primary_item_to_gallery,
        primary_item_to_position,
    )

    if dry_run:
        _finish_gallery_import_log(
            import_log=import_log,
            total=total,
            imported=media_items_changed,
            errors=errors,
            error_messages=error_messages,
            timezone_module=timezone_module,
            always_partial_on_errors=True,
        )
        logger.info(
            "Gallery-item link sync complete: media_items_changed=%d link_rows=%d errors=%d [DRY RUN]",
            media_items_changed,
            len(gallery_item_links),
            errors,
        )
        return media_items_changed

    actual_media_items_changed = 0
    try:
        actual_media_items_changed = _persist_gallery_links(
            touched_gallery_ids=touched_gallery_ids,
            gallery_item_links=gallery_item_links,
            linked_ids=linked_ids,
            primary_item_to_gallery=primary_item_to_gallery,
            primary_item_to_position=primary_item_to_position,
        )
    except Exception as exc:
        logger.exception("Error while syncing media gallery links")
        import_log.status = ImportLog.Status.FAILED
        import_log.records_total = total
        import_log.records_imported = actual_media_items_changed
        import_log.records_failed = errors + 1
        import_log.finished_at = timezone_module.now()
        import_log.error_message = f"Exception during gallery link sync: {exc}"
        import_log.save()
        raise

    _finish_gallery_import_log(
        import_log=import_log,
        total=total,
        imported=actual_media_items_changed,
        errors=errors,
        error_messages=error_messages,
        timezone_module=timezone_module,
    )
    logger.info(
        "Gallery-item link sync complete: media_items_changed=%d link_rows=%d errors=%d",
        actual_media_items_changed,
        len(gallery_item_links),
        errors,
    )
    return actual_media_items_changed


def _apply_local_crop_filters(
    base_query: Any, params: dict[str, str], parse_datetime_fn: Callable[[str], Any | None]
) -> tuple[Any, dict[str, str]]:
    query = base_query
    api_filter_params: dict[str, str] = {}
    for param_key, param_value in params.items():
        match = re.fullmatch(r"(created_at|updated_at)\[(after|before|strictly_after|strictly_before)]", param_key)
        if not match:
            continue
        field_name, bound = match.groups()
        api_filter_params[param_key] = param_value

        try:
            MediaItem._meta.get_field(field_name)
        except FieldDoesNotExist:
            logger.debug(
                "Skipping local pre-filter '%s' for media_item_crops (field '%s' not on MediaItem)",
                param_key,
                field_name,
            )
            continue

        try:
            dt = parse_datetime_fn(param_value)
        except (ValueError, TypeError):
            continue
        if not dt:
            continue
        lookup = "gte" if bound in {"after", "strictly_after"} else "lte"
        query = query.filter(**{f"{field_name}__{lookup}": dt})
    return query, api_filter_params


def _api_filtered_crop_candidates(
    *,
    fetch_fn: Callable[..., list[Any]],
    api_filter_params: dict[str, str],
    foto_items: list[dict[str, Any]],
    extract_external_id_fn: Callable[[Any], str | None],
) -> list[dict[str, Any]]:
    api_items = fetch_fn(endpoint="/media/items", params=api_filter_params)
    existing_pk_by_external_id = {str(row["external_id"]).strip(): row["pk"] for row in foto_items if row.get("external_id")}
    candidates: list[dict[str, Any]] = []
    for api_item in api_items:
        if not isinstance(api_item, dict):
            continue
        raw_type = str(api_item.get("type") or "").strip().lower()
        if raw_type and raw_type != MediaItem.MediaItemType.IMAGE:
            continue
        ext_id = extract_external_id_fn(api_item.get("@id") or api_item.get("external_id") or api_item.get("id"))
        if not ext_id:
            continue
        normalized_ext_id = str(ext_id).strip()
        candidates.append({"pk": existing_pk_by_external_id.get(normalized_ext_id), "external_id": normalized_ext_id})
    return candidates


def _upsert_missing_media_item(
    external_id: str,
    item_data: dict[str, Any],
    extract_external_id_fn: Callable[[Any], str | None],
) -> int:
    media_type_raw = str(item_data.get("type") or MediaItem.MediaItemType.IMAGE).strip().lower()
    type_field = MediaItem._meta.get_field("type")
    type_choices = cast("list[tuple[str, str]]", getattr(type_field, "choices", []))
    valid_types = {choice for choice, _ in type_choices}
    media_type = media_type_raw if media_type_raw in valid_types else MediaItem.MediaItemType.IMAGE

    gallery_ext_id = extract_external_id_fn(item_data.get("gallery"))
    gallery_pk = None
    if gallery_ext_id:
        gallery_pk = (
            MediaGallery.objects.filter(external_id=str(gallery_ext_id).strip()).values_list("pk", flat=True).first()
        )

    obj, _ = MediaItem.objects.update_or_create(
        external_id=external_id,
        defaults={
            "type": media_type,
            "gallery_id": gallery_pk,
            "original_filename": str(item_data.get("original_filename") or ""),
            "position": item_data.get("position") or 0,
            "width": item_data.get("width"),
            "height": item_data.get("height"),
            "format": str(item_data.get("format") or ""),
        },
    )
    logger.info("Upserted missing MediaItem dependency for crops: %s (pk=%s)", external_id, obj.pk)
    return obj.pk


def _save_single_crop(
    *,
    session: requests.Session,
    item_pk: int,
    external_id: str,
    crop_data: dict[str, Any],
    wanted_crops: set[str],
    dry_run: bool,
    download_image_fn: Callable[[requests.Session, str], bytes | None],
    derive_crop_filename_fn: Callable[[str, str, str], str],
    error_messages: list[str],
) -> tuple[int, int]:
    crop_name: str = crop_data.get("name", "")
    if crop_name not in wanted_crops:
        return 0, 0

    image_url: str = crop_data.get("url", "")
    if not image_url:
        logger.warning("Crop '%s' for %s has no URL - skipping", crop_name, external_id)
        return 0, 0

    if dry_run:
        logger.info("[DRY RUN] Would save crop '%s' for MediaItem pk=%d from %s", crop_name, item_pk, image_url)
        return 1, 0

    image_bytes = download_image_fn(session, image_url)
    if image_bytes is None:
        _append_limited_error(error_messages, f"Download failed for crop '{crop_name}' on {external_id}")
        return 0, 1

    filename = derive_crop_filename_fn(crop_name, external_id, image_url)
    try:
        image_field = cast("models.ImageField", media_models.MediaItemCrop._meta.get_field("image"))
        upload_name = image_field.generate_filename(None, filename)
        saved_path = image_field.storage.save(upload_name, ContentFile(image_bytes))
        with transaction.atomic():
            _, created = media_models.MediaItemCrop.objects.update_or_create(
                media_item_id=item_pk,
                name=crop_name,
                defaults={"image": saved_path},
            )
        logger.debug(
            "%s crop '%s' for MediaItem pk=%d -> %s",
            "Created" if created else "Updated",
            crop_name,
            item_pk,
            saved_path,
        )
        return 1, 0
    except Exception as exc:
        logger.exception("Error saving crop '%s' for MediaItem pk=%d", crop_name, item_pk)
        _append_limited_error(error_messages, f"Save failed for crop '{crop_name}' on {external_id}: {exc}")
        return 0, 1


def _finish_crop_import_log(
    import_log: ImportLog,
    *,
    total: int,
    saved: int,
    errors: int,
    error_messages: list[str],
    timezone_module: Any,
) -> None:
    import_log.records_total = total
    import_log.records_imported = saved
    import_log.records_failed = errors
    import_log.finished_at = timezone_module.now()
    if errors == 0:
        import_log.status = ImportLog.Status.SUCCESS
    elif saved > 0:
        import_log.status = ImportLog.Status.PARTIAL_SUCCESS
        import_log.error_message = f"{errors} crops failed: {', '.join(error_messages)}"
    else:
        import_log.status = ImportLog.Status.FAILED
        import_log.error_message = f"All {errors} crops failed: {', '.join(error_messages)}"
    import_log.save()


def _load_crop_candidates(
    *,
    fetch_fn: Callable[..., list[Any]],
    extract_external_id_fn: Callable[[Any], str | None],
    parse_datetime_fn: Callable[[str], Any | None],
    params: dict[str, str] | None,
) -> list[dict[str, Any]]:
    foto_items_query = MediaItem.objects.filter(type=MediaItem.MediaItemType.IMAGE)
    api_filter_params: dict[str, str] = {}
    if params:
        foto_items_query, api_filter_params = _apply_local_crop_filters(foto_items_query, params, parse_datetime_fn)

    foto_items = list(foto_items_query.values("pk", "external_id"))
    if not api_filter_params:
        return foto_items

    filtered_candidates = _api_filtered_crop_candidates(
        fetch_fn=fetch_fn,
        api_filter_params=api_filter_params,
        foto_items=foto_items,
        extract_external_id_fn=extract_external_id_fn,
    )
    logger.info(
        "Applied API filters to media_item_crops candidates: %d -> %d (local-independent)",
        len(foto_items),
        len(filtered_candidates),
    )
    return filtered_candidates


def _fetch_crop_item_data(
    *,
    session: requests.Session,
    external_id: str,
    fetch_with_retry_fn: Callable[..., tuple[Any | None, str | None]],
    error_messages: list[str],
) -> tuple[dict[str, Any] | None, int]:
    item_url = external_id if external_id.startswith("http") else urljoin(BASE_DOMAIN, external_id)
    try:
        item_data, _ = fetch_with_retry_fn(session, item_url)
    except Exception as exc:
        logger.exception("Failed to fetch media item %s", item_url)
        _append_limited_error(error_messages, f"Fetch failed for {external_id}: {exc}")
        return None, 1
    if item_data is None:
        return None, 0
    if not isinstance(item_data, dict):
        _append_limited_error(error_messages, f"Unexpected media item payload for {external_id}")
        return None, 1
    return item_data, 0


def _ensure_crop_item_pk(
    *,
    item_pk: Any,
    external_id: str,
    item_data: dict[str, Any],
    dry_run: bool,
    extract_external_id_fn: Callable[[Any], str | None],
    error_messages: list[str],
) -> tuple[int | None, int]:
    if item_pk is not None:
        return item_pk, 0
    if dry_run:
        logger.info("[DRY RUN] Would upsert missing MediaItem for crop sync: %s", external_id)
        _append_limited_error(error_messages, f"MediaItem dependency unresolved for {external_id}")
        return None, 1
    try:
        return _upsert_missing_media_item(external_id, item_data, extract_external_id_fn), 0
    except Exception as exc:
        logger.exception("Failed to upsert MediaItem dependency for crop sync (%s)", external_id)
        _append_limited_error(error_messages, f"Missing MediaItem upsert failed for {external_id}: {exc}")
        return None, 1


def _process_crop_item(
    *,
    row: dict[str, Any],
    session: requests.Session,
    fetch_with_retry_fn: Callable[..., tuple[Any | None, str | None]],
    download_image_fn: Callable[[requests.Session, str], bytes | None],
    derive_crop_filename_fn: Callable[[str, str, str], str],
    extract_external_id_fn: Callable[[Any], str | None],
    wanted_crops: set[str],
    dry_run: bool,
    error_messages: list[str],
) -> tuple[int, int]:
    item_pk = row.get("pk")
    external_id = str(row.get("external_id") or "")
    if not external_id:
        logger.warning("MediaItem pk=%d has no external_id - skipping", item_pk)
        return 0, 1

    item_data, fetch_errors = _fetch_crop_item_data(
        session=session,
        external_id=external_id,
        fetch_with_retry_fn=fetch_with_retry_fn,
        error_messages=error_messages,
    )
    if item_data is None:
        return 0, fetch_errors

    item_pk, pk_errors = _ensure_crop_item_pk(
        item_pk=item_pk,
        external_id=external_id,
        item_data=item_data,
        dry_run=dry_run,
        extract_external_id_fn=extract_external_id_fn,
        error_messages=error_messages,
    )
    if item_pk is None:
        logger.error("MediaItem dependency unresolved for crop sync: %s", external_id)
        return 0, fetch_errors + pk_errors

    crops_raw = item_data.get("crops", [])
    if not isinstance(crops_raw, list):
        logger.debug("Unexpected crops format for %s: %r", external_id, crops_raw)
        return 0, fetch_errors + pk_errors

    saved = 0
    errors = fetch_errors + pk_errors
    for crop_data in crops_raw:
        if not isinstance(crop_data, dict):
            continue
        saved_inc, errors_inc = _save_single_crop(
            session=session,
            item_pk=item_pk,
            external_id=external_id,
            crop_data=crop_data,
            wanted_crops=wanted_crops,
            dry_run=dry_run,
            download_image_fn=download_image_fn,
            derive_crop_filename_fn=derive_crop_filename_fn,
            error_messages=error_messages,
        )
        saved += saved_inc
        errors += errors_inc
    return saved, errors


def sync_media_item_crops_impl(
    *,
    fetch_fn: Callable[..., list[Any]],
    build_session_fn: Callable[[], requests.Session],
    fetch_with_retry_fn: Callable[..., tuple[Any | None, str | None]],
    download_image_fn: Callable[[requests.Session, str], bytes | None],
    derive_crop_filename_fn: Callable[[str, str, str], str],
    extract_external_id_fn: Callable[[Any], str | None],
    parse_datetime_fn: Callable[[str], Any | None],
    timezone_module: Any,
    dry_run: bool = False,
    on_progress: Callable[[int, int], None] | None = None,
    params: dict[str, str] | None = None,
) -> int:
    """Fetch individual foto MediaItems, download wanted crops, and persist them."""
    import_log = ImportLog.objects.create(
        source="viernulvier:media_item_crops",
        status=ImportLog.Status.IN_PROGRESS,
        started_at=timezone_module.now(),
    )

    try:
        foto_items = _load_crop_candidates(
            fetch_fn=fetch_fn,
            extract_external_id_fn=extract_external_id_fn,
            parse_datetime_fn=parse_datetime_fn,
            params=params,
        )
    except Exception as exc:
        import_log.status = ImportLog.Status.FAILED
        import_log.finished_at = timezone_module.now()
        import_log.error_message = str(exc)
        import_log.save()
        raise

    if not foto_items:
        logger.info("No foto MediaItems found - skipping crop sync.")
        return _finalize_empty_import(import_log, timezone_module)

    wanted_crops: set[str] = media_models.MediaItemCrop.SYNCED_CROP_NAMES
    total = len(foto_items)
    saved = 0
    errors = 0
    error_messages: list[str] = []
    session = build_session_fn()

    logger.info("Syncing crops for %d foto MediaItems (variants: %s)", total, ", ".join(sorted(wanted_crops)))

    for idx, row in enumerate(foto_items, start=1):
        saved_inc, errors_inc = _process_crop_item(
            row=row,
            session=session,
            fetch_with_retry_fn=fetch_with_retry_fn,
            download_image_fn=download_image_fn,
            derive_crop_filename_fn=derive_crop_filename_fn,
            extract_external_id_fn=extract_external_id_fn,
            wanted_crops=wanted_crops,
            dry_run=dry_run,
            error_messages=error_messages,
        )
        saved += saved_inc
        errors += errors_inc

        if on_progress:
            on_progress(idx, total)

    _finish_crop_import_log(
        import_log,
        total=total,
        saved=saved,
        errors=errors,
        error_messages=error_messages,
        timezone_module=timezone_module,
    )
    logger.info("Crop sync complete: saved=%d, errors=%d%s", saved, errors, " [DRY RUN]" if dry_run else "")
    return saved
