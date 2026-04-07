"""
Shared fixtures and helpers for scraper tests.
"""

from __future__ import annotations

import builtins
from contextlib import contextmanager
from decimal import Decimal
import datetime
from types import SimpleNamespace
from typing import Never
from unittest.mock import Mock

from django.db import connection, models
import pytest

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import FKCache, ModelSyncConfig


# ---------------------------------------------------------------------------
# Mock Session Helpers
# ---------------------------------------------------------------------------


def _mock_build_session(monkeypatch, response_sequence=None, *, raise_exc=None):
    """
    Replace _build_session so that session.get returns controlled responses.

    response_sequence: list of (status_code, data) tuples, consumed in order.
    If the list is exhausted the last entry is repeated (handles retry loops).
    raise_exc: if given, session.get raises this exception on every call.
    """
    if response_sequence is None:
        response_sequence = [(200, [])]

    call_index = [0]

    def _make_response(status, data):
        r = Mock()
        r.status_code = status
        r.ok = status < 400
        r.headers = Mock()
        r.headers.get = Mock(return_value=None)
        if isinstance(data, Exception):
            r.json.side_effect = data
        else:
            r.json.return_value = data
        return r

    def fake_build_session():
        session = Mock()

        def fake_get(url, params=None, headers=None, timeout=None):
            if raise_exc is not None:
                raise raise_exc
            idx = min(call_index[0], len(response_sequence) - 1)
            status, data = response_sequence[idx]
            call_index[0] += 1
            return _make_response(status, data)

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)
    monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)

    return call_index


def _make_ok_response(data, etag=None):
    r = Mock()
    r.status_code = 200
    r.ok = True
    r.headers = Mock()
    r.headers.get = Mock(return_value=etag)
    r.json.return_value = data
    return r


def _make_status_response(status, headers=None):
    r = Mock()
    r.status_code = status
    r.ok = status < 400
    r.headers = Mock()
    header_dict = headers or {}
    r.headers.get = lambda k, d=None: header_dict.get(k, d)
    return r


def _mock_session(monkeypatch, responses_fn):
    """responses_fn(url, call_count) -> Mock response or raise."""
    call_count = [0]
    monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)

    def fake_build_session():
        session = Mock()

        def fake_get(url, params=None, headers=None, timeout=None):
            call_count[0] += 1
            return responses_fn(url, call_count[0])

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)
    return call_count


# ---------------------------------------------------------------------------
# Model and Config Helpers
# ---------------------------------------------------------------------------


@contextmanager
def _temp_viernulvier_model():
    """Create a temporary in-memory model for sync tests with automatic cleanup."""

    class ViernulvierItem(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        title = models.CharField(max_length=255, null=True, blank=True)
        description = models.TextField(null=True, blank=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(ViernulvierItem)
    try:
        yield ViernulvierItem
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(ViernulvierItem)


class _PassThroughConfig(ModelSyncConfig):
    """Minimal config that maps '@id' as the lookup key (default api_id_key)."""

    def __init__(self) -> None:
        super().__init__(lookup_field="id")


# ---------------------------------------------------------------------------
# Translation Model Helper
# ---------------------------------------------------------------------------


def _fake_trans_model(call_log):
    class FakeMeta:
        def get_field(self, name):
            return models.CharField(name=name, max_length=255)

    class FakeManager:
        def update_or_create(self, **kwargs):
            call_log.append(kwargs)
            return (Mock(), True)

    class FakeTrans:
        __name__ = "FakeTrans"
        _meta = FakeMeta()
        objects = FakeManager()

    return FakeTrans


# ---------------------------------------------------------------------------
# M2M Setup Helper
# ---------------------------------------------------------------------------


def _make_m2m_setup():
    created_rows = []

    class FakeRelated:
        __name__ = "FakeRelated"
        DoesNotExist = Exception

        def __init__(self, pk=None) -> None:
            self.pk = pk

    class FakeThrough:
        __name__ = "FakeThrough"

        def __init__(self, **kwargs) -> None:
            created_rows.append(dict(kwargs))

        class objects:
            @staticmethod
            def filter(**_):
                return SimpleNamespace(delete=lambda: None)

    return FakeRelated, FakeThrough, created_rows


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_build_session_helper(monkeypatch):
    """Fixture providing _mock_build_session helper."""
    return lambda *args, **kwargs: _mock_build_session(monkeypatch, *args, **kwargs)


@pytest.fixture
def mock_session_helper(monkeypatch):
    """Fixture providing _mock_session helper."""
    return lambda fn: _mock_session(monkeypatch, fn)


@pytest.fixture
def temp_viernulvier_model():
    """Fixture providing temporary model context manager."""
    return _temp_viernulvier_model


@pytest.fixture
def fake_trans_model_fixture():
    """Fixture for creating fake translation models."""
    return _fake_trans_model


@pytest.fixture
def m2m_setup_fixture():
    """Fixture for M2M test setup."""
    return _make_m2m_setup

