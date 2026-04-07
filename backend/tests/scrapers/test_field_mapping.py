"""
Tests for field mapping, defaults building, and flexible configuration.
"""

from __future__ import annotations

import datetime
import logging

from django.db import connection, models
from django.test.utils import isolate_apps
import pytest

from apps.events.models import Event, EventPrice
from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    FKCache,
    ModelSyncConfig,
    _build_defaults,
    _parse_field_value,
)
from apps.pricing.models import PriceRank
from apps.productions.models import Production
from tests.scrapers.conftest import _PassThroughConfig

# ---------------------------------------------------------------------------
# Flexible Field Mapping and Parsing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFlexibleFieldMapping:
    def test_throws_no_error_for_year_minus_one_date(self) -> None:
        """Negative-year datetime strings are repaired and parsed."""
        field = Event._meta.get_field("starts_at")
        result = _parse_field_value(field, "-0001-01-01T00:00:00+00:00")

        assert result == datetime.datetime(1, 1, 1, 0, 0, 0, tzinfo=datetime.UTC)

    def test_throws_no_error_for_year_zero_date(self) -> None:
        """Year-0000 datetime strings are repaired to 1970."""
        field = Event._meta.get_field("starts_at")
        result = _parse_field_value(field, "0000-01-01T00:00:00+00:00")

        assert result == datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.UTC)

    def test_returns_none_for_missing_value(self) -> None:
        """None value for a DateTimeField returns None, not an error."""

        field = Event._meta.get_field("starts_at")
        assert _parse_field_value(field, None) is None

    def test_skips_unknown_fields_event_price(self) -> None:
        """Unknown API fields are silently ignored."""

        prod = Production.objects.create(external_id="/api/productions/1")
        event = Event.objects.create(external_id="1", production=prod)
        price_rank = PriceRank.objects.create(external_id="1", position=1)

        item = {
            "external_id": "/api/event_prices/1",
            "event": event.external_id,
            "priceRank": price_rank.external_id,
            "amount": "25.50",
            "available": 100,
            "unknownField": "should be ignored",
            "anotherUnknownField": 123,
            "yetAnotherField": {"nested": "object"},
        }
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(EventPrice, item, _PassThroughConfig(), fk_cache)

        assert "event_id" in defaults
        assert "price_rank_id" in defaults
        assert "amount" in defaults
        assert "available" in defaults
        assert "unknownField" not in defaults
        assert "unknown_field" not in defaults
        assert "anotherUnknownField" not in defaults
        assert "another_unknown_field" not in defaults

    def test_handles_known_fields_correctly(self) -> None:
        """Known FK and scalar fields are resolved and placed in defaults."""

        prod = Production.objects.create(external_id="/api/productions/3")
        event = Event.objects.create(external_id="3", production=prod)
        price_rank = PriceRank.objects.create(external_id="3", position=3)

        item = {
            "external_id": "/api/event_prices/3",
            "event": event.external_id,
            "priceRank": price_rank.external_id,
            "amount": "20.00",
            "available": 75,
        }
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(EventPrice, item, _PassThroughConfig(), fk_cache)

        assert "price_rank_id" in defaults
        assert "event_id" in defaults
        assert "amount" in defaults


