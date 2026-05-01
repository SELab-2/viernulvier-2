"""Management command argument/filter and main loop coverage tests."""

from datetime import UTC, datetime, timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management.base import CommandParser, OutputWrapper
import pytest

from apps.import_log.models import ImportLog
from apps.imports.management.commands.sync_viernulvier import (
    SINCE_LAST_SUCCESS_SAFETY_BUFFER,
    SYNC_STEPS,
    Command,
)


@pytest.fixture(autouse=True)
def _mock_media_item_gallery_link_step():
    """Keep command tests deterministic by stubbing custom gallery-link syncing."""

    with patch("apps.imports.management.commands.sync_viernulvier.sync_media_item_gallery_links", return_value=0):
        yield


def _make_command() -> Command:
    cmd = Command()
    cmd.stdout = OutputWrapper(StringIO())
    cmd.stderr = OutputWrapper(StringIO())
    return cmd


def test_add_arguments_registers_only_and_all_filter_variants() -> None:
    parser = CommandParser(prog="manage.py")
    command = Command()

    command.add_arguments(parser)

    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert "--only" in option_strings

    for prefix in command.FILTER_FIELDS:
        for bound in ("after", "before"):
            assert f"--{prefix}-{bound}" in option_strings
            assert f"--{prefix}-{bound}-x" in option_strings


def test_handle_builds_expected_filter_params_and_respects_only() -> None:

    command = _make_command()
    options = {
        "only": "events",
        "created_after": "2024-01-01T00:00:00Z",
        "updated_before_x": "2024-12-31T23:59:59Z",
    }

    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=5) as sync_mock:
        command.handle(**options)

    call_kwargs = sync_mock.call_args.kwargs
    assert sync_mock.call_count == 1
    assert call_kwargs["endpoint"] == "/events"
    assert call_kwargs["params"] == {
        "created_at[after]": "2024-01-01T00:00:00Z",
        "updated_at[strictly_before]": "2024-12-31T23:59:59Z",
    }


def test_handle_reports_unknown_step_without_syncing() -> None:

    command = _make_command()

    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier") as sync_mock:
        result = command.handle(only="not_a_real_step")

    assert result is None
    assert "Unknown step 'not_a_real_step'" in command.stderr.getvalue()
    sync_mock.assert_not_called()


@pytest.mark.parametrize(
    ("options", "expected_params"),
    [
        ({"created_after_x": "2024-01-01T00:00:00Z"}, {"created_at[strictly_after]": "2024-01-01T00:00:00Z"}),
        ({"updated_before_x": "2024-12-31T23:59:59Z"}, {"updated_at[strictly_before]": "2024-12-31T23:59:59Z"}),
        ({"starts_after": "2025-06-01T00:00:00Z"}, {"starts_at[after]": "2025-06-01T00:00:00Z"}),
    ],
)
def test_handle_single_filter_mappings(options, expected_params) -> None:

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0) as mock_sync:
        cmd.handle(only="events", **options)
    assert mock_sync.call_args.kwargs["params"] == expected_params


def test_handle_combined_filters() -> None:

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0) as mock_sync:
        cmd.handle(
            only="events",
            created_after="2024-01-01T00:00:00Z",
            ends_before="2024-12-31T23:59:59Z",
        )

    params = mock_sync.call_args.kwargs["params"]
    assert params["created_at[after]"] == "2024-01-01T00:00:00Z"
    assert params["ends_at[before]"] == "2024-12-31T23:59:59Z"


def test_dry_run_warning_written_to_stdout() -> None:

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0):
        cmd.handle(only="events", dry_run=True)
    assert "DRY RUN" in cmd.stdout.getvalue()


def test_exception_in_step_logged_as_failed() -> None:

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", side_effect=RuntimeError("API boom")):
        cmd.handle(only="events")

    assert "FAILED" in cmd.stdout.getvalue()
    assert "API boom" in cmd.stdout.getvalue()


def test_handle_no_only_runs_all_steps() -> None:

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=5) as mock_sync:
        cmd.handle()

    assert mock_sync.call_count == len(SYNC_STEPS)


def test_etag_cache_shared_across_steps() -> None:

    cmd = _make_command()
    received_caches = []

    def capture_cache(**kwargs) -> int:
        received_caches.append(id(kwargs.get("etag_cache")))
        return 0

    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", side_effect=capture_cache):
        cmd.handle()

    assert len(set(received_caches)) == 1


