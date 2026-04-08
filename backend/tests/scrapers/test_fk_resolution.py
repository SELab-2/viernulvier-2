"""
Tests for FK resolution, FK caching, and lookup value extraction.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Never

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    FKCache,
    ModelSyncConfig,
    _extract_lookup_value,
    _resolve_fk,
)

# ---------------------------------------------------------------------------
# _extract_external_id_from_url
# ---------------------------------------------------------------------------


def test_extract_external_id_handles_int() -> None:
    assert viernulvier._extract_external_id_from_url(42) == "42"
    assert viernulvier._extract_external_id_from_url(123) == "123"


def test_extract_external_id_handles_dict_at_id() -> None:
    assert viernulvier._extract_external_id_from_url({"@id": "/api/v1/x"}) == "/api/v1/x"


def test_extract_external_id_handles_dict_external_id_fallback() -> None:
    assert viernulvier._extract_external_id_from_url({"external_id": "test123"}) == "test123"


def test_extract_external_id_handles_dict_id_fallback() -> None:
    assert viernulvier._extract_external_id_from_url({"id": "test456"}) == "test456"


def test_extract_external_id_handles_blank_string() -> None:
    assert viernulvier._extract_external_id_from_url("   ") is None


def test_extract_external_id_handles_none() -> None:
    assert viernulvier._extract_external_id_from_url(None) is None


def test_extract_external_id_handles_empty_dict() -> None:
    assert viernulvier._extract_external_id_from_url({}) is None


def test_extract_external_id_handles_list() -> None:
    assert viernulvier._extract_external_id_from_url([]) is None


def test_extract_external_id_handles_dict_all_none_values() -> None:
    assert viernulvier._extract_external_id_from_url({"foo": "bar"}) is None


def test_extract_external_id_non_string_non_int_non_dict_returns_none() -> None:
    assert viernulvier._extract_external_id_from_url(3.14) is None


# ---------------------------------------------------------------------------
# _extract_lookup_value
# ---------------------------------------------------------------------------


def test_extract_lookup_value_uses_api_id_key() -> None:
    config = ModelSyncConfig(api_id_key="@id")
    assert _extract_lookup_value({"@id": "val"}, config) == "val"


def test_extract_lookup_value_falls_back_to_external_id() -> None:
    config = ModelSyncConfig(api_id_key="@id")
    assert _extract_lookup_value({"external_id": "ext123"}, config) == "ext123"


def test_extract_lookup_value_falls_back_to_id() -> None:
    config = ModelSyncConfig(api_id_key="@id")
    assert _extract_lookup_value({"id": "test123"}, config) == "test123"


def test_extract_lookup_value_unwraps_nested_dict() -> None:
    config = ModelSyncConfig(api_id_key="@id")
    assert _extract_lookup_value({"external_id": {"id": "x-1"}}, config) == "x-1"
    assert _extract_lookup_value({"@id": {"@id": "nested123"}}, config) == "nested123"


def test_extract_lookup_value_strips_whitespace() -> None:
    config = ModelSyncConfig(api_id_key="@id")
    assert _extract_lookup_value({"@id": "  value  "}, config) == "value"


def test_extract_lookup_value_returns_none_on_missing() -> None:
    config = ModelSyncConfig(api_id_key="@id")
    assert _extract_lookup_value({}, config) is None


# ---------------------------------------------------------------------------
# _resolve_fk
# ---------------------------------------------------------------------------


def test_resolve_fk_returns_pk_on_cache_hit() -> None:
    """Cache hit returns the PK directly without hitting the DB."""

    class FakeRelatedModel:
        __name__ = "FakeRelated"

        class DoesNotExist(Exception):
            pass

    field = SimpleNamespace(remote_field=SimpleNamespace(model=FakeRelatedModel))
    fk_cache = FKCache()
    fk_cache.set(FakeRelatedModel, "rel-1", 77)

    assert _resolve_fk(field, "rel-1", fk_cache) == 77


def test_resolve_fk_returns_none_for_none_input() -> None:
    field = SimpleNamespace(remote_field=SimpleNamespace(model=object))
    fk_cache = FKCache()
    assert _resolve_fk(field, None, fk_cache) is None


def test_resolve_fk_warns_on_missing_related(caplog) -> None:
    """Missing FK logs a warning and returns None."""

    class FakeDoesNotExist(Exception):
        pass

    class FakeValuesList:
        def get(self, _=None, **__) -> Never:
            raise FakeRelatedModel.DoesNotExist

    class FakeRelatedModel:
        __name__ = "FakeRelated"
        DoesNotExist = FakeDoesNotExist

        class objects:
            @staticmethod
            def values_list(*_args, **_kwargs):
                return FakeValuesList()

    field = SimpleNamespace(remote_field=SimpleNamespace(model=FakeRelatedModel))
    fk_cache = FKCache()
    fk_cache._loaded[FakeRelatedModel] = True

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    result = _resolve_fk(field, "missing", fk_cache)

    assert result is None
    assert any("FK not found" in r.message for r in caplog.records)


def test_resolve_fk_logs_error_on_unexpected_exception(caplog) -> None:
    """Unexpected exceptions are logged as errors and None is returned."""

    class FakeValuesList:
        def get(self, **_) -> Never:
            raise RuntimeError("boom")

    class FakeRelatedModel:
        __name__ = "FakeRelated"

        class DoesNotExist(Exception):
            pass

        class objects:
            @staticmethod
            def values_list(*_args, **_kwargs):
                return FakeValuesList()

    field = SimpleNamespace(remote_field=SimpleNamespace(model=FakeRelatedModel))
    fk_cache = FKCache()
    fk_cache._loaded[FakeRelatedModel] = True

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = _resolve_fk(field, "error", fk_cache)

    assert result is None
    assert any("Error resolving FK" in r.message for r in caplog.records)


def test_resolve_fk_db_hit_populates_cache() -> None:
    """Successful DB lookup on cache miss stores the result in the cache."""

    class FakeValuesList:
        def get(self, _=None, **__) -> int:
            return 42

    class FakeRelatedModel:
        __name__ = "FakeRelated"

        class DoesNotExist(Exception):
            pass

        class objects:
            @staticmethod
            def values_list(*_args, **_kwargs):
                return FakeValuesList()

    field = SimpleNamespace(remote_field=SimpleNamespace(model=FakeRelatedModel))
    fk_cache = FKCache()
    fk_cache._loaded[FakeRelatedModel] = True

    result = _resolve_fk(field, "ext-42", fk_cache)
    assert result == 42
    # Second call hits cache
    assert fk_cache.get(FakeRelatedModel, "ext-42") == 42


# ---------------------------------------------------------------------------
# FKCache
# ---------------------------------------------------------------------------


class TestFKCache:
    def _make_queryable(self, rows):
        class QS:
            def iterator(self):
                return iter(rows)

        class M:
            __name__ = "M"

            class objects:
                @staticmethod
                def values_list(*_, **__):
                    return QS()

        return M

    def test_warmup_populates_cache(self) -> None:
        M = self._make_queryable([("ext-1", 1), ("ext-2", 2)])
        cache = FKCache()
        cache.warmup(M)
        assert cache._loaded[M] is True
        assert cache.get(M, "ext-1") == 1
        assert cache.get(M, "ext-2") == 2

    def test_warmup_skipped_on_second_call(self) -> None:
        call_count = [0]

        class QS:
            def iterator(self):
                call_count[0] += 1
                return iter([])

        class M:
            __name__ = "M"

            class objects:
                @staticmethod
                def values_list(*_, **__):
                    return QS()

        cache = FKCache()
        cache.warmup(M)
        cache.warmup(M)
        assert call_count[0] == 1

    def test_warmup_failure_marks_loaded_false(self, caplog) -> None:
        class QS:
            def iterator(self) -> Never:
                raise RuntimeError("no external_id")

        class M:
            __name__ = "NoExtId"

            class objects:
                @staticmethod
                def values_list(*_, **__):
                    return QS()

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        cache = FKCache()
        cache.warmup(M)
        assert cache._loaded[M] is False

    def test_warmup_failure_not_retried(self) -> None:
        call_count = [0]

        class QS:
            def iterator(self) -> Never:
                call_count[0] += 1
                raise RuntimeError("boom")

        class M:
            __name__ = "Bad"

            class objects:
                @staticmethod
                def values_list(*_, **__):
                    return QS()

        cache = FKCache()
        cache.warmup(M)
        cache.warmup(M)
        assert call_count[0] == 1

    def test_set_then_get_returns_value(self) -> None:
        cache = FKCache()

        class M:
            __name__ = "M"

        cache._loaded[M] = True
        cache.set(M, "ext-99", 99)
        assert cache.get(M, "ext-99") == 99

    def test_get_returns_none_on_miss(self) -> None:
        cache = FKCache()

        class M:
            __name__ = "M"

        cache._loaded[M] = True
        assert cache.get(M, "nonexistent") is None
