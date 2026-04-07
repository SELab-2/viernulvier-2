from __future__ import annotations

import pytest

from apps.import_log.models import ImportLog
from apps.imports.csv_importer import import_legacy_csv_file, legacy_csv_normalize, legacy_csv_sync
from apps.imports.csv_importer.legacy_csv_io import _count_csv_rows, _iter_csv_rows
from tests.imports_csv.helpers import write_csv

pytestmark = pytest.mark.django_db(transaction=True)


def test_import_legacy_csv_file_rejects_unknown_headers(tmp_path) -> None:
    csv_path = tmp_path / "mystery.csv"
    write_csv(csv_path, ["foo", "bar"], [["1", "2"]])

    with pytest.raises(ValueError, match="Unsupported legacy CSV headers"):
        import_legacy_csv_file(csv_path)


def test_import_legacy_csv_missing_csv_headers(tmp_path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing headers"):
        _iter_csv_rows(bad_csv)


def test_import_legacy_csv_rows_exception_during_processing(tmp_path) -> None:
    def _failing_handler(row, *, dry_run):
        raise RuntimeError("Test failure")

    csv_path = tmp_path / "Productions - output.csv"
    write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "900", "legacy-900"]],
    )

    rows = list(legacy_csv_sync._io._iter_csv_rows(csv_path))

    imported = legacy_csv_sync._import_legacy_csv_rows(
        source_name="test.csv",
        rows=rows,
        row_handler=_failing_handler,
        partial_error_label="test failed",
        failed_error_label="test failed",
        dry_run=False,
    )

    assert imported == 0
    log = ImportLog.objects.get(source="legacy_csv:test.csv")
    assert log.status == ImportLog.Status.FAILED
    assert log.records_failed == 1


def test_import_legacy_csv_rows_with_progress_callback(tmp_path) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [
            ["Artist1", "Title1", "Body", "Credits", "Theater", "1000", "legacy-1000"],
            ["Artist2", "Title2", "Body", "Credits", "Theater", "1001", "legacy-1001"],
        ],
    )

    progress_updates = []

    def _progress_callback(processed, total):
        progress_updates.append((processed, total))

    imported = legacy_csv_sync._import_legacy_csv_file(
        csv_path,
        row_handler=legacy_csv_sync._handlers._import_legacy_production_row,
        partial_error_label="test failed",
        failed_error_label="test failed",
        dry_run=False,
        progress_callback=_progress_callback,
    )

    assert imported == 2
    assert progress_updates == [(1, 2), (2, 2)]


def test_count_csv_rows_with_valid_csv(tmp_path) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [
            ["Artist1", "Title1", "Body", "Credits", "Theater", "1100", "legacy-1100"],
            ["Artist2", "Title2", "Body", "Credits", "Theater", "1101", "legacy-1101"],
            ["Artist3", "Title3", "Body", "Credits", "Theater", "1102", "legacy-1102"],
        ],
    )

    count = _count_csv_rows(csv_path)

    assert count == 3


def test_import_csv_without_progress_callback_no_count(tmp_path) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "1110", "legacy-1110"]],
    )

    imported = legacy_csv_sync._import_legacy_csv_file(
        csv_path,
        row_handler=legacy_csv_sync._handlers._import_legacy_production_row,
        partial_error_label="test failed",
        failed_error_label="test failed",
        dry_run=False,
        progress_callback=None,
    )

    assert imported == 1


def test_count_csv_rows_missing_headers_raises_value_error(tmp_path) -> None:
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing headers"):
        _count_csv_rows(csv_path)


def test_parse_legacy_datetime_returns_none_when_parser_raises(monkeypatch) -> None:
    def _boom(_value):
        raise ValueError("broken parser")

    monkeypatch.setattr(legacy_csv_normalize, "parse_datetime", _boom)

    assert legacy_csv_normalize._parse_legacy_datetime("2010-01-01 10:00:00") is None


def test_import_legacy_csv_rows_marks_log_failed_when_row_iteration_crashes() -> None:
    def _rows():
        yield {
            "Titel": "Artist",
            "Ondertitel": "Title",
            "Description1": "Body",
            "Description2": "Credits",
            "Genre": "Theater",
            "ID": "1140",
            "Planning ID": "legacy-1140",
        }
        raise RuntimeError("iterator exploded")

    def _ok_handler(_row, *, dry_run):
        return True

    with pytest.raises(RuntimeError, match="iterator exploded"):
        legacy_csv_sync._import_legacy_csv_rows(
            source_name="iter-fail.csv",
            rows=_rows(),
            row_handler=_ok_handler,
            partial_error_label="rows failed",
            failed_error_label="rows failed",
            dry_run=False,
        )

    log = ImportLog.objects.get(source="legacy_csv:iter-fail.csv")
    assert log.status == ImportLog.Status.FAILED
    assert log.records_total == 1
    assert log.records_imported == 1
    assert log.records_failed == 0
    assert "iterator exploded" in (log.error_message or "")


def test_import_legacy_csv_file_rejects_unsupported_detected_kind(monkeypatch, tmp_path) -> None:

    csv_path = tmp_path / "Productions - output.csv"
    write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "1141", "legacy-1141"]],
    )

    monkeypatch.setattr(legacy_csv_sync._io, "detect_legacy_csv_kind", lambda _path: "mystery")

    with pytest.raises(ValueError, match="Unsupported CSV kind: mystery"):
        legacy_csv_sync.import_legacy_csv_file(csv_path)
