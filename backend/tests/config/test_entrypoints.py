import builtins
import importlib
import os
import runpy
import sys
from unittest import mock

import pytest


def _fresh_import(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_manage_main_sets_default_settings_and_executes_command(monkeypatch: pytest.MonkeyPatch) -> None:
    manage = importlib.import_module("manage")
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    monkeypatch.setattr(sys, "argv", ["manage.py", "check"])

    with mock.patch("django.core.management.execute_from_command_line") as execute:
        manage.main()

    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.dev"
    execute.assert_called_once_with(["manage.py", "check"])


def test_manage_main_keeps_existing_settings_module(monkeypatch: pytest.MonkeyPatch) -> None:
    manage = importlib.import_module("manage")
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.test")
    monkeypatch.setattr(sys, "argv", ["manage.py", "check"])

    with mock.patch("django.core.management.execute_from_command_line") as execute:
        manage.main()

    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.test"
    execute.assert_called_once_with(["manage.py", "check"])


def test_manage_main_raises_helpful_error_when_django_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    manage = importlib.import_module("manage")
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "django.core.management":
            raise ImportError("django missing")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(sys, "argv", ["manage.py", "check"])

    with pytest.raises(ImportError, match="Couldn't import Django"):
        manage.main()


def test_manage_module_entrypoint_calls_main(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    monkeypatch.setattr(sys, "argv", ["manage.py", "check"])

    with mock.patch("django.core.management.execute_from_command_line") as execute:
        runpy.run_module("manage", run_name="__main__")

    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.dev"
    execute.assert_called_once_with(["manage.py", "check"])


def test_asgi_sets_default_settings_module_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    fake_application = object()

    with mock.patch("django.core.asgi.get_asgi_application", return_value=fake_application) as get_application:
        module = _fresh_import("config.asgi")

    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.prod"
    assert module.application is fake_application
    get_application.assert_called_once_with()


def test_asgi_keeps_existing_settings_module(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.test")
    fake_application = object()

    with mock.patch("django.core.asgi.get_asgi_application", return_value=fake_application):
        _fresh_import("config.asgi")

    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.test"


def test_wsgi_sets_default_settings_module_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    fake_application = object()

    with mock.patch("django.core.wsgi.get_wsgi_application", return_value=fake_application) as get_application:
        module = _fresh_import("config.wsgi")

    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.prod"
    assert module.application is fake_application
    get_application.assert_called_once_with()


def test_wsgi_keeps_existing_settings_module(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.test")
    fake_application = object()

    with mock.patch("django.core.wsgi.get_wsgi_application", return_value=fake_application):
        _fresh_import("config.wsgi")

    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.test"
