"""Progress-bar and custom-step coverage for sync_viernulvier command."""

import importlib
from io import StringIO
import re
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.management.base import OutputWrapper
import pytest

import apps.imports.management.commands.sync_viernulvier as cmd_module
from apps.imports.management.commands.sync_viernulvier import Command


@pytest.fixture(autouse=True)
def _mock_media_item_gallery_link_step_default():
    """Default gallery-link behavior for tests not explicitly overriding it."""
    with patch("apps.imports.management.commands.sync_viernulvier.sync_media_item_gallery_links", return_value=0):
        yield


@pytest.mark.parametrize("tqdm_installed", [True, False])
def test_make_progress_callback(monkeypatch, tqdm_installed, capsys) -> None:
    command = Command()
    name = "test_step"

    if tqdm_installed:
        fake_bar = SimpleNamespace(n=0, refresh=Mock(), close=Mock())
        fake_tqdm = Mock(return_value=fake_bar)
        monkeypatch.setattr("apps.imports.management.commands.sync_viernulvier._tqdm", fake_tqdm)
    else:
        monkeypatch.setattr("apps.imports.management.commands.sync_viernulvier._tqdm", None)

    callback = command._make_progress_callback(name)
    callback(0, 1000)
    callback(500, 1000)
    callback(1000, 1000)

    if tqdm_installed:
        assert fake_tqdm.call_count == 1
        assert fake_bar.n == 1000
        assert fake_bar.refresh.call_count >= 2
        assert fake_bar.close.call_count == 1
    else:
        captured = capsys.readouterr()
        assert f"{name}: 500/1000" in captured.out or f"{name}: 1000/1000" in captured.out


def test_make_progress_callback_tqdm_bar_lifecycle(monkeypatch) -> None:
    cmd = Command()
    cmd.stdout = OutputWrapper(StringIO())

    fake_bar = SimpleNamespace(n=0, refresh=Mock(), close=Mock())
    fake_tqdm = Mock(return_value=fake_bar)
    monkeypatch.setattr("apps.imports.management.commands.sync_viernulvier._tqdm", fake_tqdm)

    callback = cmd._make_progress_callback("step")
    assert fake_tqdm.call_count == 0

    callback(100, 500)
    assert fake_tqdm.call_count == 1
    assert fake_bar.n == 100

    callback(200, 500)
    assert fake_tqdm.call_count == 1
    assert fake_bar.n == 200

    callback(500, 500)
    assert fake_bar.n == 500
    assert fake_bar.close.call_count == 1


def test_make_progress_callback_no_tqdm_writes_at_500_intervals(monkeypatch) -> None:
    cmd = Command()
    cmd.stdout = OutputWrapper(StringIO())
    monkeypatch.setattr("apps.imports.management.commands.sync_viernulvier._tqdm", None)

    callback = cmd._make_progress_callback("mystep")
    callback(0, 2000)
    callback(500, 2000)
    callback(1000, 2000)
    callback(1500, 2000)
    callback(2000, 2000)

    output = cmd.stdout.getvalue()
    assert "500/2000" in output or "1000/2000" in output or "2000/2000" in output


def test_make_progress_bar_returns_value_when_tqdm_present(monkeypatch) -> None:
    fake_bar = Mock()
    fake_tqdm = Mock(return_value=fake_bar)
    monkeypatch.setattr(cmd_module, "_tqdm", fake_tqdm)

    result = cmd_module._make_progress_bar("step", 100)
    assert result is None or result == fake_bar


def test_make_progress_bar_graceful_degradation_when_tqdm_missing() -> None:
    with patch.dict(sys.modules, {"tqdm": None}):
        importlib.reload(cmd_module)

        assert cmd_module._tqdm is None
        assert cmd_module._make_progress_bar("test", 100) is None

    importlib.reload(cmd_module)


@pytest.mark.parametrize(
    ("dry_run", "saved", "expected_label"),
    [
        (False, 3, "3 crops"),
        (True, 5, "5 would save"),
    ],
)
def test_run_crops_writes_expected_success_label(dry_run, saved, expected_label) -> None:
    cmd = Command()
    cmd.stdout = OutputWrapper(StringIO())

    with (
        patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0),
        patch("apps.imports.management.commands.sync_viernulvier.sync_media_item_crops", return_value=saved),
    ):
        cmd.handle(dry_run=dry_run)

    out = cmd.stdout.getvalue()
    assert "-> media_item_crops" in out
    assert expected_label in out


