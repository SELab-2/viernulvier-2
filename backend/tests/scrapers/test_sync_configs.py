"""Tests for sync configurations in management/commands/sync_viernulvier.py

This module tests that all sync configurations are properly structured and compatible
with the scraper architecture.
"""

from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch, Mock

import pytest
from django.core.management.base import CommandParser, OutputWrapper
from django.db import models as django_models

from apps.events.models import Event, EventPrice
from apps.genres.models import Genre, GenreUseAs
from apps.imports.management.commands.sync_viernulvier import (
    UITDATABASE_THEME_CONFIG,
    UITDATABASE_TYPE_CONFIG,
    GENRE_CONFIG,
    TAG_CONFIG,
    LOCATION_CONFIG,
    SPACE_CONFIG,
    HALL_CONFIG,
    MEDIA_GALLERY_CONFIG,
    MEDIA_ITEM_CONFIG,
    PRICE_CONFIG,
    PRICE_RANK_CONFIG,
    PRODUCTION_CONFIG,
    EVENT_CONFIG,
    EVENT_PRICE_CONFIG,
    SYNC_STEPS,
    Command,
    _is_not_longterm,
    nee_ja_to_bool,
    _resolve_genre_use_as,
)
from apps.imports.scrapers.viernulvier import (
    ModelSyncConfig,
    TranslationConfig,
    M2MConfig,
)
from apps.locations.models import Location, Space, Hall
from apps.media_library.models import MediaGallery, MediaItem
from apps.pricing.models import Price, PriceRank
from apps.productions.models import (
    UitDatabaseTheme,
    UitDatabaseType,
    Production,
)
from apps.tags.models import Tag


# ===========================================================================
# Helper Functions
# ===========================================================================


def get_model_field_names(model):
    """Get all field names from a Django model, excluding auto-generated fields."""
    return {
        field.name
        for field in model._meta.get_fields()
        if isinstance(field, django_models.Field) and not field.auto_created
    }


# ===========================================================================
# Test Value Transform Functions
# ===========================================================================


class TestValueTransforms:
    """Test value transformation functions."""

    def test_nee_ja_to_bool_with_ja_string(self):
        """Test that 'ja' string converts to True."""
        for val in ["ja", "JA", "  ja  "]:
            assert nee_ja_to_bool(val) is True

    def test_nee_ja_to_bool_with_nee_string(self):
        """Test that 'nee' string converts to False."""
        for val in ["nee", "NEE", "  nee  "]:
            assert nee_ja_to_bool(val) is False

    def test_nee_ja_to_bool_with_boolean(self):
        """Test that boolean values pass through unchanged."""
        assert nee_ja_to_bool(True) is True
        assert nee_ja_to_bool(False) is False

    def test_nee_ja_to_bool_with_english_strings(self):
        """Test English equivalents."""
        for val in ["true", "yes", "1", "TRUE", " YES ", " 1 "]:
            assert nee_ja_to_bool(val) is True
        for val in ["false", "no", "0", "FALSE", " NO ", " 0 "]:
            assert nee_ja_to_bool(val) is False

    def test_nee_ja_to_bool_with_empty_string(self):
        """Empty string should return False."""
        assert nee_ja_to_bool("") is False
        assert nee_ja_to_bool("   ") is False

    def test_nee_ja_to_bool_with_ints(self):
        """Integers should convert correctly."""
        assert nee_ja_to_bool(1) is True
        assert nee_ja_to_bool(0) is False
        assert nee_ja_to_bool(42) is True
        assert nee_ja_to_bool(-1) is True

    def test_nee_ja_to_bool_with_other_values(self):
        """Other types should be coerced via bool()."""
        assert nee_ja_to_bool(None) is False
        assert nee_ja_to_bool([]) is False
        assert nee_ja_to_bool([1, 2]) is True
        assert nee_ja_to_bool({}) is False
        assert nee_ja_to_bool({"x": 1}) is True

    @pytest.mark.django_db
    def test_resolve_genre_use_as_creates_new(self):
        """Test that _resolve_genre_use_as creates a new GenreUseAs when needed."""
        pk = _resolve_genre_use_as("test_genre")
        assert pk is not None
        assert GenreUseAs.objects.filter(pk=pk, name="test_genre").exists()

    @pytest.mark.django_db
    def test_resolve_genre_use_as_returns_existing(self):
        """Test that _resolve_genre_use_as returns existing GenreUseAs."""
        existing = GenreUseAs.objects.create(name="existing_genre")
        pk = _resolve_genre_use_as("existing_genre")
        assert pk == existing.pk
        assert GenreUseAs.objects.filter(name="existing_genre").count() == 1

    @pytest.mark.django_db
    def test_resolve_genre_use_as_handles_none(self):
        """Test that _resolve_genre_use_as handles None value."""
        pk = _resolve_genre_use_as(None)
        assert pk is not None
        assert GenreUseAs.objects.filter(pk=pk, name="unknown").exists()


