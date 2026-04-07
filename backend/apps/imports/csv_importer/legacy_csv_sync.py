"""Import orchestration and import-log handling for legacy CSV data."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone

from apps.import_log.models import ImportLog
from apps.imports.scrapers.viernulvier_import_log import append_limited_error, finalize_import_log

from . import legacy_csv_constants as _constants
from . import legacy_csv_handlers as _handlers
from . import legacy_csv_io as _io

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

logger = logging.getLogger(__name__)


def _import_legacy_csv_rows(
    *,
    source_name: str,
    rows: Iterable[dict[str, Any]],
    row_handler: Any,
    partial_error_label: str,
    failed_error_label: str,
    dry_run: bool,
    total_rows: int | None = None,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> int:
    import_log = ImportLog.objects.create(
        source=f"legacy_csv:{source_name}",
        status=ImportLog.Status.IN_PROGRESS,
        started_at=timezone.now(),
    )

    saved = 0
    total = 0
    errors = 0
    error_messages: list[str] = []
    try:
        for row in rows:
            total += 1
            try:
                with transaction.atomic():
                    saved_row = row_handler(row, dry_run=dry_run)
            except Exception as exc:
                logger.exception("Legacy CSV row import failed for %s at row %s", source_name, total)
                errors += 1
                append_limited_error(error_messages, f"Row {total}: {exc}")
            else:
                if saved_row:
                    saved += 1
            if progress_callback:
                progress_callback(total, total_rows)
    except Exception as exc:
        if import_log.status != ImportLog.Status.FAILED:
            import_log.status = ImportLog.Status.FAILED
            import_log.finished_at = timezone.now()
            import_log.records_total = total
            import_log.records_imported = saved
            import_log.records_failed = 0
            import_log.error_message = str(exc)
            import_log.save()
        raise

    finalize_import_log(
        import_log=import_log,
        total=total,
        imported=saved,
        errors=errors,
        error_messages=error_messages,
        timezone_module=timezone,
        partial_error_label=partial_error_label,
        failed_error_label=failed_error_label,
    )
    return saved


def _import_legacy_csv_file(
    csv_path: Path,
    *,
    row_handler: Any,
    partial_error_label: str,
    failed_error_label: str,
    dry_run: bool,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> int:
    total_rows = _io._count_csv_rows(csv_path) if progress_callback else None
    return _import_legacy_csv_rows(
        source_name=csv_path.name,
        rows=_io._iter_csv_rows(csv_path),
        row_handler=row_handler,
        partial_error_label=partial_error_label,
        failed_error_label=failed_error_label,
        dry_run=dry_run,
        total_rows=total_rows,
        progress_callback=progress_callback,
    )


def import_legacy_csv_file(
    csv_path: Path | str,
    *,
    dry_run: bool = False,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> int:
    """Import a single legacy CSV export into the Django database."""
    path = Path(csv_path)
    kind = _io.detect_legacy_csv_kind(path)
    if kind == "productions":
        return _import_legacy_csv_file(
            path,
            row_handler=_handlers._import_legacy_production_row,
            partial_error_label="production rows failed",
            failed_error_label="production rows failed",
            dry_run=dry_run,
            progress_callback=progress_callback,
        )
    if kind == "events":
        return _import_legacy_csv_file(
            path,
            row_handler=_handlers._import_legacy_event_row,
            partial_error_label="event rows failed",
            failed_error_label="event rows failed",
            dry_run=dry_run,
            progress_callback=progress_callback,
        )
    raise ValueError(f"Unsupported CSV kind: {kind}")


def import_bundled_legacy_csv_files(
    *,
    dry_run: bool = False,
    base_dir: Path | None = None,
    only: str | None = None,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> int:
    """Import the legacy CSV files bundled with the backend package."""
    root = base_dir or _constants.PACKAGE_ROOT
    productions_original_path = root / _constants.LEGACY_PRODUCTION_ORIGINAL_CSV.name
    productions_fallback_path = root / _constants.LEGACY_PRODUCTION_CSV.name
    productions_path = productions_original_path if productions_original_path.exists() else productions_fallback_path
    events_path = root / _constants.LEGACY_EVENT_CSV.name

    csv_paths: list[Path]
    if only == "productions":
        csv_paths = [productions_path]
    elif only == "events":
        csv_paths = [events_path]
    else:
        csv_paths = [productions_path, events_path]

    total_rows = sum(_io._count_csv_rows(csv_path) for csv_path in csv_paths) if progress_callback else None
    processed_offset = 0
    imported_total = 0

    for csv_path in csv_paths:
        file_processed = 0

        def _file_progress(processed: int, _total: int | None, *, offset: int = processed_offset) -> None:
            nonlocal file_processed
            file_processed = processed
            if progress_callback:
                progress_callback(offset + processed, total_rows)

        imported_total += import_legacy_csv_file(
            csv_path,
            dry_run=dry_run,
            progress_callback=_file_progress if progress_callback else None,
        )
        processed_offset += file_processed

    return imported_total
