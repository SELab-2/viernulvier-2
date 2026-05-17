"""Tests for the import_legacy_csv management command."""

from __future__ import annotations

from io import StringIO

from django.core.management import call_command
import pytest

import apps.imports.management.commands.import_legacy_csv as import_legacy_csv_command

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    ("args", "expected_call", "expected_output"),
    [
        (
            ["--dry-run"],
            {"dry_run": True, "only": None, "has_progress_callback": True},
            "Imported 12 legacy CSV records [DRY RUN]",
        ),
        (
            ["--only", "productions"],
            {"dry_run": False, "only": "productions", "has_progress_callback": True},
            "Imported 7 legacy CSV records",
        ),
    ],
)
def test_import_legacy_csv_management_command_passes_expected_arguments(
    monkeypatch,
    args: list[str],
    expected_call: dict[str, object],
    expected_output: str,
) -> None:
    call_args = {}

    def _fake_import(*, dry_run: bool, only: str | None = None, progress_callback=None) -> int:
        call_args["dry_run"] = dry_run
        call_args["only"] = only
        call_args["has_progress_callback"] = progress_callback is not None
        return 12 if dry_run else 7

    monkeypatch.setattr(import_legacy_csv_command, "import_bundled_legacy_csv_files", _fake_import)
    output = StringIO()

    call_command("import_legacy_csv", *args, stdout=output)

    assert call_args == expected_call
    assert expected_output in output.getvalue()


def test_import_legacy_csv_management_command_updates_tqdm(monkeypatch) -> None:
    class _FakeBar:
        def __init__(self, total):
            self.total = total
            self.n = 0
            self.updates: list[int] = []
            self.closed = False

        def update(self, value: int) -> None:
            self.n += value
            self.updates.append(value)

        def close(self) -> None:
            self.closed = True

    created: dict[str, _FakeBar] = {}

    def _fake_tqdm(*, total, unit, desc, leave):
        assert unit == "rows"
        assert desc == "Importing legacy CSV"
        assert leave is False
        bar = _FakeBar(total)
        created["bar"] = bar
        return bar

    def _fake_import(*, dry_run: bool, only: str | None = None, progress_callback=None) -> int:
        assert dry_run is False
        assert only is None
        assert progress_callback is not None
        progress_callback(1, 3)
        progress_callback(3, 3)
        return 3

    monkeypatch.setattr(import_legacy_csv_command, "_tqdm", _fake_tqdm)
    monkeypatch.setattr(import_legacy_csv_command, "import_bundled_legacy_csv_files", _fake_import)
    output = StringIO()

    call_command("import_legacy_csv", stdout=output)

    bar = created["bar"]
    assert bar.updates == [1, 2]
    assert bar.closed is True
    assert "Imported 3 legacy CSV records" in output.getvalue()


def test_import_legacy_csv_management_command_works_without_tqdm(monkeypatch) -> None:
    callback_observed = {"called": False}

    def _fake_import(*, dry_run: bool, only: str | None = None, progress_callback=None) -> int:
        assert dry_run is True
        assert only is None
        assert progress_callback is not None
        callback_observed["called"] = True
        progress_callback(1, 1)
        return 1

    monkeypatch.setattr(import_legacy_csv_command, "_tqdm", None)
    monkeypatch.setattr(import_legacy_csv_command, "import_bundled_legacy_csv_files", _fake_import)
    output = StringIO()

    call_command("import_legacy_csv", "--dry-run", stdout=output)

    assert callback_observed["called"] is True
    assert "Imported 1 legacy CSV records [DRY RUN]" in output.getvalue()


def test_import_legacy_csv_management_command_refreshes_tqdm_when_total_changes(monkeypatch) -> None:
    class _FakeBar:
        def __init__(self, total):
            self.total = total
            self.n = 0
            self.updates: list[int] = []
            self.closed = False
            self.refresh_count = 0

        def update(self, value: int) -> None:
            self.n += value
            self.updates.append(value)

        def refresh(self) -> None:
            self.refresh_count += 1

        def close(self) -> None:
            self.closed = True

    created: dict[str, _FakeBar] = {}

    def _fake_tqdm(*, total, unit, desc, leave):
        assert unit == "rows"
        assert desc == "Importing legacy CSV"
        assert leave is False
        bar = _FakeBar(total)
        created["bar"] = bar
        return bar

    def _fake_import(*, dry_run: bool, only: str | None = None, progress_callback=None) -> int:
        assert dry_run is False
        assert only is None
        assert progress_callback is not None
        progress_callback(1, 2)
        progress_callback(2, 3)
        return 2

    monkeypatch.setattr(import_legacy_csv_command, "_tqdm", _fake_tqdm)
    monkeypatch.setattr(import_legacy_csv_command, "import_bundled_legacy_csv_files", _fake_import)
    output = StringIO()

    call_command("import_legacy_csv", stdout=output)

    bar = created["bar"]
    assert bar.total == 3
    assert bar.refresh_count == 1
    assert bar.updates == [1, 1]
    assert bar.closed is True
    assert "Imported 2 legacy CSV records" in output.getvalue()