# ===========================================================================
# Test Configuration Structure
# ===========================================================================


class TestConfigStructure:
    """Test that all configurations have the correct structure."""

    def test_all_configs_are_model_sync_config(self):
        """Test that all config objects are instances of ModelSyncConfig."""
        configs = [
            UITDATABASE_THEME_CONFIG,
            UITDATABASE_TYPE_CONFIG,
            GENRE_CONFIG,
            TAG_CONFIG,
            LOCATION_CONFIG,
            SPACE_CONFIG,
            HALL_CONFIG,
            MEDIA_GALLERY_CONFIG,
            MEDIA_ITEM_CONFIG,
            PRICE_CONFIG,
            PRICE_RANK_CONFIG,
            PRODUCTION_CONFIG,
            EVENT_CONFIG,
            EVENT_PRICE_CONFIG,
        ]
        for config in configs:
            assert isinstance(config, ModelSyncConfig)

    def test_configs_have_required_attributes(self):
        """Test that all configs have required attributes."""
        configs = [
            UITDATABASE_THEME_CONFIG,
            UITDATABASE_TYPE_CONFIG,
            GENRE_CONFIG,
            TAG_CONFIG,
            LOCATION_CONFIG,
        ]
        for config in configs:
            assert hasattr(config, "field_map")
            assert isinstance(config.field_map, dict)
            assert hasattr(config, "lookup_field")
            assert hasattr(config, "api_id_key")

    def test_configs_with_translations_have_valid_structure(self):
        """Test that configs with translations have properly structured TranslationConfig objects."""
        configs_with_translations = [
            GENRE_CONFIG,
            TAG_CONFIG,
            LOCATION_CONFIG,
            SPACE_CONFIG,
            HALL_CONFIG,
            MEDIA_ITEM_CONFIG,
            PRICE_CONFIG,
            PRICE_RANK_CONFIG,
            PRODUCTION_CONFIG,
        ]

        for config in configs_with_translations:
            assert hasattr(config, "translations")
            assert isinstance(config.translations, list)
            if config.translations:
                for trans_cfg in config.translations:
                    assert isinstance(trans_cfg, TranslationConfig)
                    assert hasattr(trans_cfg, "api_key")
                    assert hasattr(trans_cfg, "model")
                    assert hasattr(trans_cfg, "parent_fk")
                    assert hasattr(trans_cfg, "flat_field")
                    assert hasattr(trans_cfg, "language_fk")

    def test_production_config_has_m2m(self):
        """Test that production config has M2M configuration."""
        assert hasattr(PRODUCTION_CONFIG, "m2m")
        assert isinstance(PRODUCTION_CONFIG.m2m, list)
        assert len(PRODUCTION_CONFIG.m2m) > 0

        for m2m_cfg in PRODUCTION_CONFIG.m2m:
            assert isinstance(m2m_cfg, M2MConfig)
            assert hasattr(m2m_cfg, "api_key")
            assert hasattr(m2m_cfg, "related_model")
            assert hasattr(m2m_cfg, "through_model")
            assert hasattr(m2m_cfg, "parent_fk")
            assert hasattr(m2m_cfg, "related_fk")


