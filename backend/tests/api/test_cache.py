from types import SimpleNamespace

import api.cache as cache_utils
from api.cache import cache_api_view, cache_get_view


def test_cache_get_view_returns_decorator():
    decorator = cache_get_view(60)
    assert callable(decorator)


def test_cache_api_view_decorator_wraps_function():
    def dummy_view(request):
        return "ok"

    dummy_view(None)

    decorator = cache_api_view(60)
    wrapped = decorator(dummy_view)

    assert callable(wrapped)


def test_clear_api_cache_uses_delete_pattern(monkeypatch):
    called = {"pattern": None}

    def fake_delete_pattern(pattern):
        called["pattern"] = pattern
        return 3

    fake_cache = SimpleNamespace(delete_pattern=fake_delete_pattern, clear=lambda: None)

    monkeypatch.setattr(cache_utils, "cache", fake_cache)

    result = cache_utils.clear_api_cache()

    assert result == 3
    assert called["pattern"] == cache_utils.API_CACHE_DELETE_PATTERN


def test_clear_api_cache_falls_back_to_clear_when_delete_pattern_missing(monkeypatch):
    called = {"clear": False}

    def fake_clear():
        called["clear"] = True

    fake_cache = SimpleNamespace(clear=fake_clear)

    monkeypatch.setattr(cache_utils, "cache", fake_cache)

    result = cache_utils.clear_api_cache()

    assert result is None
    assert called["clear"] is True


def test_cache_api_view_returns_callable_decorator():
    def view(request):
        return "ok"

    wrapped = cache_api_view(60)(view)

    assert callable(wrapped)


def test_clear_api_cache_returns_none_when_delete_pattern_fails(monkeypatch):
    def bad_delete_pattern(_pattern):
        raise ConnectionError("redis down")

    fake_cache = SimpleNamespace(delete_pattern=bad_delete_pattern, clear=lambda: None)
    monkeypatch.setattr(cache_utils, "cache", fake_cache)

    result = cache_utils.clear_api_cache()

    assert result is None