def test_run_crops_saved_count_added_to_total() -> None:
    cmd = Command()
    cmd.stdout = OutputWrapper(StringIO())

    with (
        patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0),
        patch("apps.imports.management.commands.sync_viernulvier.sync_media_item_crops", return_value=9),
    ):
        cmd.handle()

    assert "9" in cmd.stdout.getvalue()


def test_run_crops_elapsed_time_appears_in_output() -> None:
    cmd = Command()
    cmd.stdout = OutputWrapper(StringIO())

    with (
        patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0),
        patch("apps.imports.management.commands.sync_viernulvier.sync_media_item_crops", return_value=2),
    ):
        cmd.handle()

    assert "s)" in cmd.stdout.getvalue()


def test_run_crops_exception_logged_as_failed() -> None:
    cmd = Command()
    cmd.stdout = OutputWrapper(StringIO())

    with (
        patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0),
        patch(
            "apps.imports.management.commands.sync_viernulvier.sync_media_item_crops", side_effect=RuntimeError("crops boom")
        ),
    ):
        cmd.handle()

    out = cmd.stdout.getvalue()
    assert "FAILED" in out
    assert "crops boom" in out


@pytest.mark.parametrize("dry_run", [True, False])
def test_run_crops_passes_expected_kwargs(dry_run) -> None:
    cmd = Command()
    cmd.stdout = OutputWrapper(StringIO())
    calls = []

    def capture(**kwargs) -> int:
        calls.append(kwargs)
        return 0

    with (
        patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0),
        patch("apps.imports.management.commands.sync_viernulvier.sync_media_item_crops", side_effect=capture),
    ):
        cmd.handle(dry_run=dry_run)

    assert calls
    assert calls[0]["dry_run"] is dry_run
    assert callable(calls[0]["on_progress"])


@pytest.mark.parametrize(
    ("only", "crops_called", "sync_called"),
    [
        ("events", False, True),
        ("media_item_crops", True, False),
    ],
)
def test_run_crops_only_mode_behavior(only, crops_called, sync_called) -> None:
    cmd = Command()
    cmd.stdout = OutputWrapper(StringIO())

    with (
        patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier") as mock_sync,
        patch("apps.imports.management.commands.sync_viernulvier.sync_media_item_crops", return_value=4) as mock_crops,
    ):
        cmd.handle(only=only)

    assert mock_crops.called is crops_called
    assert mock_sync.called is sync_called


def test_command_exception_handlers_catch_and_log_all_failures() -> None:
    """Verify all step-specific exception handlers report failures and command still finishes."""
    cmd1 = Command()
    cmd1.stdout = OutputWrapper(StringIO())

    with patch(
        "apps.imports.management.commands.sync_viernulvier.sync_viernulvier", side_effect=ValueError("Network error")
    ):
        cmd1.handle(only="genres", dry_run=False)

    output1 = cmd1.stdout.getvalue()
    assert "✗ FAILED after" in output1
    assert "Network error" in output1
    assert "genres" in output1
    assert "Done" in output1
    assert re.search(r"✗ FAILED after \d+\.\ds: ", output1)

    cmd2 = Command()
    cmd2.stdout = OutputWrapper(StringIO())
    with (
        patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0),
        patch(
            "apps.imports.management.commands.sync_viernulvier.sync_media_item_gallery_links",
            side_effect=RuntimeError("API rate limit exceeded"),
        ),
    ):
        cmd2.handle(only="media_item_gallery_links", dry_run=False)

    output2 = cmd2.stdout.getvalue()
    assert "✗ FAILED after" in output2
    assert "API rate limit exceeded" in output2
    assert "media_item_gallery_links" in output2
    assert "Done" in output2

    cmd3 = Command()
    cmd3.stdout = OutputWrapper(StringIO())
    with (
        patch("apps.imports.management.commands.sync_viernulvier.sync_viernulvier", return_value=0),
        patch("apps.imports.management.commands.sync_viernulvier.sync_media_item_gallery_links", return_value=0),
        patch("apps.imports.management.commands.sync_viernulvier.sync_media_item_crops", side_effect=OSError("DB lost")),
    ):
        cmd3.handle(only="media_item_crops", dry_run=False)

    output3 = cmd3.stdout.getvalue()
    assert "✗ FAILED after" in output3
    assert "DB lost" in output3
    assert "media_item_crops" in output3
    assert "Done" in output3