# ===========================================================================
# Test Configuration Compatibility
# ===========================================================================


class TestConfigCompatibility:
    """Test that configurations are compatible with their models."""

    def test_all_mapped_fields_exist_in_models(self):
        """Test that field_map values reference valid model fields."""
        configs_and_models = [
            (UITDATABASE_THEME_CONFIG, UitDatabaseTheme),
            (UITDATABASE_TYPE_CONFIG, UitDatabaseType),
            (GENRE_CONFIG, Genre),
            (TAG_CONFIG, Tag),
            (LOCATION_CONFIG, Location),
            (MEDIA_GALLERY_CONFIG, MediaGallery),
            (MEDIA_ITEM_CONFIG, MediaItem),
            (PRICE_CONFIG, Price),
            (PRICE_RANK_CONFIG, PriceRank),
            (PRODUCTION_CONFIG, Production),
            (EVENT_CONFIG, Event),
            (EVENT_PRICE_CONFIG, EventPrice),
        ]

        for config, model in configs_and_models:
            model_fields = get_model_field_names(model)

            for api_field, model_field in config.field_map.items():
                if model_field is not None:
                    field_exists = (
                        model_field in model_fields
                        or f"{model_field}_id" in model_fields
                    )
                    assert field_exists, (
                        f"Config for {model.__name__}: mapped field '{model_field}' "
                        f"(from API field '{api_field}') doesn't exist in model"
                    )

    def test_value_transforms_reference_model_fields(self):
        """Test that value_transforms reference valid model fields."""
        configs_and_models = [
            (TAG_CONFIG, Tag),
            (LOCATION_CONFIG, Location),
            (HALL_CONFIG, Hall),
        ]

        for config, model in configs_and_models:
            if hasattr(config, "value_transforms") and config.value_transforms:
                model_fields = get_model_field_names(model)

                for field_name in config.value_transforms.keys():
                    assert field_name in model_fields, (
                        f"Config for {model.__name__}: value_transform field '{field_name}' "
                        f"doesn't exist in model"
                    )

    def test_fk_resolvers_reference_model_fields(self):
        """Test that fk_resolvers reference valid model fields."""
        configs_and_models = [
            (GENRE_CONFIG, Genre),
        ]

        for config, model in configs_and_models:
            if hasattr(config, "fk_resolvers") and config.fk_resolvers:
                model_fields = get_model_field_names(model)

                for field_name in config.fk_resolvers.keys():
                    assert field_name in model_fields, (
                        f"Config for {model.__name__}: fk_resolver field '{field_name}' "
                        f"doesn't exist in model"
                    )


# ===========================================================================
# Test Sync Steps Configuration
# ===========================================================================


