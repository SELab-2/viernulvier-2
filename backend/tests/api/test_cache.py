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


def make_request(path="/api/v1/test/", lang=""):
    return SimpleNamespace(
        method="GET",
        META={"HTTP_ACCEPT_LANGUAGE": lang},
        get_full_path=lambda: path,
    )


def test_cache_api_view_returns_cached_response(monkeypatch):
    """Cache hit: view should not be called."""
    cached_response = SimpleNamespace(status_code=200)
    fake_cache = SimpleNamespace(
        get=lambda _key: cached_response,
        set=lambda *_a, **_kw: None,
    )
    monkeypatch.setattr(cache_utils, "cache", fake_cache)

    call_count = {"n": 0}

    def view(self, request, *args, **kwargs):
        call_count["n"] += 1
        return SimpleNamespace(status_code=200)

    wrapped = cache_api_view(60)(view)
    result = wrapped(None, make_request())

    assert result is cached_response
    assert call_count["n"] == 0


def test_cache_api_view_stores_response_on_miss(monkeypatch):
    """Cache miss: view is called and response is stored."""
    stored = {}
    fake_cache = SimpleNamespace(
        get=lambda _key: None,
        set=lambda key, value, _timeout: stored.update({"key": key, "value": value}),
    )
    monkeypatch.setattr(cache_utils, "cache", fake_cache)

    response = SimpleNamespace(status_code=200)

    def view(self, request, *args, **kwargs):
        return response

    wrapped = cache_api_view(60)(view)
    result = wrapped(None, make_request())

    assert result is response
    assert stored["value"] is response
    assert stored["key"].startswith("api:GET:")


def test_cache_api_view_falls_back_on_read_error(monkeypatch):
    """Exception during cache read: view is called without caching."""

    def bad_get(key):
        raise ConnectionError("redis down")

    fake_cache = SimpleNamespace(get=bad_get, set=lambda *_a, **_kw: None)
    monkeypatch.setattr(cache_utils, "cache", fake_cache)

    response = SimpleNamespace(status_code=200)

    def view(self, request, *args, **kwargs):
        return response

    wrapped = cache_api_view(60)(view)
    result = wrapped(None, make_request())

    assert result is response


def test_cache_api_view_continues_on_write_error(monkeypatch):
    """Exception during cache write: response is still returned."""

    def bad_set(*args, **kwargs):
        raise ConnectionError("redis down")

    fake_cache = SimpleNamespace(get=lambda _key: None, set=bad_set)
    monkeypatch.setattr(cache_utils, "cache", fake_cache)

    response = SimpleNamespace(status_code=200)

    def view(self, request, *args, **kwargs):
        return response

    wrapped = cache_api_view(60)(view)
    result = wrapped(None, make_request())

    assert result is response
