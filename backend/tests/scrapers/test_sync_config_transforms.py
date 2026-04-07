"""Focused tests for sync_viernulvier value/filter transform helpers."""

import pytest

from apps.genres.models import GenreUseAs
from apps.imports.management.commands.sync_viernulvier import (
    _is_not_longterm,
    _resolve_genre_use_as,
    nee_ja_to_bool,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ja", True),
        ("JA", True),
        ("  ja  ", True),
        ("true", True),
        ("yes", True),
        ("1", True),
        ("TRUE", True),
        (" YES ", True),
        (" 1 ", True),
        ("nee", False),
        ("NEE", False),
        ("  nee  ", False),
        ("false", False),
        ("no", False),
        ("0", False),
        ("FALSE", False),
        (" NO ", False),
        (" 0 ", False),
        ("", False),
        ("   ", False),
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (42, True),
        (-1, True),
        (None, False),
        ([], False),
        ([1, 2], True),
        ({}, False),
        ({"x": 1}, True),
    ],
)
def test_nee_ja_to_bool(value, expected) -> None:
    """nee_ja_to_bool should support nl/en strings, bools, ints, and fallback coercion."""
    assert nee_ja_to_bool(value) is expected


@pytest.mark.django_db
def test_resolve_genre_use_as_creates_new() -> None:
    """When no matching row exists, _resolve_genre_use_as creates one."""
    pk = _resolve_genre_use_as("test_genre")
    assert pk is not None
    assert GenreUseAs.objects.filter(pk=pk, name="test_genre").exists()


@pytest.mark.django_db
def test_resolve_genre_use_as_returns_existing() -> None:
    """When a matching row exists, _resolve_genre_use_as returns its pk."""
    existing = GenreUseAs.objects.create(name="existing_genre")
    pk = _resolve_genre_use_as("existing_genre")

    assert pk == existing.pk
    assert GenreUseAs.objects.filter(name="existing_genre").count() == 1


@pytest.mark.django_db
def test_resolve_genre_use_as_handles_none() -> None:
    """None input resolves to the default 'unknown' row."""
    pk = _resolve_genre_use_as(None)
    assert pk is not None
    assert GenreUseAs.objects.filter(pk=pk, name="unknown").exists()


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"production": {"@id": "/api/v1/productions/123"}}, True),
        ({"production": {"@id": "/api/v1/longterm/456"}}, False),
        ({"production": "/api/v1/productions/99"}, True),
        ({"production": "/api/v1/longterm/99"}, False),
        ({}, True),
        ({"production": None}, True),
    ],
)
def test_is_not_longterm(payload, expected) -> None:
    """_is_not_longterm should only reject payloads pointing to /longterm/ productions."""
    assert _is_not_longterm(payload) is expected