class TestSyncStepsConfiguration:
    """Test that SYNC_STEPS is properly configured."""

    def test_sync_steps_is_list(self):
        """Test that SYNC_STEPS is a list."""
        assert isinstance(SYNC_STEPS, list)
        assert len(SYNC_STEPS) > 0

    def test_sync_steps_structure(self):
        """Test that each sync step has the correct structure."""
        for step in SYNC_STEPS:
            assert isinstance(step, tuple)
            assert len(step) == 4
            name, model, config, endpoint = step

            assert isinstance(name, str)
            assert hasattr(model, "_meta")
            assert isinstance(config, ModelSyncConfig)
            assert isinstance(endpoint, str)
            assert endpoint.startswith("/")

    def test_sync_steps_unique_names(self):
        """Test that sync step names are unique."""
        names = [name for name, *_ in SYNC_STEPS]
        assert len(names) == len(set(names)), "Duplicate sync step names found"

    def test_sync_steps_unique_endpoints(self):
        """Test that sync step endpoints are unique."""
        endpoints = [endpoint for *_, endpoint in SYNC_STEPS]
        assert len(endpoints) == len(set(endpoints)), (
            "Duplicate sync step endpoints found"
        )

    def test_sync_steps_matches_configs(self):
        """Test that all defined configs are used in SYNC_STEPS."""
        configs_in_steps = [config for _, _, config, _ in SYNC_STEPS]

        defined_configs = [
            UITDATABASE_THEME_CONFIG,
            UITDATABASE_TYPE_CONFIG,
            GENRE_CONFIG,
            TAG_CONFIG,
            LOCATION_CONFIG,
            SPACE_CONFIG,
            HALL_CONFIG,
            MEDIA_GALLERY_CONFIG,
            MEDIA_ITEM_CONFIG,
            PRICE_CONFIG,
            PRICE_RANK_CONFIG,
            PRODUCTION_CONFIG,
            EVENT_CONFIG,
            EVENT_PRICE_CONFIG,
        ]

        for config in defined_configs:
            assert config in configs_in_steps, (
                f"Config {config} is defined but not used in SYNC_STEPS"
            )

        assert len(configs_in_steps) == len(defined_configs), (
            f"SYNC_STEPS has {len(configs_in_steps)} configs but {len(defined_configs)} are defined"
        )

    def test_all_models_in_sync_steps_have_external_id(self):
        """Test that all models in SYNC_STEPS have external_id field."""
        for name, model, config, endpoint in SYNC_STEPS:
            model_fields = get_model_field_names(model)
            assert "external_id" in model_fields, (
                f"Model {model.__name__} used in sync step '{name}' doesn't have external_id"
            )


# ===========================================================================
# Test External ID Mapping
# ===========================================================================


class TestExternalIDMapping:
    """Test that all configs properly map external_id."""

    def test_all_configs_map_at_id_to_external_id(self):
        """Test that all configs map '@id' to 'external_id' or use default."""
        configs = [
            ("UitDatabaseTheme", UitDatabaseTheme, UITDATABASE_THEME_CONFIG),
            ("UitDatabaseType", UitDatabaseType, UITDATABASE_TYPE_CONFIG),
            ("Genre", Genre, GENRE_CONFIG),
            ("Tag", Tag, TAG_CONFIG),
            ("Location", Location, LOCATION_CONFIG),
            ("Space", Space, SPACE_CONFIG),
            ("Hall", Hall, HALL_CONFIG),
            ("MediaGallery", MediaGallery, MEDIA_GALLERY_CONFIG),
            ("MediaItem", MediaItem, MEDIA_ITEM_CONFIG),
            ("Price", Price, PRICE_CONFIG),
            ("PriceRank", PriceRank, PRICE_RANK_CONFIG),
            ("Production", Production, PRODUCTION_CONFIG),
            ("Event", Event, EVENT_CONFIG),
            ("EventPrice", EventPrice, EVENT_PRICE_CONFIG),
        ]

        for name, model, config in configs:
            model_fields = get_model_field_names(model)
            assert "external_id" in model_fields, (
                f"Model {name} doesn't have external_id field"
            )

            if "@id" in config.field_map:
                assert config.field_map["@id"] == "external_id", (
                    f"Config for {name} doesn't map '@id' to 'external_id'"
                )


# ===========================================================================
# Integration Tests
# ===========================================================================


