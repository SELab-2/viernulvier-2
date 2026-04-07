"""Management command argument/filter and main loop coverage tests."""

from io import StringIO

from django.core.management.base import CommandParser, OutputWrapper
import pytest

from apps.imports.management.commands.sync_viernulvier import Command, SYNC_STEPS


@pytest.fixture(autouse=True)
def _mock_media_item_gallery_link_step():
    """Keep command tests deterministic by stubbing custom gallery-link syncing."""
    from unittest.mock import patch

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
    from unittest.mock import patch

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
    from unittest.mock import patch

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
    from unittest.mock import patch

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0) as mock_sync:
        cmd.handle(only="events", **options)
    assert mock_sync.call_args.kwargs["params"] == expected_params


def test_handle_combined_filters() -> None:
    from unittest.mock import patch

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
    from unittest.mock import patch

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0):
        cmd.handle(only="events", dry_run=True)
    assert "DRY RUN" in cmd.stdout.getvalue()


def test_exception_in_step_logged_as_failed() -> None:
    from unittest.mock import patch

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", side_effect=RuntimeError("API boom")):
        cmd.handle(only="events")

    assert "FAILED" in cmd.stdout.getvalue()
    assert "API boom" in cmd.stdout.getvalue()


def test_handle_no_only_runs_all_steps() -> None:
    from unittest.mock import patch

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=5) as mock_sync:
        cmd.handle()

    assert mock_sync.call_count == len(SYNC_STEPS)


def test_etag_cache_shared_across_steps() -> None:
    from unittest.mock import patch

    cmd = _make_command()
    received_caches = []

    def capture_cache(**kwargs) -> int:
        received_caches.append(id(kwargs.get("etag_cache")))
        return 0

    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", side_effect=capture_cache):
        cmd.handle()

    assert len(set(received_caches)) == 1


def test_total_saved_count_in_summary() -> None:
    from unittest.mock import patch

    cmd = _make_command()
    with patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=42):
        cmd.handle(only="events")

    assert "42" in cmd.stdout.getvalue()

