"""
Tests for M2M synchronization.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Never
from unittest.mock import Mock

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    FKCache,
    M2MConfig,
    _sync_m2m,
)
from tests.scrapers.conftest import _make_m2m_setup


class TestSyncM2M:
    def test_returns_early_when_payload_is_not_list(self) -> None:
        """_sync_m2m does nothing if the API value for the key is not a list."""
        through_model = Mock()
        cfg = M2MConfig(
            api_key="genres",
            related_model=Mock(),
            through_model=through_model,
            parent_fk="parent",
            related_fk="related",
        )
        fk_cache = FKCache()
        viernulvier._sync_m2m(SimpleNamespace(pk=1), {"genres": "not-a-list"}, cfg, fk_cache)
        through_model.objects.filter.assert_not_called()

    def test_warns_when_related_object_not_found(self, caplog) -> None:
        """A missing related object is skipped with a warning."""

        class FakeDoesNotExist(Exception):
            pass

        class FakeRelatedModel:
            __name__ = "FakeRelated"
            DoesNotExist = FakeDoesNotExist

            class objects:
                @staticmethod
                def get(**_kwargs) -> Never:
                    raise FakeRelatedModel.DoesNotExist

        class FakeThroughModel:
            __name__ = "FakeThroughModel"

            class objects:
                @staticmethod
                def filter(**_kw):
                    return SimpleNamespace(delete=lambda: None)

        cfg = M2MConfig(
            api_key="items",
            related_model=FakeRelatedModel,
            through_model=FakeThroughModel,
            parent_fk="parent",
            related_fk="related",
        )
        fk_cache = FKCache()
        fk_cache._loaded[FakeRelatedModel] = True

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        viernulvier._sync_m2m(SimpleNamespace(pk=1), {"items": ["ext-missing"]}, cfg, fk_cache)
        assert any("not found" in r.message for r in caplog.records)

    def test_logs_error_on_bulk_create_fallback_failure(self, caplog) -> None:
        """When bulk_create fails and individual save also fails, an error is logged."""

        class FakeRelatedModel:
            __name__ = "FakeRelated"

            class DoesNotExist(Exception):
                pass

            def __init__(self, **kwargs) -> None:
                self._kwargs = kwargs
                self.pk = kwargs.get("pk", 1)

        created_objs = []

        class FakeThroughModel:
            __name__ = "FakeThroughModel"

            def __init__(self, **kwargs) -> None:
                self._kwargs = kwargs
                created_objs.append(self)

            def save(self) -> Never:
                raise RuntimeError("save failed")

            class objects:
                @staticmethod
                def filter(**_kw):
                    return SimpleNamespace(delete=lambda: None)

        cfg = M2MConfig(
            api_key="items",
            related_model=FakeRelatedModel,
            through_model=FakeThroughModel,
            parent_fk="parent",
            related_fk="related",
        )
        fk_cache = FKCache()
        fk_cache._loaded[FakeRelatedModel] = True
        fk_cache.set(FakeRelatedModel, "ext-1", 1)

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        viernulvier._sync_m2m(SimpleNamespace(pk=1), {"items": ["ext-1"]}, cfg, fk_cache)
        assert any("Error creating" in r.message for r in caplog.records)

    def test_extra_fields_from_dict_item_applied(self) -> None:
        """position field in dict item is stored in the through row."""
        fake_related, fake_through, rows = _make_m2m_setup()
        cache = FKCache()
        cache._loaded[fake_related] = True
        cache.set(fake_related, "ext-1", 1)

        cfg = M2MConfig(
            api_key="genres",
            related_model=fake_related,
            through_model=fake_through,
            parent_fk="production",
            related_fk="genre",
            extra_fields={"position": "position"},
        )
        _sync_m2m(
            SimpleNamespace(pk=10),
            {"genres": [{"@id": "ext-1", "position": 7}]},
            cfg,
            cache,
        )
        assert rows[0]["position"] == 7

    def test_position_auto_filled_from_index_for_url_strings(self) -> None:
        """When raw item is a plain string, position is the list index."""
        fake_related, fake_through, rows = _make_m2m_setup()
        cache = FKCache()
        cache._loaded[fake_related] = True
        cache.set(fake_related, "ext-A", 10)
        cache.set(fake_related, "ext-B", 20)

        cfg = M2MConfig(
            api_key="genres",
            related_model=fake_related,
            through_model=fake_through,
            parent_fk="production",
            related_fk="genre",
            extra_fields={"position": "position"},
        )
        _sync_m2m(
            SimpleNamespace(pk=10),
            {"genres": ["ext-A", "ext-B"]},
            cfg,
            cache,
        )
        assert rows[0]["position"] == 0
        assert rows[1]["position"] == 1

    def test_empty_ext_id_items_skipped(self) -> None:
        """None / empty string / empty dict items are skipped."""
        bulk_called = [False]
        fake_related, _, _ = _make_m2m_setup()

        class FT:
            __name__ = "FT"

            class objects:
                @staticmethod
                def filter(**_):
                    return SimpleNamespace(delete=lambda: None)

        cache = FKCache()
        cache._loaded[fake_related] = True

        cfg = M2MConfig(
            api_key="items",
            related_model=fake_related,
            through_model=FT,
            parent_fk="prod",
            related_fk="rel",
        )
        _sync_m2m(
            SimpleNamespace(pk=1),
            {"items": [None, "", {}]},
            cfg,
            cache,
        )
        assert not bulk_called[0]

    def test_cache_miss_triggers_db_lookup(self) -> None:
        """Cache miss falls back to DB and populates cache on success."""

        class FR:
            __name__ = "FR"
            DoesNotExist = Exception

            def __init__(self, pk=None) -> None:
                self.pk = pk

            class objects:
                @staticmethod
                def get(**_):
                    return SimpleNamespace(pk=99)

        created_rows = []

        class FT:
            __name__ = "FT"

            def __init__(self, **kw) -> None:
                created_rows.append(kw)

            class objects:
                @staticmethod
                def filter(**_):
                    return SimpleNamespace(delete=lambda: None)

        cache = FKCache()
        cache._loaded[FR] = True

        cfg = M2MConfig(
            api_key="items",
            related_model=FR,
            through_model=FT,
            parent_fk="prod",
            related_fk="rel",
        )
        _sync_m2m(SimpleNamespace(pk=1), {"items": ["ext-miss"]}, cfg, cache)
        assert created_rows