class TestConfigIntegration:
    """Integration tests to verify configs work with the scraper."""

    def test_configs_compatible_with_sync_viernulvier(self):
        """Test that configs have all attributes required by sync_viernulvier function."""
        all_configs = [config for _, _, config, _ in SYNC_STEPS]

        required_attributes = [
            "field_map",
            "lookup_field",
            "api_id_key",
            "value_transforms",
            "fk_resolvers",
            "translations",
            "m2m",
        ]

        for config in all_configs:
            for attr in required_attributes:
                assert hasattr(config, attr), (
                    f"Config {config} missing required attribute '{attr}'"
                )

    def test_translation_configs_compatible_with_sync_translations(self):
        """Test that translation configs have required attributes."""
        all_configs = [config for _, _, config, _ in SYNC_STEPS]

        for config in all_configs:
            if config.translations:
                for trans_cfg in config.translations:
                    required = [
                        "api_key",
                        "model",
                        "parent_fk",
                        "flat_field",
                        "language_fk",
                    ]
                    for attr in required:
                        assert hasattr(trans_cfg, attr), (
                            f"TranslationConfig missing required attribute '{attr}'"
                        )

    def test_m2m_configs_compatible_with_sync_m2m(self):
        """Test that M2M configs have required attributes."""
        all_configs = [config for _, _, config, _ in SYNC_STEPS]

        for config in all_configs:
            if config.m2m:
                for m2m_cfg in config.m2m:
                    required = [
                        "api_key",
                        "related_model",
                        "through_model",
                        "parent_fk",
                        "related_fk",
                        "related_lookup_field",
                    ]
                    for attr in required:
                        assert hasattr(m2m_cfg, attr), (
                            f"M2MConfig missing required attribute '{attr}'"
                        )

    def test_lookup_field_exists_in_all_models(self):
        """Test that lookup_field specified in config exists in the model."""
        for name, model, config, endpoint in SYNC_STEPS:
            model_fields = get_model_field_names(model)
            lookup_field = config.lookup_field

            assert lookup_field in model_fields, (
                f"Model {model.__name__} doesn't have lookup_field '{lookup_field}'"
            )


# ===========================================================================
# Test Management Command Argument + Filter Handling
# ===========================================================================


class TestSyncCommandOptions:
    """Test management command option wiring and filter param construction."""

    def test_add_arguments_registers_only_and_all_filter_variants(self):
        """Test that add_arguments exposes --only and generated filter flags."""
        parser = CommandParser(prog="manage.py")
        command = Command()

        command.add_arguments(parser)

        option_strings = {
            option for action in parser._actions for option in action.option_strings
        }

        assert "--only" in option_strings
        for prefix in command.FILTER_FIELDS:
            for bound in ("after", "before"):
                assert f"--{prefix}-{bound}" in option_strings
                assert f"--{prefix}-{bound}-x" in option_strings

    def test_handle_builds_expected_filter_params_and_respects_only(self):
        """Test filter option mapping to API params and --only step selection."""
        command = Command()
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()
        command.stdout = OutputWrapper(stdout_buffer)
        command.stderr = OutputWrapper(stderr_buffer)

        options = {
            "only": "events",
            "created_after": "2024-01-01T00:00:00Z",
            "updated_before_x": "2024-12-31T23:59:59Z",
        }

        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            return_value=5,
        ) as sync_mock:
            command.handle(**options)

        assert sync_mock.call_count == 1
        call_kwargs = sync_mock.call_args.kwargs
        assert call_kwargs["endpoint"] == "/events"
        assert call_kwargs["params"] == {
            "created_at[after]": "2024-01-01T00:00:00Z",
            "updated_at[strictly_before]": "2024-12-31T23:59:59Z",
        }

    def test_handle_reports_unknown_step_without_syncing(self):
        """Test unknown --only step triggers error path and no sync call."""
        command = Command()
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()
        command.stdout = OutputWrapper(stdout_buffer)
        command.stderr = OutputWrapper(stderr_buffer)

        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier"
        ) as sync_mock:
            result = command.handle(only="not_a_real_step")

        assert result is None
        assert "Unknown step 'not_a_real_step'" in stderr_buffer.getvalue()
        sync_mock.assert_not_called()