def test_total_saved_count_in_summary() -> None:

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=42):
        cmd.handle(only="events")

    assert "42" in cmd.stdout.getvalue()


# ---------------------------------------------------------------------------
# --since-last-success
# ---------------------------------------------------------------------------


def _expected_updated_after(started_at: datetime) -> str:
    """Mirror the command's --updated-after derivation (for asserting params)."""
    return (started_at - SINCE_LAST_SUCCESS_SAFETY_BUFFER).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.mark.django_db
def test_since_last_success_uses_latest_successful_import_log_started_at() -> None:
    """Derive --updated-after from the most recent non-failed viernulvier:* ImportLog row."""
    older_success = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    latest_success = datetime(2025, 1, 5, 3, 30, 0, tzinfo=UTC)
    ImportLog.objects.create(
        source="viernulvier:/events",
        status=ImportLog.Status.SUCCESS,
        started_at=older_success,
        finished_at=older_success + timedelta(minutes=2),
    )
    ImportLog.objects.create(
        source="viernulvier:/productions",
        status=ImportLog.Status.PARTIAL_SUCCESS,
        started_at=latest_success,
        finished_at=latest_success + timedelta(minutes=2),
    )

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0) as sync_mock:
        cmd.handle(only="events", since_last_success=True)

    assert sync_mock.called
    params = sync_mock.call_args.kwargs["params"]
    assert params == {"updated_at[after]": _expected_updated_after(latest_success)}


@pytest.mark.django_db
def test_since_last_success_skips_failed_imports() -> None:
    """FAILED rows must not contribute to --updated-after."""
    failed_at = datetime(2025, 1, 10, 0, 0, 0, tzinfo=UTC)
    success_at = datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)
    ImportLog.objects.create(
        source="viernulvier:/events",
        status=ImportLog.Status.FAILED,
        started_at=failed_at,
    )
    ImportLog.objects.create(
        source="viernulvier:/productions",
        status=ImportLog.Status.SUCCESS,
        started_at=success_at,
        finished_at=success_at + timedelta(minutes=1),
    )

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0) as sync_mock:
        cmd.handle(only="events", since_last_success=True)

    params = sync_mock.call_args.kwargs["params"]
    assert params == {"updated_at[after]": _expected_updated_after(success_at)}


@pytest.mark.django_db
def test_since_last_success_ignores_non_viernulvier_sources() -> None:
    """Only source rows prefixed with 'viernulvier:' count as prior runs."""
    legacy_at = datetime(2025, 1, 10, 0, 0, 0, tzinfo=UTC)
    ImportLog.objects.create(
        source="legacy_csv:productions",
        status=ImportLog.Status.SUCCESS,
        started_at=legacy_at,
        finished_at=legacy_at + timedelta(minutes=1),
    )

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier") as sync_mock:
        cmd.handle(only="events", since_last_success=True)

    sync_mock.assert_not_called()
    assert "No prior successful Viernulvier import" in cmd.stderr.getvalue()


@pytest.mark.django_db
def test_since_last_success_errors_when_no_prior_successful_run() -> None:
    """Empty ImportLog must produce a clear error and not run any sync."""
    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier") as sync_mock:
        cmd.handle(only="events", since_last_success=True)

    sync_mock.assert_not_called()
    assert "No prior successful Viernulvier import" in cmd.stderr.getvalue()


@pytest.mark.django_db
def test_since_last_success_rejects_conflicting_updated_after() -> None:
    """Combining --since-last-success with --updated-after must fail explicitly."""
    success_at = datetime(2025, 1, 5, 3, 30, 0, tzinfo=UTC)
    ImportLog.objects.create(
        source="viernulvier:/events",
        status=ImportLog.Status.SUCCESS,
        started_at=success_at,
        finished_at=success_at + timedelta(minutes=1),
    )

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier") as sync_mock:
        cmd.handle(
            only="events",
            since_last_success=True,
            updated_after="2024-01-01T00:00:00Z",
        )

    sync_mock.assert_not_called()
    assert "--since-last-success cannot be combined" in cmd.stderr.getvalue()


def test_add_arguments_registers_since_last_success() -> None:
    parser = CommandParser(prog="manage.py")
    Command().add_arguments(parser)
    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert "--since-last-success" in option_strings
