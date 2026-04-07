"""
Tests for translation synchronization.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Never

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from unittest.mock import Mock
import pytest

from apps.imports.scrapers.viernulvier import (
    TranslationConfig,
    _sync_all_translations,
)
from apps.imports.scrapers import viernulvier

from tests.scrapers.conftest import _fake_trans_model


class TestSyncAllTranslations:
    def test_multiple_configs_same_model_batched_per_language(self) -> None:
        """Two TranslationConfigs for the same model -> ONE update_or_create per language."""
        calls = []
        FT = _fake_trans_model(calls)

        configs = [
            TranslationConfig("title", FT, "parent", "title"),
            TranslationConfig("description", FT, "parent", "description"),
        ]
        _sync_all_translations(
            SimpleNamespace(pk=1),
            {
                "title": {"nl": "Titel", "en": "Title"},
                "description": {"nl": "Beschrijving", "en": "Description"},
            },
            configs,
        )
        assert len(calls) == 2
        langs = {c["language_id"] for c in calls}
        assert langs == {"nl", "en"}
        nl_call = next(c for c in calls if c["language_id"] == "nl")
        assert nl_call["defaults"]["title"] == "Titel"
        assert nl_call["defaults"]["description"] == "Beschrijving"

    def test_empty_language_code_skipped(self) -> None:
        """Empty string language codes are silently skipped."""
        calls = []
        FT = _fake_trans_model(calls)
        cfg = TranslationConfig("title", FT, "parent", "title")
        _sync_all_translations(
            SimpleNamespace(pk=1),
            {"title": {"": "no-lang", "nl": "Hallo"}},
            [cfg],
        )
        assert len(calls) == 1
        assert calls[0]["language_id"] == "nl"

    def test_returns_for_non_dict_payload(self) -> None:
        """Early exit when translation payload is not a dict."""

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
        )
        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": "not-dict"}, [cfg])

    def test_returns_on_empty_config_list(self) -> None:
        """Empty translation_configs list causes immediate return."""
        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "X"}}, [])

    def test_logs_warning_on_missing_field(self, caplog) -> None:
        """Warning is logged when a configured flat_field does not exist on the model."""

        class FakeMeta:
            def get_field(self, _name) -> Never:
                raise FieldDoesNotExist("missing")

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
        )

        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "Hallo"}}, [cfg])
        assert any("Translation field" in r.message for r in caplog.records)

    def test_logs_error_on_update_or_create_failure(self, caplog) -> None:
        """update_or_create exceptions are caught and logged as errors."""

        class FakeMeta:
            def get_field(self, _name):
                return models.CharField(name="title", max_length=255)

        class FakeManager:
            def update_or_create(self, **_kwargs) -> Never:
                raise RuntimeError("write failed")

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()
            objects = FakeManager()

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
        )

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "Hallo"}}, [cfg])
        assert any("Error syncing" in r.message for r in caplog.records)

    def test_skips_none_language_values(self) -> None:
        """Languages with None values are skipped; non-None values are processed."""
        called_with_langs = []

        class FakeMeta:
            def get_field(self, _name):
                return models.CharField(name="title", max_length=255)

        class FakeManager:
            def update_or_create(self, **kwargs):
                called_with_langs.append(kwargs.get("language_id"))
                return (Mock(), True)

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()
            objects = FakeManager()

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
        )

        viernulvier._sync_all_translations(
            SimpleNamespace(pk=1),
            {"title": {"nl": "Hallo", "fr": "Bonjour", "de": None}},
            [cfg],
        )

        assert "nl" in called_with_langs
        assert "fr" in called_with_langs
        assert "de" not in called_with_langs

    def test_applies_value_transform(self) -> None:
        """value_transforms are applied before persisting translated values."""
        calls = []
        FT = _fake_trans_model(calls)
        cfg = TranslationConfig(
            "title",
            FT,
            "parent",
            "title",
            value_transforms={"title": str.upper},
        )
        _sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "hallo"}}, [cfg])
        assert calls[0]["defaults"]["title"] == "HALLO"

    def test_transform_returning_none_omits_field_no_call(self) -> None:
        """If the only field has transform -> None, update_or_create is never called."""

        class FakeMeta:
            def get_field(self, _name):
                return models.CharField(name="title", max_length=255)

        mock_manager = Mock()

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()
            objects = mock_manager

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
            value_transforms={"title": lambda _: None},
        )

        viernulvier._sync_all_translations(SimpleNamespace(pk=1), {"title": {"nl": "hallo"}}, [cfg])

        mock_manager.update_or_create.assert_not_called()

    def test_skips_empty_string_for_non_blank_field(self) -> None:
        """Empty string raw value is skipped when the model field has blank=False."""

        class FakeMeta:
            def get_field(self, _name):
                f = models.CharField(name="title", max_length=255)
                f.blank = False
                return f

        mock_manager = Mock()
        mock_manager.update_or_create.return_value = (Mock(), True)

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()
            objects = mock_manager

        cfg = TranslationConfig(
            api_key="title",
            model=FakeTranslationModel,
            parent_fk="parent",
            flat_field="title",
        )
        viernulvier._sync_all_translations(
            SimpleNamespace(pk=1),
            {"title": {"nl": "", "fr": "Bonjour"}},
            [cfg],
        )

        # update_or_create called once (for "fr"); "nl" skipped because blank=False + empty
        assert mock_manager.update_or_create.call_count == 1
        call_kwargs = mock_manager.update_or_create.call_args[1]
        assert call_kwargs["language_id"] == "fr"

    def test_skips_non_dict_raw_dict_for_individual_config(self) -> None:
        """If one config's api_key maps to a non-dict, that config is skipped per language."""
        calls = []

        class FakeMeta:
            def get_field(self, name):
                return models.CharField(name=name, max_length=255)

        class FakeManager:
            def update_or_create(self, **kwargs):
                calls.append(kwargs)
                return (Mock(), True)

        class FakeTranslationModel:
            __name__ = "FakeTranslationModel"
            _meta = FakeMeta()
            objects = FakeManager()

        configs = [
            TranslationConfig("title", FakeTranslationModel, "parent", "title"),
            TranslationConfig("subtitle", FakeTranslationModel, "parent", "subtitle"),
        ]
        viernulvier._sync_all_translations(
            SimpleNamespace(pk=1),
            {"title": {"nl": "Hallo"}, "subtitle": "plain-string"},
            configs,
        )
        assert len(calls) == 1
        assert "title" in calls[0]["defaults"]
        assert "subtitle" not in calls[0]["defaults"]