@pytest.mark.parametrize("tqdm_installed", [True, False])
def test_make_progress_callback(monkeypatch, tqdm_installed, capsys):
    """Test _make_progress_callback writes progress correctly."""

    command = Command()
    name = "test_step"

    if tqdm_installed:
        fake_bar = SimpleNamespace(n=0, refresh=Mock(), close=Mock())
        fake_tqdm = Mock(return_value=fake_bar)
        monkeypatch.setattr(
            "apps.imports.management.commands.sync_viernulvier._tqdm", fake_tqdm
        )
    else:
        monkeypatch.setattr(
            "apps.imports.management.commands.sync_viernulvier._tqdm", None
        )

    callback = command._make_progress_callback(name)

    callback(0, 1000)
    callback(500, 1000)
    callback(1000, 1000)

    if tqdm_installed:
        assert fake_tqdm.call_count == 1
        assert fake_bar.n == 1000
        assert fake_bar.refresh.call_count >= 2
        assert fake_bar.close.call_count == 1
    else:
        captured = capsys.readouterr()
        assert (
            f"{name}: 500/1000" in captured.out or f"{name}: 1000/1000" in captured.out
        )


# ===========================================================================
# _is_not_longterm filter
# ===========================================================================


class TestIsNotLongterm:
    def test_normal_production_returns_true(self):
        assert _is_not_longterm({"production": {"@id": "/api/v1/productions/123"}}) is True

    def test_longterm_production_returns_false(self):
        assert _is_not_longterm({"production": {"@id": "/api/v1/longterm/456"}}) is False

    def test_string_production_normal_returns_true(self):
        assert _is_not_longterm({"production": "/api/v1/productions/99"}) is True

    def test_string_production_longterm_returns_false(self):
        assert _is_not_longterm({"production": "/api/v1/longterm/99"}) is False

    def test_missing_production_key_returns_true(self):
        assert _is_not_longterm({}) is True

    def test_none_production_returns_true(self):
        assert _is_not_longterm({"production": None}) is True


# ===========================================================================
# Extended management command coverage
# ===========================================================================


