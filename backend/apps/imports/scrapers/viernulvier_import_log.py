"""Shared import-log helpers for Viernulvier scraper modules."""

from __future__ import annotations

from typing import Any

from apps.import_log.models import ImportLog

from .viernulvier_constants import MAX_ERROR_MESSAGES


def append_limited_error(error_messages: list[str], message: str) -> None:
    """Append an error message, keeping the existing capped-list behavior."""
    if len(error_messages) < MAX_ERROR_MESSAGES:
        error_messages.append(message)


def finalize_empty_import(import_log: ImportLog, timezone_module: Any) -> int:
    """Finalize an import log for an empty payload."""
    import_log.status = ImportLog.Status.SUCCESS
    import_log.records_total = 0
    import_log.records_imported = 0
    import_log.records_failed = 0
    import_log.finished_at = timezone_module.now()
    import_log.save()
    return 0


def finalize_import_log(
    import_log: ImportLog,
    *,
    total: int,
    imported: int,
    errors: int,
    error_messages: list[str],
    timezone_module: Any,
    partial_error_label: str,
    failed_error_label: str,
    always_partial_on_errors: bool = False,
) -> None:
    """Finalize an import log using the same counters/status semantics as the existing scrapers."""
    truncation_note = f" (showing first {MAX_ERROR_MESSAGES} of {errors})" if errors > MAX_ERROR_MESSAGES else ""
    import_log.records_total = total
    import_log.records_imported = imported
    import_log.records_failed = errors
    import_log.finished_at = timezone_module.now()

    if errors == 0:
        import_log.status = ImportLog.Status.SUCCESS
    elif always_partial_on_errors or imported > 0:
        import_log.status = ImportLog.Status.PARTIAL_SUCCESS
        import_log.error_message = f"{errors} {partial_error_label}{truncation_note}: {', '.join(error_messages)}"
    else:
        import_log.status = ImportLog.Status.FAILED
        import_log.error_message = f"All {errors} {failed_error_label}{truncation_note}: {', '.join(error_messages)}"

    import_log.save()
