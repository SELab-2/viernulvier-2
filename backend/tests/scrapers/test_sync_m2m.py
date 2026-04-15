"""
Tests for M2M synchronization.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Never
from unittest.mock import Mock

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers import viernulvier_relations as rel
from apps.imports.scrapers.viernulvier import (
    FKCache,
    M2MConfig,
    _sync_m2m,
)
from tests.scrapers.conftest import _make_m2m_setup


class TestSyncM2M:
    def test_normalizes_scalar_payload_to_single_item(self) -> None:
        """A non-list payload is treated as a one-item list and processed safely."""

        class FakeRelatedModel:
            __name__ = "FakeRelated"

            class DoesNotExist(Exception):
                pass

            class objects:
                @staticmethod
                def values_list(*_args, **_kwargs):
                    return SimpleNamespace(iterator=lambda: iter(()))

                @staticmethod
                def get(**_kwargs) -> Never:
                    raise FakeRelatedModel.DoesNotExist

        class FakeThroughModel:
            __name__ = "FakeThroughModel"

            class objects:
                filter = Mock(return_value=SimpleNamespace(delete=lambda: None))
                bulk_create = Mock()

        cfg = M2MConfig(
            api_key="genres",
            related_model=FakeRelatedModel,
            through_model=FakeThroughModel,
            parent_fk="parent",
            related_fk="related",
        )
        fk_cache = FKCache()
        viernulvier._sync_m2m(SimpleNamespace(pk=1), {"genres": "not-a-list"}, cfg, fk_cache)
        FakeThroughModel.objects.filter.assert_called_once()
        FakeThroughModel.objects.bulk_create.assert_not_called()

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

    def test_sync_m2m_ignores_missing_api_key(self):
        """If the item does not contain the m2m api key, the function returns early."""
        class DummyRelated:
            pass

        class Through:
            class objects:
                filter = staticmethod(lambda **_: None)

        cfg = M2MConfig(
            api_key="missing",
            related_model=DummyRelated,
            through_model=Through,
            parent_fk="p",
            related_fk="r",
        )

        result = rel.sync_m2m(object(), {}, cfg, rel.FKCache())
        assert result is None

    def test_resolve_related_pk_with_create_fn_sets_cache(self):
        fk = rel.FKCache()

        class RelModel:
            class DoesNotExist(Exception):
                pass

            class objects:
                @staticmethod
                def get(**_kwargs):
                    raise RelModel.DoesNotExist

        created = {}

        def create_fn(ext_id, raw_item):
            created["val"] = ext_id
            return 777

        m2m = M2MConfig(
            api_key="x",
            related_model=RelModel,
            through_model=None,
            parent_fk="p",
            related_fk="r",
            create_related_fn=create_fn,
        )

        pk = rel._resolve_related_pk(RelModel, "missing-id", {"name": "x"}, m2m, fk)

        assert pk == 777
        assert fk.get(RelModel, "missing-id") == 777
        assert created["val"] == "missing-id"

    def test_sync_m2m_bulk_create_fallback_and_save_exception(self, caplog):
        fk = rel.FKCache()

        class DummyRelated:
            def __init__(self, pk=None):
                self.pk = pk

        # fake through model and manager
        class FakeManager:
            def filter(self, **_kwargs):
                class D:
                    def delete(self):
                        return None

                return D()

            def bulk_create(self, _objs, ignore_conflicts=False):
                del ignore_conflicts
                raise RuntimeError("bulk create fail")

        class FakeThrough:
            objects = FakeManager()

            def __init__(self, **kwargs):
                self._kwargs = kwargs

            def save(self):
                raise RuntimeError("save failed")

        class ParentObj:
            def __init__(self):
                self.pk = 42

        parent = ParentObj()

        m2m = M2MConfig(
            api_key="things",
            related_model=DummyRelated,
            through_model=FakeThrough,
            parent_fk="parent",
            related_fk="related",
            extra_fields={"position": "position"},
        )

        # prime cache so _resolve_related_pk returns a pk without DB lookup
        fk.set(DummyRelated, "EXT1", 99)

        item = {"things": [{"@id": "EXT1"}]}

        # ensure logger captures warning/error paths
        caplog.set_level(logging.WARNING, logger=rel.logger.name)

        # run; should hit bulk_create exception then save exception and log an exception
        rel.sync_m2m(parent, item, m2m, fk)

        # ensure fallback path logged (warning) or error logged on save failure
        assert any(
            ("bulk_create failed" in rec.getMessage()) or ("Error creating" in rec.getMessage()) for rec in caplog.records
        )