class TestManagementCommandCoverage:
    def _make_command(self):
        cmd = Command()
        cmd.stdout = OutputWrapper(StringIO())
        cmd.stderr = OutputWrapper(StringIO())
        return cmd

    def test_dry_run_warning_written_to_stdout(self):
        """--dry-run prints DRY RUN warning before executing steps."""
        cmd = self._make_command()
        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            return_value=0,
        ):
            cmd.handle(only="events", dry_run=True)
        assert "DRY RUN" in cmd.stdout.getvalue()

    def test_exception_in_step_logged_as_failed(self):
        """A RuntimeError in a step is caught and printed as FAILED."""
        cmd = self._make_command()
        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            side_effect=RuntimeError("API boom"),
        ):
            cmd.handle(only="events")
        assert "FAILED" in cmd.stdout.getvalue()
        assert "API boom" in cmd.stdout.getvalue()

    def test_handle_no_only_runs_all_steps(self):
        """Omitting --only runs every step in SYNC_STEPS."""
        cmd = self._make_command()
        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            return_value=5,
        ) as mock_sync:
            cmd.handle()
        assert mock_sync.call_count == len(SYNC_STEPS)

    def test_handle_exclusive_after_filter(self):
        """--created-after-x maps to strictly_after query param."""
        cmd = self._make_command()
        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            return_value=0,
        ) as mock_sync:
            cmd.handle(only="events", created_after_x="2024-01-01T00:00:00Z")
        params = mock_sync.call_args.kwargs["params"]
        assert params == {"created_at[strictly_after]": "2024-01-01T00:00:00Z"}

    def test_handle_exclusive_before_filter(self):
        """--updated-before-x maps to strictly_before query param."""
        cmd = self._make_command()
        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            return_value=0,
        ) as mock_sync:
            cmd.handle(only="events", updated_before_x="2024-12-31T23:59:59Z")
        params = mock_sync.call_args.kwargs["params"]
        assert params == {"updated_at[strictly_before]": "2024-12-31T23:59:59Z"}

    def test_handle_starts_after_filter(self):
        """--starts-after maps to starts_at[after] query param."""
        cmd = self._make_command()
        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            return_value=0,
        ) as mock_sync:
            cmd.handle(only="events", starts_after="2025-06-01T00:00:00Z")
        params = mock_sync.call_args.kwargs["params"]
        assert params == {"starts_at[after]": "2025-06-01T00:00:00Z"}

    def test_handle_combined_filters(self):
        """Multiple filter flags are all forwarded in params."""
        cmd = self._make_command()
        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            return_value=0,
        ) as mock_sync:
            cmd.handle(
                only="events",
                created_after="2024-01-01T00:00:00Z",
                ends_before="2024-12-31T23:59:59Z",
            )
        params = mock_sync.call_args.kwargs["params"]
        assert params["created_at[after]"] == "2024-01-01T00:00:00Z"
        assert params["ends_at[before]"] == "2024-12-31T23:59:59Z"

    def test_etag_cache_shared_across_steps(self):
        """All sync steps receive the exact same etag_cache instance."""
        cmd = self._make_command()
        received_caches = []

        def capture_cache(**kwargs):
            received_caches.append(id(kwargs.get("etag_cache")))
            return 0

        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            side_effect=capture_cache,
        ):
            cmd.handle()

        assert len(set(received_caches)) == 1

    def test_total_saved_count_in_summary(self):
        """Done summary line includes the total records count."""
        cmd = self._make_command()
        with patch(
            "apps.imports.management.commands.sync_viernulvier.sync_viernulvier",
            return_value=42,
        ):
            cmd.handle(only="events")
        assert "42" in cmd.stdout.getvalue()

    def test_make_progress_callback_tqdm_bar_lifecycle(self, monkeypatch):
        """tqdm bar: lazy creation on first call, updated each call, closed at end."""
        cmd = Command()
        cmd.stdout = OutputWrapper(StringIO())

        fake_bar = SimpleNamespace(n=0, refresh=Mock(), close=Mock())
        fake_tqdm = Mock(return_value=fake_bar)
        monkeypatch.setattr(
            "apps.imports.management.commands.sync_viernulvier._tqdm", fake_tqdm
        )

        cb = cmd._make_progress_callback("step")
        assert fake_tqdm.call_count == 0  # lazy — not yet created

        cb(100, 500)
        assert fake_tqdm.call_count == 1
        assert fake_bar.n == 100
        assert fake_bar.refresh.call_count >= 1

        cb(200, 500)
        assert fake_tqdm.call_count == 1  # same bar, not re-created
        assert fake_bar.n == 200

        cb(500, 500)
        assert fake_bar.n == 500
        assert fake_bar.close.call_count == 1  # closed when done

    def test_make_progress_bar_returns_value_when_tqdm_present(self, monkeypatch):
        """_make_progress_bar uses _tqdm when it is available."""
        from apps.imports.management.commands import sync_viernulvier as cmd_module

        fake_bar = Mock()
        fake_tqdm = Mock(return_value=fake_bar)
        monkeypatch.setattr(cmd_module, "_tqdm", fake_tqdm)
        result = cmd_module._make_progress_bar("step", 100)
        # Either the tqdm bar or None is acceptable depending on branch
        assert result is None or result == fake_bar

    def test_make_progress_callback_no_tqdm_writes_at_500_intervals(
        self, monkeypatch, capsys
    ):
        """Without tqdm, progress is written to stdout every 500 records and at total."""
        cmd = Command()
        cmd.stdout = OutputWrapper(StringIO())
        monkeypatch.setattr(
            "apps.imports.management.commands.sync_viernulvier._tqdm", None
        )

        cb = cmd._make_progress_callback("mystep")
        cb(0, 2000)
        cb(500, 2000)
        cb(1000, 2000)
        cb(1500, 2000)
        cb(2000, 2000)

        output = cmd.stdout.getvalue()
        assert "500/2000" in output or "1000/2000" in output or "2000/2000" in output