# ---------------------------------------------------------------------------
# _build_defaults
# ---------------------------------------------------------------------------


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_explicit_mapping_pk_skip_fk_and_transform() -> None:
    """Explicit field_map: missing values, unknown field, PK skip, FK resolver, transform."""

    class DefaultsModel(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        title = models.CharField(max_length=255, null=True)
        parent = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(DefaultsModel)
    try:
        config = ModelSyncConfig(
            field_map={
                "missing_key": "title",
                "unknown_model_field": "does_not_exist",
                "pk_field": "id",
                "dict_translation": "title",
                "fk_custom": "parent",
                "title_field": "title",
            },
            value_transforms={"title": lambda v: str(v).upper()},
            fk_resolvers={"parent": lambda raw: 99 if raw else None},
            lookup_field="id",
        )

        item = {
            "pk_field": "item-1",
            "dict_translation": {"nl": "Titel"},
            "fk_custom": "/api/v1/parents/99",
            "title_field": "hello",
        }
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(DefaultsModel, item, config, fk_cache)

        assert defaults["parent_id"] == 99
        assert defaults["title"] == "HELLO"
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DefaultsModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_uses_auto_fk_resolver(monkeypatch) -> None:
    """Without a custom fk_resolver, the default _resolve_fk branch is used."""

    class AutoFkModel(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        parent = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(AutoFkModel)
    try:
        monkeypatch.setattr(viernulvier, "_resolve_fk", lambda _field, _raw, _cache: 123)

        config = ModelSyncConfig(field_map={"fk_auto": "parent"}, lookup_field="id")
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(
            AutoFkModel,
            {"fk_auto": "/api/v1/parents/123"},
            config,
            fk_cache,
        )

        assert defaults["parent_id"] == 123
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(AutoFkModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_auto_mapping_skips_at_keys_and_none() -> None:
    """Auto-mapping skips @ keys, None values, and maps scalar fields."""

    class AutoMapModel(models.Model):
        id = models.CharField(max_length=255, primary_key=True)
        title = models.CharField(max_length=255, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(AutoMapModel)
    try:
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(
            AutoMapModel,
            {"@id": "x", "title": "mapped", "unused": None},
            ModelSyncConfig(lookup_field="id"),
            fk_cache,
        )

        assert defaults == {"title": "mapped"}
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(AutoMapModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_skips_none_field_map_value() -> None:
    """field_map entry with None value explicitly skips that API key."""

    class TestModel(models.Model):
        name = models.CharField(max_length=100)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(TestModel)
    try:
        config = ModelSyncConfig(
            field_map={"api_name": None},
            lookup_field="external_id",
        )
        fk_cache = FKCache()
        defaults = viernulvier._build_defaults(TestModel, {"api_name": "should_be_ignored"}, config, fk_cache)
        assert "name" not in defaults
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(TestModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_auto_maps_camel_case() -> None:
    """Auto-mapping converts camelCase API keys to snake_case field names."""

    class CamelModel(models.Model):
        my_field = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(CamelModel)
    try:
        defaults = _build_defaults(
            CamelModel,
            {"myField": "hello"},
            ModelSyncConfig(),
            FKCache(),
        )
        assert defaults.get("my_field") == "hello"
    finally:
        with connection.schema_editor() as se:
            se.delete_model(CamelModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_auto_map_skips_list_values() -> None:
    """Auto-mapping skips list values (they are handled via M2M configs)."""

    class LModel(models.Model):
        title = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(LModel)
    try:
        defaults = _build_defaults(
            LModel,
            {"title": "ok", "genres": ["url1", "url2"]},
            ModelSyncConfig(),
            FKCache(),
        )
        assert "title" in defaults
        assert "genres" not in defaults
    finally:
        with connection.schema_editor() as se:
            se.delete_model(LModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_explicit_map_dict_value_for_non_relation_skipped() -> None:
    """A flat-dict value for a non-relation field in field_map is skipped (it's a translation)."""

    class TModel(models.Model):
        title = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(TModel)
    try:
        config = ModelSyncConfig(field_map={"title_dict": "title"})
        defaults = _build_defaults(
            TModel,
            {"title_dict": {"nl": "Titel", "en": "Title"}},
            config,
            FKCache(),
        )
        assert "title" not in defaults
    finally:
        with connection.schema_editor() as se:
            se.delete_model(TModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_skips_field_map_key_missing_from_item() -> None:
    """When a field_map key is not present in the API item, it is silently skipped."""

    class MissingKeyModel(models.Model):
        title = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(MissingKeyModel)
    try:
        config = ModelSyncConfig(field_map={"absent_key": "title"}, lookup_field="id")
        defaults = _build_defaults(MissingKeyModel, {}, config, FKCache())
        assert "title" not in defaults
    finally:
        with connection.schema_editor() as se:
            se.delete_model(MissingKeyModel)


@isolate_apps("tests")
@pytest.mark.django_db(transaction=True)
def test_build_defaults_logs_warning_for_nonexistent_field(caplog) -> None:
    """FieldDoesNotExist in field_map logs a warning and skips that entry."""

    class SimpleModel(models.Model):
        title = models.CharField(max_length=100, null=True)

        class Meta:
            app_label = "tests"

    with connection.schema_editor() as se:
        se.create_model(SimpleModel)
    try:
        config = ModelSyncConfig(
            field_map={
                "api_title": "title",
                "api_ghost": "does_not_exist_on_model",
            },
            lookup_field="id",
        )
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        defaults = _build_defaults(
            SimpleModel,
            {"api_title": "hello", "api_ghost": "ignored"},
            config,
            FKCache(),
        )

        assert defaults.get("title") == "hello"
        assert any("does_not_exist_on_model" in r.message and "does not exist" in r.message for r in caplog.records)
    finally:
        with connection.schema_editor() as se:
            se.delete_model(SimpleModel)
